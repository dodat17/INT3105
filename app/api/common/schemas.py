from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """JSON uses camelCase; Python code uses snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RequestModel(CamelModel):
    # Reject fields outside the contract so clients cannot set role, id, ...
    model_config = ConfigDict(extra="forbid")


class PageResponse[T](CamelModel):
    items: list[T]
    page: int
    page_size: int
    total_items: int
