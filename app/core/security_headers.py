"""Security response headers for the (JSON) API.

This API never renders HTML or runs scripts of its own, so it does not set a
Content-Security-Policy (that would also have to allow the CDN scripts the
auto-generated /docs and /redoc pages load). The frontend, which does render HTML,
sets its own strict CSP (see render.yaml, service "careerops-web"). What is set here
still matters for the API's own responses and for the auto-generated docs pages:
- stops a browser from "sniffing" a JSON response as something else (nosniff)
- stops the API (or its /docs page) from being framed by another site (DENY)
- avoids leaking the full request URL (which can carry an id) to a linked site
  (Referrer-Policy)
- denies the browser features this API has no use for (Permissions-Policy)
- tells browsers to only ever use HTTPS for this host, once it has been served over
  HTTPS at least once (HSTS; see the scheme check below for why it is conditional)
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for name, value in _HEADERS.items():
            response.headers.setdefault(name, value)
        # request.url.scheme reflects X-Forwarded-Proto once uvicorn is started with
        # --proxy-headers and a trusted proxy (see scripts/start.sh), so this is only
        # sent for requests that actually reached Render over HTTPS - never for plain
        # HTTP in local development, where it would be actively wrong.
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        return response
