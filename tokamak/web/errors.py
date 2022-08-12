from tokamak.web import response


UnknownResourceResponse = response.Response(body=b"Unknown Resource", status_code=404)
MethodNotAllowedResponse = response.Response(
    body=b"Method not allowed", status_code=405
)
RequestCancelledResponse = response.Response(
    body=b"Request time limit exceeded", status_code=408
)
RateLimitedResponse = response.Response(body=b"Rate limit exceeded", status_code=429)


async def default_cancelled_request_handler(request):
    await request.respond_with(RequestCancelledResponse)


async def unknown_handler(request):
    await request.respond_with(UnknownResourceResponse)


async def method_not_allowed(request):
    await request.respond_with(MethodNotAllowedResponse)
