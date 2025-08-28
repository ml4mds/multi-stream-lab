"""A demo script."""
import time
import asyncio
import numpy as np
from multistreamlab.base import DataStreams, Algorithm
from multistreamlab.server import MultiStreamLabServer


class DemoDataStreams(DataStreams):
    """A demo datastreams class."""

    def __init__(self):
        """Initialize an object."""
        self.m = 10
        self.n = 100
        self.d = 4
        self.data = np.random.normal(0, 1, (self.m, self.n, self.d))

    def __len__(self) -> int:
        """Get the length."""
        return self.n

    def __getitem__(self, index: int | slice):
        """Get a list of batches of data in a feature-label pair."""
        return [
            (self.data[i, index, :-1], self.data[i, index, -1])
            for i in range(self.m)
        ]

    def labels(self) -> list[str]:
        """Get the labels of data streams."""
        return [f"Stream #{i+1}" for i in range(self.m)]


class DemoAlgorithm(Algorithm):
    """A demo algorithm class."""

    def __init__(self):
        """Initialize an object."""
        self.m = None

    def fit(self, data):
        """Train from scratch."""
        self.m = len(data)
        time.sleep(1)
        return

    def partial_fit(self, data, is_drift):
        """Adapt to the concept drift."""
        time.sleep(1)
        return

    def score(self, data):
        """Evaluate the prediction results, and detect if concept drift occurs."""
        acc = np.random.uniform(0, 1, self.m).tolist()
        is_drift = [a < 0.1 for a in acc]
        return acc, is_drift


async def main():
    """Start the server."""
    ds = DemoDataStreams()
    algo = DemoAlgorithm()
    server = MultiStreamLabServer(
        {"DemoDataset": ds},
        {"DemoAlgorithm": algo},
        10,
        10,
        30,
    )
    server.listen(8888)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
