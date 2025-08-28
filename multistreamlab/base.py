"""The base classes for data streams and algorithms."""
from typing import TypeVar, Generic

X, Y = TypeVar("features"), TypeVar("label")


class DataStreams(Generic[X, Y]):
    """
    The base class for data streams.

    This base class is inspired by the design of `Dataset` class in PyTorch.
    Any customized subclass should override the following methods:
    - `__len__`
    - `__getitem__`
    - `labels`
    """

    def __len__(self) -> int:
        """Get the length."""
        raise NotImplementedError("The `__len__` method must be overrided.")

    def __getitem__(self, index: int | slice) -> list[tuple[X, Y]]:
        """Get a list of batches of data in a feature-label pair."""
        raise NotImplementedError("The `__getitem__` method must be overrided.")

    def labels(self) -> list[str]:
        """
        Get the labels of data streams.

        These labels will be displayed as tab names in the frontend.
        The number of labels should equal to the number of data streams.
        """
        raise NotImplementedError("The `labels` method must be overrided.")


class Algorithm(Generic[X, Y]):
    """
    The base class for algorithms.

    This base class inherits the interface of Scikit-learn.
    Any customized subclass should override the following methods:
    - `fit`
    - `partial_fit`
    - `score`
    Optional methods which may be overrided include:
    - `labels`
    """

    def fit(self, data: list[tuple[X, Y]]):
        """
        Train from scratch.

        This method is called when initial training.
        The `partial_fit` method will be called when drift adaptation.
        """
        raise NotImplementedError("The `fit` method must be overrided.")

    def partial_fit(self, data: list[tuple[X, Y]], is_drift: list[bool] | None):
        """
        Adapt to the concept drift.

        This method is called when drift adaptation.
        The `fit` method will be called when intial training.
        The `is_drift` argument is directly from the `score` method,
        which is used to trigger drift adaptation on specific data streams.
        """
        raise NotImplementedError("The `partial_fit` method must be overrided.")

    def score(self, data: list[tuple[X, Y]]) -> tuple[list[float], list[bool] | None]:
        """
        Evaluate the prediction results, and detect if concept drift occurs.

        If the drift adaptation is triggered by the drift detection,
        return the detection results as the second position.
        Return `None` if models are updated for each batch of data.
        """
        raise NotImplementedError("The `score` method must be overrided.")

    def labels(self) -> list[str]:
        """
        Get the labels of possible additional plot.

        Provide labels of any possible additional plot,
        except evaluation results of each data stream.
        An example may be a heatmap of correlations between data streams.
        An empty list is returned by default.
        """
        return []
