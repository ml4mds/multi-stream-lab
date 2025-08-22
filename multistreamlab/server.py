"""All handlers used by the application."""
import json
import tornado
import tornado.websocket as ws
from multistreamlab.base import DataStreams, Algorithm
from multistreamlab.evaluate import _evaluate


class OptionsHandler(tornado.web.RequestHandler):
    """The handler to response datasets and algorithms."""

    def initialize(
        self,
        datasets: dict[str, DataStreams],
        algorithms: dict[str, Algorithm]
    ):
        """Initialize the handler with given options."""
        self.datasets = {
            k: v.__doc__ if v.__doc__ is not None else ""
            for k, v in datasets.items()
        }
        self.algorithms = {
            k: v.__doc__ if v.__doc__ is not None else ""
            for k, v in algorithms.items()
        }

    def get(self):
        """Deal with the get request."""
        self.write({
            "data": {
                "datasets": self.datasets,
                "algorithms": self.algorithms
            },
        })


class ImageWebSocketHandler(ws.WebSocketHandler):
    """The handler to deal with the WebSocket connection."""

    def initialize(
        self,
        datasets: dict[str, DataStreams],
        algorithms: dict[str, Algorithm],
        trainset_size: int,
        batch_size: int,
        window_size: int,
    ):
        """Initialize the handler."""
        self.datasets = datasets
        self.algorithms = algorithms
        self.trainset_size = trainset_size
        self.batch_size = batch_size
        self.window_size = window_size
        self._dataset = None
        self._algorithm = None

    def open(self):
        """Handle when a WebSocket connection is opened."""
        # do nothing, wait for messages from the client

    def on_message(self, message: str):
        """Deal with incoming messagees."""
        # check if the message is valid
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            self.write_message({
                "type": "error",
                "data": "The message cannot be deserialized."
            })
            return
        if not isinstance(data, dict) \
                or "type" not in data \
                or "data" not in data:
            self.write_message({
                "type": "error",
                "data": "The message is invalid."
            })
            return

        # parse the message
        match data["type"]:
            case "data":
                if "dataset" not in data["data"] \
                        or "algorithm" not in data["data"]:
                    self.write_message({
                        "type": "error",
                        "data": "Missing dataset or algorithm."
                    })
                    return
                if data["data"]["dataset"] not in self.datasets \
                        or data["data"]["algorithm"] not in self.algorithms:
                    self.write_message({
                        "type": "error",
                        "data": "Unknown dataset or algorithm."
                    })
                    return
                self._dataset = data["data"]["dataset"]
                self._algorithm = data["data"]["algorithm"]
                labels = self.datasets[self._dataset].labels() \
                    + self.algorithms[self._algorithm].labels()
                self.write_message({
                    "type": "data",
                    "data": labels
                })
            case "action":
                match data["data"]:
                    case "start":
                        # TODO: execute the cpu-bound task in another thread to prevent blocking
                        for images in _evaluate(
                            self._dataset,
                            self._algorithm,
                            self.trainset_size,
                            self.batch_size,
                            self.window_size,
                        ):
                            for label, image in images.items():
                                self.write_message({
                                    "type": "data",
                                    "data": {
                                        "image": {
                                            "label": label,
                                            "content": image
                                        }
                                    }
                                })
                        self.write_message({
                            "type": "action",
                            "data": "completion"
                        })
                    case "stop":
                        # TODO: add a share state between multiple handlers.
                        # the evaluation procedure check the state to determine if stop itself.
                        self.write_message({
                            "type": "error",
                            "data": "Stop action is not supported currently."
                        })
                    case _:
                        self.write_message({
                            "type": "error",
                            "data": "Unknown action."
                        })
            case _:
                self.write_message({
                    "type": "error",
                    "data": "Unknown message type."
                })

    def on_close(self):
        """Handle when a WebSocket connection is closed."""
        # do nothing

    def check_origin(self, origin: str) -> bool:
        """Configure to support for allowing alternate origins."""
        return True


class MultiStreamLabServer:
    """The MultiStreamLab server based on Tornado."""

    def __init__(
        self,
        datasets: dict[str, DataStreams],
        algorithms: dict[str, Algorithm],
        trainset_size: int,
        batch_size: int,
        window_size: int,
    ):
        """Initialize a server."""
        self.server = tornado.web.Application([
            (r"/", tornado.web.StaticFileHandler, {"path": "frontend"}),
            (r"/api/options", OptionsHandler, (datasets, algorithms)),
            (r"/ws", ImageWebSocketHandler, (
                datasets,
                algorithms,
                trainset_size,
                batch_size,
                window_size,
            )),
        ])

    def listen(self, port: int):
        """Start the server."""
        self.server.listen(port)
