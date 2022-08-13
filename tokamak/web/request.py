from typing import Dict

import trio

from tokamak.web.response import Response


class Request:
    """The Tokamak request class for sending responses and scheduling
    background tasks.


    """

    def __init__(
        self,
        context: Dict[str, str],
        scope,
        receive,
        path: str,
        background_chan: trio._channel.MemorySendChannel,
        response_chan: trio._channel.MemorySendChannel,
    ):
        self.context = context
        self.scope = scope
        self.receive = receive
        self.path = path
        # self.responder = response_chan
        self.background = background_chan
        self.response_chan = response_chan

    @property
    def app(self) -> "tokamak.web.app.Tokamak":
        return self.scope.get("app")

    async def register_background(self, callable, args=None, kwargs=None) -> None:
        """Method to schedule background tasks in a request handler"""
        async with self.background:
            await self.background.send(callable)

    async def respond_with(self, response: Response) -> None:
        """
        In order to send a response to a client this method must be called.

        This allows the Tokamak framework to properly handle cancellations and time-limits
        around request-handling.
        """
        async with self.response_chan:
            await self.response_chan.send(response)
