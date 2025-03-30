import os
import json
import gradio as gr
import asyncio
import argparse
from dotenv import dotenv_values
from azure.cosmos import CosmosClient
from openai import AzureOpenAI

from src.db_setup import setup_db_and_containers
from src.insert_data import insert_data
from src.embedding import generate_embeddings
from src.search import vector_search, get_cache, get_recent_history
from src.completion import generate_completion, cache_response

parser = argparse.ArgumentParser()
parser.add_argument("--skip-insert", action="store_true", help="데이터 삽입 생략")
args = parser.parse_args()

# Load config
config = dotenv_values("rag_env.env")

# OpenAI Client
# Embedding용 클라이언트
embedding_client = AzureOpenAI(
    azure_endpoint=config["openai_embeddings_endpoint"],
    api_key=config["openai_embeddings_key"],
    api_version=config["openai_api_version"]
)

# Completion용 클라이언트
completion_client = AzureOpenAI(
    azure_endpoint=config["openai_completions_endpoint"],
    api_key=config["openai_completions_key"],
    api_version=config["openai_api_version"]
)


# Cosmos DB Client
cosmos_client = CosmosClient(
    config["cosmos_uri"], credential=config["cosmos_key"])

# Setup DB & containers
_, movies_container, cache_container = setup_db_and_containers(
    cosmos_client,
    config["cosmos_database_name"],
    config["cosmos_collection_name"],
    config["cosmos_cache_collection_name"],
    int(config["openai_embeddings_dimensions"]),
    config["cosmos_vector_property_name"]
)

# Load data (벡터화된 JSON 사용)
if not args.skip_insert:
    with open("data/MovieLens-4489-256D.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 초기 데이터 삽입 (비동기 실행)
    asyncio.run(insert_data(
        movies_container,
        data,
        embedding_client,
        config["openai_embeddings_deployment"],
        int(config["openai_embeddings_dimensions"]),
        vectorize=False
    ))
else:
    print("데이터 삽입 생략 (--skip-insert)")


def handle_chat(user_input, chat_history):
    embedding = generate_embeddings(
        embedding_client,
        user_input,
        config["openai_embeddings_deployment"],
        int(config["openai_embeddings_dimensions"])
    )

    cached = get_cache(cache_container, embedding)
    if cached:
        print("캐시 응답 반환")
        return "", chat_history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": cached[0]['completion']}
        ]

    retrieved = vector_search(movies_container, embedding)
    history = get_recent_history(cache_container)

    response = generate_completion(
        completion_client,
        user_input,
        retrieved,
        history,
        config["openai_completions_deployment"]
    )

    cache_response(cache_container, user_input, embedding, response)
    answer = response["choices"][0]["message"]["content"]

    return "", chat_history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": answer}
    ]


# Gradio UI
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label="Chat", type="messages")
    msg = gr.Textbox(label="Ask a movie question")
    clear = gr.Button("Clear")

    msg.submit(handle_chat, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot)

demo.queue()
demo.launch()
