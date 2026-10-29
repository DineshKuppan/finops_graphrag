from typing import List, Sequence

import numpy as np
from sklearn.ensemble import IsolationForest

from src.interfaces.anomaly_detector import IAnomalyDetector


class IsolationForestAnomalyDetector(IAnomalyDetector):
    """Unsupervised outlier scoring via scikit-learn's IsolationForest.

    `score_samples` is negated so the result follows the original paper's convention:
    ~0.5 for typical rows, approaching 1 for rows isolated in very few splits. A fixed
    `random_state` keeps scores reproducible between runs, which reviewers rely on.
    """

    def __init__(self, n_estimators: int = 200, random_state: int = 0):
        self.n_estimators = n_estimators
        self.random_state = random_state

    def score(self, rows: Sequence[Sequence[float]]) -> List[float]:
        matrix = np.asarray(rows, dtype=float)
        model = IsolationForest(n_estimators=self.n_estimators, random_state=self.random_state).fit(matrix)
        return (-model.score_samples(matrix)).tolist()
