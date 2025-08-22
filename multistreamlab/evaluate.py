"""The evaluation procedure."""
from collections import deque
from io import BytesIO
from base64 import b64encode
from typing import TypeVar, Generic, Iterator
from matplotlib.figure import Figure
from multistreamlab.base import DataStreams, Algorithm

X, Y = TypeVar("features"), TypeVar("label")


class DataStreamsLoader(Generic[X, Y]):
    """
    The data streams loader.

    This class is inspired by the `DataLoader` class in PyTorch,
    but it's much simpler compared to its predecessor.
    Features like shuffle or sampling are not necessary
    because the seqence order is important to keep in the data stream scenario.
    """

    def __init__(
        self,
        datastreams: DataStreams[X, Y],
        trainset_size: int,
        batch_size: int,
    ):
        """Initialize a data streams loader."""
        if trainset_size <= 0:
            raise ValueError("The trainset size must be larger than 0.")
        if batch_size <= 0:
            raise ValueError("The batch size must be larger than 0.")
        if trainset_size > len(datastreams):
            raise ValueError("The trainset size must not be larger than the length of the datastreams.")
        self.datastreams = datastreams
        self.trainset_size = trainset_size
        self.batch_size = batch_size

    def train(self) -> list[tuple[X, Y]]:
        """Retrieve the train dataset."""
        return self.datastreams[:self.trainset_size]

    def streams(self) -> Iterator[list[tuple[X, Y]]]:
        """Retrieve the testing dataset."""
        start = self.trainset_size
        while start < len(self.datastreams):
            stop = min(start + self.batch_size, len(self))
            yield self.datastreams[start:stop]


def _evaluate(
    dataset: DataStreams,
    algorithm: Algorithm,
    trainset_size: int,
    batch_size: int,
    window_size: int,
) -> Iterator[dict[str, str]]:
    """Evaluate the given algorithm on the given dataset."""
    data_loader = DataStreamsLoader(dataset, trainset_size, batch_size)
    x, y = data_loader.train()
    algorithm.fit(x, y)
    window = deque()
    for i, (x, y) in enumerate(data_loader.streams()):
        # evaluate and adapt
        acc, is_drift = algorithm.detect(x, y)
        window.append((acc, is_drift))
        if len(window) > window_size:
            window.popleft()
        algorithm.partial_fit(x, y, is_drift)

        # plot
        # TODO: add customized plot from algorithm
        buffers = {label: BytesIO() for label in dataset.labels()}
        fig = Figure()
        for j, label in enumerate(dataset.labels()):
            fig.clear()
            ax = fig.subplots()
            ax.set_title(f"Performance of {label}")
            ax.set_xlabel("time")
            xmin, xmax = max(0, i - window_size + 1), max(window_size - 1, i)
            ax.set_xlim(xmin, xmax)
            ax.plot(
                range(xmin, i + 1),
                [acc[j] for acc, _ in window],
                label=label
            )
            ymin, ymax = ax.get_ylim()
            for _, drifts in window:
                if drifts is not None:
                    for drift in drifts:
                        ax.vlines(drift, ymin, ymax, color="red")
            fig.savefig(buffers[label], format="png")
        yield {
            label: b64encode(buffer.getbuffer()).decode("ascii")
            for label, buffer in buffers.items()
        }
