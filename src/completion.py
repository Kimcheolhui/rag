import json
import uuid


def generate_completion(openai_client, user_prompt, retrieved_docs, history, deployment_name):
    system_prompt = """
    You are a helpful assistant for answering movie-related queries based on the given context.
    Only answer from the given context. List at least 3 relevant movies if applicable.
    """

    messages = [{'role': 'system', 'content': system_prompt}]

    for entry in history:
        messages.append({'role': 'user', 'content': entry['prompt']})
        messages.append({'role': 'assistant', 'content': entry['completion']})

    messages.append({'role': 'user', 'content': user_prompt})

    for doc in retrieved_docs:
        messages.append({'role': 'system', 'content': json.dumps(doc)})

    response = openai_client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        temperature=0.3
    )
    return response.model_dump()


def cache_response(container, user_prompt, embedding, response):
    doc = {
        'id': str(uuid.uuid4()),
        'prompt': user_prompt,
        'completion': response['choices'][0]['message']['content'],
        'model': response['model'],
        'vector': embedding,
        'totalTokens': response['usage']['total_tokens']
    }
    container.create_item(body=doc)
