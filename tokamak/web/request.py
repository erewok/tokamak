import logging
from collections.abc import Callable

from tokamak.web.response import Response

logger = logging.getLogger("tokamak")

try:
    import trio
except ImportError:
    logger.error(

            "To use Tokamak's web properties, "
            "the library must be installed with option [web]"

    )
    raise


class Request:
    """The Tokamak request class for sending responses and scheduling
    background tasks.

    Args:

        context (Dict[str, str]): Context from the matching path
        scope (dict): Request scope dictionary
        receive (Channel): Channel for receiving the request body
        path (str): Path matched for this request
        background_chan: Send channel for scheduling background tasks
        response_chan: Send channel for submitting a response
    """

    def __init__(
        self,
        context: dict[str, str],
        scope: dict[str, str],
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
    def app(self):
        """
        Returns:
            Tokamak application instance
        """
        return self.scope.get("app")

    async def register_background(self, callable: Callable) -> None:
        """
        Method to schedule background tasks in a request handler

        Args:

            callable: Arbitrary async function
        """
        async with self.background:
            await self.background.send(callable)

    async def respond_with(self, response: Response) -> None:
        """
        In order to send a response to a client this method must be called.

        This allows the Tokamak framework to properly handle cancellations and time-limits
        around request-handling.

        Args:

            response: Response class to send to client.
        """
        async with self.response_chan:
            await self.response_chan.send(response)
