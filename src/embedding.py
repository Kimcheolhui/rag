from tenacity import retry, wait_random_exponential, stop_after_attempt
import logging


@retry(wait=wait_random_exponential(min=2, max=300), stop=stop_after_attempt(20))
def generate_embeddings(openai_client, text: str, deployment_name: str, dimensions: int):
    try:
        response = openai_client.embeddings.create(
            input=text,
            model=deployment_name,
            dimensions=dimensions
        )
        return response.model_dump()['data'][0]['embedding']
    except Exception as e:
        logging.error("Embedding 생성 중 오류 발생", exc_info=True)
        raise
