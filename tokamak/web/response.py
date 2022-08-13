from functools import cached_property
from typing import List, Tuple


class Response:
    """Tokamak Web framework response class"""

    def __init__(
        self,
        status_code: int = 200,
        headers: dict = None,
        body: bytes = b"",
        content_type: str = "text/plain",
        charset: str = "utf-8",
        streaming: bool = False,
    ) -> None:
        self.status_code = status_code
        self.streaming_body = False
        self.body = body
        self._headers = headers or dict()
        self.content_type = content_type
        self.charset = charset
        self.streaming = streaming

    @cached_property
    def raw_headers(self) -> List[Tuple[bytes, bytes]]:
        """Headers are constructed for an ASGI send response"""
        raw_headers = [
            (k.lower().encode("latin-1"), v.encode("latin-1"))
            for k, v in self._headers.items()
        ]
        keys = [h[0] for h in raw_headers]
        populate_content_length = b"content-length" not in keys
        populate_content_type = b"content-type" not in keys

        body = getattr(self, "body", b"")
        if body and populate_content_length:
            content_length = str(len(body))
            raw_headers.append((b"content-length", content_length.encode("latin-1")))

        content_type = self.content_type
        if content_type is not None and populate_content_type:
            if content_type.startswith("text/"):
                content_type += "; charset=" + self.charset
            raw_headers.append((b"content-type", content_type.encode("latin-1")))

        return raw_headers

    async def __call__(self, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )
        if self.streaming:
            async for chunk in self.streaming_body:
                await send(
                    {"type": "http.response.body", "body": chunk, "more_body": True}
                )
            await send({"type": "http.response.body", "body": b"", "more_body": False})
        else:
            await send({"type": "http.response.body", "body": self.body})
