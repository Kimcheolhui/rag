import os
import json
import asyncio
import argparse
import streamlit as st
from dotenv import dotenv_values
from azure.cosmos import CosmosClient
from openai import AzureOpenAI

from src.db_setup import setup_db_and_containers
from src.insert_data import insert_data
from src.embedding import generate_embeddings
from src.search import vector_search, get_cache, get_recent_history
from src.completion import generate_completion, cache_response

# CLI args
parser = argparse.ArgumentParser()
parser.add_argument("--skip-insert", action="store_true", help="데이터 삽입 생략")
args, _ = parser.parse_known_args()

# Load config
config = dotenv_values("rag_env.env")

# OpenAI Clients
embedding_client = AzureOpenAI(
    azure_endpoint=config["openai_embeddings_endpoint"],
    api_key=config["openai_embeddings_key"],
    api_version=config["openai_api_version"]
)

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

# Insert data (optional)
if not args.skip_insert:
    with open("data/MovieLens-4489-256D.json", "r", encoding="utf-8") as f:
        data = json.load(f)

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

# Streamlit UI
st.set_page_config(page_title="RAG Movie Chatbot")
st.title("🎬 영화 챗봇")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("영화에 대해 질문해보세요:", key="input")

if st.button("전송") and user_input:
    embedding = generate_embeddings(
        embedding_client,
        user_input,
        config["openai_embeddings_deployment"],
        int(config["openai_embeddings_dimensions"])
    )

    cached = get_cache(cache_container, embedding)
    if cached:
        answer = cached[0]['completion']
    else:
        retrieved = vector_search(movies_container, embedding)
        history = get_recent_history(cache_container)

        response = generate_completion(
            completion_client,
            user_input,
            retrieved,
            history,
            config["openai_completions_deployment"]
        )
        answer = response["choices"][0]["message"]["content"]
        cache_response(cache_container, user_input, embedding, response)

    st.session_state.chat_history.append(
        {"role": "user", "content": user_input})
    st.session_state.chat_history.append(
        {"role": "assistant", "content": answer})

# Display chat history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**🙋‍♂️ 나:** {msg['content']}")
    else:
        st.markdown(f"**🤖 챗봇:** {msg['content']}")
