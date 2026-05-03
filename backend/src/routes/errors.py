from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail model."""

    loc: Optional[List[Union[str, int]]] = None
    msg: str
    type: str


class HTTPError(BaseModel):
    """Base HTTP error model."""

    detail: Union[str, List[ErrorDetail]] = Field(
        ...,
        description="Error message or list of validation errors",
    )
    request_id: Optional[str] = Field(
        None,
        description="Unique request ID for tracking",
    )


class ErrorResponse400(HTTPError):
    """400 Error response."""
    pass


class ErrorResponse404(HTTPError):
    """404 Error response."""
    pass


class ErrorResponse422(HTTPError):
    """422 Error response."""
    pass


class ErrorResponse500(HTTPError):
    """500 Error response."""
    pass
