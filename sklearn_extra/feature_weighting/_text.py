import numpy as np
import scipy.sparse as sp

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_array, check_X_y
from sklearn.preprocessing import LabelEncoder


class TfigmTransformer(BaseEstimator, TransformerMixin):
    """Apply TF-IGM feature weighting

    Parameters
    ----------
    alpha : float, default=7
      regularization parameter

    References
    ----------
    Chen, Kewen, et al. "Turning from TF-IDF to TF-IGM for term weighting
    in text classification." Expert Systems with Applications 66 (2016):
    245-260.
    """

    def __init__(self, alpha=7.0):
        self.alpha = alpha

    def _fit(self, X, y):
        self._le = LabelEncoder().fit(y)
        class_freq = np.zeros((len(self._le.classes_), X.shape[1]))

        X_nz = X != 0
        if sp.issparse(X_nz):
            X_nz = X_nz.asformat("csr", copy=False)

        for idx, class_label in enumerate(self._le.classes_):
            y_mask = y == class_label
            n_samples = y_mask.sum()
            class_freq[idx, :] = X_nz[y_mask].sum(axis=0) / n_samples

        self._class_freq = class_freq
        self._class_rank = np.argsort(-self._class_freq, axis=0)
        f1 = self._class_freq[
            self._class_rank[0, :], np.arange(self._class_freq.shape[1])
        ]
        fk = (self._class_freq * (self._class_rank + 1)).sum(axis=0)
        self.coef_ = 1 + self.alpha * (f1 / fk)
        return self

    def fit(self, X, y):
        X, y = check_X_y(X, y, accept_sparse=["csr", "csc"])
        self._fit(X, y)
        return self

    def _transform(self, X):
        if sp.issparse(X):
            X_tr = X @ sp.diags(self.coef_)
        else:
            X_tr = X * self.coef_[None, :]
        return X_tr

    def transform(self, X):
        X = check_array(X, accept_sparse=["csr", "csc"])
        X_tr = self._transform(X)
        return X_tr

    def fit_transform(self, X, y):
        X, y = check_X_y(X, y, accept_sparse=["csr", "csc"])
        self._fit(X, y)
        X_tr = self._transform(X)
        return X_tr
