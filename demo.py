"""A demo script."""
import time
import random
import asyncio
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn import linear_model
from multistreamlab.base import DataStreams, Algorithm
from multistreamlab.server import MultiStreamLabServer


class DemoDataStreams(DataStreams):
    """A demo datastreams class."""

    def __init__(self):
        """Initialize an object."""
        self.m = 6
        self.n = 20844
        self.d = 3
        df = pd.read_csv("demo.csv")
        self.data = np.zeros((6, 20844, 4))
        for i in range(6):
            i1 = 4 * i
            i2 = i1 + 4
            self.data[i, :, :] = df.iloc[:, i1:i2].to_numpy()
        del df

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


# rank sum test
def rank_sum_test(memb1, memb2, alpha=0.005):
    """Rank sum test."""
    _, p = mannwhitneyu(memb1, memb2)
    return memb1.mean() - 0.1 * memb1.std() < memb2.mean()


# membership functions
class SMF:
    """sigmoid membership function."""

    def __init__(self):
        """__init__ method."""
        self.func = linear_model.LogisticRegression()

    def membership(self, x):
        """Return the membership of a ndarray."""
        x = x.reshape((-1, 1))
        return self.func.predict_proba(x).max(axis=1)

    def fit(self, x1, x2, epochs=5):
        """Estimate the parameters of membership.

        x1, x2: ndarray of size (n, d)
        """
        n1 = x1.shape[0]
        n2 = x2.shape[0]
        X = np.hstack((x1, x2))
        Y = np.ones(n1 + n2)
        Y[n1:] = 0
        shuff = np.random.permutation(n1+n2)
        X = X[shuff]
        Y = Y[shuff]
        self.func.fit(X.reshape((-1, 1)), Y)


# stream handler, each stream has a learner and a membership fucntion
class StreamHandler:
    """Handle a stream in dynamic environment."""

    def __init__(self, base_learner, random_state=None):
        """__init__ for StreamHandler."""
        self.learner = base_learner
        self.mf = SMF()
        self.hist_memb = None

    def fit(self, x, y, x1, y1, epochs=100, sample_weight=None):
        """Fit method."""
        self.learner.fit(x, y, sample_weight=sample_weight)
        yhat = self.learner.predict(x)
        loss = (yhat - y) ** 2
        yhat1 = self.learner.predict(x1)
        loss1 = (yhat1 - y1) ** 2
        self.mf.fit(loss, loss1, epochs=epochs)
        self.hist_memb = self.mf.membership(loss)

    def partial_fit(self, x, y, x1, y1, epochs=100, sample_weight=None):
        """Partial fit method."""
        self.learner.partial_fit(x, y, sample_weight=sample_weight)
        yhat = self.learner.predict(x)
        loss = (yhat - y) ** 2
        yhat1 = self.learner.predict(x1)
        loss1 = (yhat1 - y1) ** 2
        self.mf.fit(loss, loss1, epochs=epochs)
        self.hist_memb = self.mf.membership(loss)

    def score(self, x, y, return_memb=False):
        """Score method.

        x: ndarray of size (n, d)
        y: ndarray of size (n,)
        """
        yhat = self.learner.predict(x)
        loss = (yhat - y) ** 2
        memb = self.mf.membership(loss)
        if return_memb:
            return memb
        drift = rank_sum_test(self.hist_memb, memb)
        return loss.mean(), drift


class DemoAlgorithm(Algorithm):
    """A demo algorithm class."""

    def __init__(self):
        """Initialize an object."""
        self.m = None
        self.hdlrs = []

    def fit(self, data):
        """Train from scratch."""
        self.m = len(data)
        for i, (x, y) in enumerate(data):
            self.hdlrs.append(StreamHandler(linear_model.Ridge(alpha=1)))
            i_other = random.choice([j for j in range(self.m) if j != i])
            x_other, y_other = data[i_other]
            self.hdlrs[-1].fit(x, y, x_other, y_other)
        return

    def partial_fit(self, data, is_drift):
        """Adapt to the concept drift."""
        drift_streams = [i for i, drift in enumerate(is_drift) if drift]
        for j in drift_streams:
            # retrainset = [i for i, drift in enumerate(is_drift) if not drift] + [j]
            j_other = random.choice([j_other for j_other in range(self.m) if j_other != j])
            x, y = data[j]
            x_other, y_other = data[j_other]
            self.hdlrs[j].fit(x, y, x_other, y_other)
        return

    def score(self, data):
        """Evaluate the prediction results, and detect if concept drift occurs."""
        accs, is_drift = [], []
        for i in range(self.m):
            x, y = data[i]
            acc, drift = self.hdlrs[i].score(x, y)
            accs.append(acc)
            is_drift.append(drift)
        return np.array(accs), is_drift


async def main():
    """Start the server."""
    ds = DemoDataStreams()
    algo = DemoAlgorithm()
    server = MultiStreamLabServer(
        {"DemoDataset": ds},
        {"DemoAlgorithm": algo},
        1000,
        100,
        30,
    )
    server.listen(8888)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
