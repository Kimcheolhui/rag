def vector_search(container, embedding, similarity_score=0.02, num_results=5, vector_field='vector'):
    query = f"""
    SELECT TOP @num_results c.overview,
           VectorDistance(c.{vector_field}, @embedding) AS SimilarityScore
    FROM c
    WHERE VectorDistance(c.{vector_field}, @embedding) > @similarity_score
    ORDER BY VectorDistance(c.{vector_field}, @embedding)
    """
    results = container.query_items(
        query=query,
        parameters=[
            {"name": "@embedding", "value": embedding},
            {"name": "@num_results", "value": num_results},
            {"name": "@similarity_score", "value": similarity_score}
        ],
        enable_cross_partition_query=True
    )
    return list(results)


def get_cache(container, embedding, similarity_score=0.99, num_results=1, vector_field='vector'):
    query = f"""
    SELECT TOP @num_results *
    FROM c
    WHERE VectorDistance(c.{vector_field}, @embedding) > @similarity_score
    ORDER BY VectorDistance(c.{vector_field}, @embedding)
    """
    results = container.query_items(
        query=query,
        parameters=[
            {"name": "@embedding", "value": embedding},
            {"name": "@num_results", "value": num_results},
            {"name": "@similarity_score", "value": similarity_score}
        ],
        enable_cross_partition_query=True
    )
    return list(results)


def get_recent_history(container, limit=3):
    query = """
    SELECT TOP @limit *
    FROM c
    ORDER BY c._ts DESC
    """
    results = container.query_items(
        query=query,
        parameters=[{"name": "@limit", "value": limit}],
        enable_cross_partition_query=True
    )
    return list(results)
