from __future__ import annotations

import hashlib
import hmac
import importlib
import os

from fastapi import FastAPI, Request

_slowapi = importlib.import_module("slowapi")
_slowapi_errors = importlib.import_module("slowapi.errors")
_slowapi_middleware = importlib.import_module("slowapi.middleware")
_slowapi_util = importlib.import_module("slowapi.util")

Limiter = _slowapi.Limiter
RateLimitExceeded = _slowapi_errors.RateLimitExceeded
SlowAPIASGIMiddleware = _slowapi_middleware.SlowAPIASGIMiddleware
get_remote_address = _slowapi_util.get_remote_address
_rate_limit_exceeded_handler = _slowapi._rate_limit_exceeded_handler

_HMAC_KEY = os.urandom(32)


def get_rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            digest = hmac.new(_HMAC_KEY, token.encode(), hashlib.sha256).hexdigest()
            return f"user:{digest}"

    return get_remote_address(request)


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["60/minute"],
    application_limits=["1000/minute"],
    headers_enabled=True,
)


def rate_limit_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, RateLimitExceeded):
        return _rate_limit_exceeded_handler(request, exc)
    raise exc


def setup_rate_limiting(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
    app.add_middleware(SlowAPIASGIMiddleware)
