from azure.cosmos import CosmosClient, PartitionKey, exceptions


def setup_db_and_containers(
    cosmos_client: CosmosClient,
    cosmos_database: str,
    cosmos_collection: str,
    cosmos_cache_collection: str,
    openai_embeddings_dimensions: int,
    cosmos_vector_property: str
):
    # 데이터베이스 생성 또는 가져오기
    db = cosmos_client.create_database_if_not_exists(id=cosmos_database)

    # 벡터 embedding 정책
    vector_embedding_policy = {
        "vectorEmbeddings": [
            {
                "path": "/" + cosmos_vector_property,
                "dataType": "float32",
                "distanceFunction": "cosine",
                "dimensions": openai_embeddings_dimensions
            },
        ]
    }

    # 벡터 인덱스 정책
    indexing_policy = {
        "includedPaths": [
            {"path": "/*"}
        ],
        "excludedPaths": [
            {"path": "/\"_etag\"/?"},
            {"path": "/" + cosmos_vector_property + "/*"}
        ],
        "vectorIndexes": [
            {
                "path": "/" + cosmos_vector_property,
                "type": "quantizedFlat"
            }
        ]
    }

    # 벡터 저장 컨테이너 생성
    try:
        movies_container = db.create_container_if_not_exists(
            id=cosmos_collection,
            partition_key=PartitionKey(path="/id"),
            indexing_policy=indexing_policy,
            vector_embedding_policy=vector_embedding_policy,
            offer_throughput=500
        )
        print(
            f"✅ Container '{movies_container.id}' created or already exists.")
    except exceptions.CosmosHttpResponseError as e:
        print("❌ Error creating movies container:", e)
        raise e

    # 캐시 컨테이너 생성
    try:
        cache_container = db.create_container_if_not_exists(
            id=cosmos_cache_collection,
            partition_key=PartitionKey(path="/id"),
            indexing_policy=indexing_policy,
            vector_embedding_policy=vector_embedding_policy,
            offer_throughput=400
        )
        print(f"✅ Container '{cache_container.id}' created or already exists.")
    except exceptions.CosmosHttpResponseError as e:
        print("❌ Error creating cache container:", e)
        raise e

    return db, movies_container, cache_container
