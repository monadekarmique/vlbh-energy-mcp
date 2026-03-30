from __future__ import annotations
import os
from fastapi import Header, HTTPException, status, Request


def verify_token(x_vlbh_token: str = Header(..., alias="X-VLBH-Token")) -> None:
    """Validate Bearer token against VLBH_TOKEN env variable."""
    expected = os.environ.get("VLBH_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="VLBH_TOKEN not configured",
        )
    if x_vlbh_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-VLBH-Token",
        )


def get_make_service(request: Request):
    """Retrieve MakeService instance from app state."""
    return request.app.state.make_service
