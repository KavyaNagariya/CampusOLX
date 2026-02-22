from fastapi import Query


def pagination_params(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    skip = (page - 1) * size
    limit = size
    return skip, limit
