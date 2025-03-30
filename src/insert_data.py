import asyncio
import time
import logging
from azure.cosmos.exceptions import CosmosHttpResponseError
from src.embedding import generate_embeddings


async def generate_vectors(data: list, openai_client, deployment_name, dimensions, vector_key='vector', text_key='overview'):
    loop = asyncio.get_event_loop()

    async def process_item(item):
        try:
            vector = await loop.run_in_executor(None, generate_embeddings, openai_client, item[text_key], deployment_name, dimensions)
            item[vector_key] = vector
        except Exception as e:
            logging.error(f"벡터 생성 실패: {item[text_key][:50]}", exc_info=True)

    tasks = [process_item(item) for item in data]
    await asyncio.gather(*tasks)
    return data


def upsert_with_retry(container, item, max_retries=5):
    for attempt in range(max_retries):
        try:
            return container.upsert_item(item)
        except CosmosHttpResponseError as e:
            if e.status_code == 429:
                retry_after = int(e.response.headers.get(
                    "x-ms-retry-after-ms", 500)) / 1000
                print(
                    f"429 TooManyRequests, {retry_after:.2f}초 후 재시도 중... (시도 {attempt + 1})")
                time.sleep(retry_after)
            else:
                raise e


async def insert_data(container, data: list, openai_client, deployment_name, dimensions, vectorize=True, vector_key='vector'):
    start = time.time()

    if vectorize:
        print("⚙ 벡터화 진행 중...")
        data = await generate_vectors(data, openai_client, deployment_name, dimensions, vector_key)

    semaphore = asyncio.Semaphore(3)
    loop = asyncio.get_event_loop()
    counter = 0

    async def upsert_item(item):
        nonlocal counter
        async with semaphore:
            await loop.run_in_executor(None, upsert_with_retry, container, item)
            counter += 1
            if counter % 100 == 0:
                print(f"{counter}개 삽입됨")
            await asyncio.sleep(0.2)

    await asyncio.gather(*(upsert_item(d) for d in data))

    print(f"✔ 총 {counter}개 삽입 완료, 소요시간: {round(time.time() - start, 2)}초")
