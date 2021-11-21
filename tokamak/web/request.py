from tokamak.web.response import Response


class Request:
    def __init__(self, context, scope, receive, response_chan, background_chan):
        self.scope = scope
        self.receive = receive
        self.context = context
        self.responder = response_chan
        self.background = background_chan

    async def respond_with(self, response: Response):
        async with self.responder:
            await self.responder.send(response)

    async def register_background(self, callable, args=None, kwargs=None):
        async with self.background:
            await self.background.send(callable)
