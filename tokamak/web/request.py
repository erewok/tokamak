from tokamak.web.response import Response


class Request:
    def __init__(self, context, scope, receive, path, response_chan, background_chan):
        self.context = context
        self.scope = scope
        self.receive = receive
        self.path = path
        self.responder = response_chan
        self.background = background_chan

    @property
    def app(self):
        return self.scope.get("app")

    async def respond_with(self, response: Response):
        async with self.responder:
            await self.responder.send(response)

    async def register_background(self, callable, args=None, kwargs=None):
        await self.background.send(callable)
