"""Security response headers for direct backend access.

In production the real perimeter is Nginx (see nginx/prod/*.conf), which
sets the canonical CSP/HSTS/etc. for both the static frontend and the
proxied API, stripping whatever the backend sends first so there is never a
duplicate or conflicting header (proxy_hide_header + add_header). This
middleware is the defense-in-depth layer for whenever the backend is
reached directly — local development without Nginx, or if Nginx is ever
bypassed — so the API is never unprotected on its own.

/docs, /redoc, and /openapi.json are exempted: FastAPI's bundled Swagger/
Redoc UI loads scripts from a third-party CDN, which a strict CSP would
break. Those routes are disabled entirely in production (see app/main.py),
so the exemption only matters in development.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if request.url.path.startswith(_DOCS_PATHS):
            return response

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # API responses are JSON, never HTML: default-src 'none' is safe and
        # simplest — there is nothing here for a browser to execute/render.
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response
