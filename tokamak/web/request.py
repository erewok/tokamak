from tokamak.web.response import Response


class Request:
    def __init__(self, context, scope, receive, path, background_chan, response_chan):
        self.context = context
        self.scope = scope
        self.receive = receive
        self.path = path
        # self.responder = response_chan
        self.background = background_chan
        self.response_chan = response_chan

    @property
    def app(self):
        return self.scope.get("app")

    async def register_background(self, callable, args=None, kwargs=None):
        async with self.background:
            await self.background.send(callable)

    async def respond_with(self, response: Response):
        async with self.response_chan:
            await self.response_chan.send(response)
