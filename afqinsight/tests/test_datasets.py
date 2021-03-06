from __future__ import absolute_import, division, print_function

import numpy as np
from afqinsight.datasets import make_classification
from collections import defaultdict
from functools import partial
from sklearn.utils.testing import assert_equal
from sklearn.utils.testing import assert_array_almost_equal
from sklearn.utils.testing import assert_raises


def test_make_classification():
    weights = [0.1, 0.25]
    X, y = make_classification(
        n_samples=100,
        n_features=20,
        n_informative=5,
        n_redundant=1,
        n_repeated=1,
        n_classes=3,
        n_clusters_per_class=1,
        hypercube=False,
        shift=None,
        scale=None,
        weights=weights,
        random_state=0,
    )

    assert_equal(weights, [0.1, 0.25])
    assert_equal(X.shape, (100, 20), "X shape mismatch")
    assert_equal(y.shape, (100,), "y shape mismatch")
    assert_equal(np.unique(y).shape, (3,), "Unexpected number of classes")
    assert_equal(sum(y == 0), 10, "Unexpected number of samples in class #0")
    assert_equal(sum(y == 1), 25, "Unexpected number of samples in class #1")
    assert_equal(sum(y == 2), 65, "Unexpected number of samples in class #2")

    # Test for n_features > 30
    X, y = make_classification(
        n_samples=2000,
        n_features=31,
        n_informative=31,
        n_redundant=0,
        n_repeated=0,
        hypercube=True,
        scale=0.5,
        random_state=0,
    )

    assert_equal(X.shape, (2000, 31), "X shape mismatch")
    assert_equal(y.shape, (2000,), "y shape mismatch")
    assert_equal(
        np.unique(X.view([("", X.dtype)] * X.shape[1]))
        .view(X.dtype)
        .reshape(-1, X.shape[1])
        .shape[0],
        2000,
        "Unexpected number of unique rows",
    )

    assert_raises(
        ValueError, make_classification, n_features=2, n_informative=2, n_redundant=3
    )
    assert_raises(ValueError, make_classification, weights=weights, n_classes=5)


def test_make_classification_informative_features():
    """Test the construction of informative features in make_classification

    Also tests `n_clusters_per_class`, `n_classes`, `hypercube` and
    fully-specified `weights`.
    """
    # Create very separate clusters; check that vertices are unique and
    # correspond to classes
    class_sep = 1e6
    make = partial(
        make_classification,
        class_sep=class_sep,
        n_redundant=0,
        n_repeated=0,
        flip_y=0,
        shift=0,
        scale=1,
        shuffle=False,
    )

    for n_informative, weights, n_clusters_per_class in [
        (2, [1], 1),
        (2, [1 / 3] * 3, 1),
        (2, [1 / 4] * 4, 1),
        (2, [1 / 2] * 2, 2),
        (2, [3 / 4, 1 / 4], 2),
        (10, [1 / 3] * 3, 10),
    ]:
        n_classes = len(weights)
        n_clusters = n_classes * n_clusters_per_class
        n_samples = n_clusters * 50

        for hypercube in (False, True):
            X, y = make(
                n_samples=n_samples,
                n_classes=n_classes,
                weights=weights,
                n_features=n_informative,
                n_informative=n_informative,
                n_clusters_per_class=n_clusters_per_class,
                hypercube=hypercube,
                random_state=0,
            )

            assert_equal(X.shape, (n_samples, n_informative))
            assert_equal(y.shape, (n_samples,))

            # Cluster by sign, viewed as strings to allow uniquing
            signs = np.sign(X)
            signs = signs.view(dtype="|S{0}".format(signs.strides[0]))
            unique_signs, cluster_index = np.unique(signs, return_inverse=True)

            assert_equal(
                len(unique_signs),
                n_clusters,
                "Wrong number of clusters, or not in distinct " "quadrants",
            )

            clusters_by_class = defaultdict(set)
            for cluster, cls in zip(cluster_index, y):
                clusters_by_class[cls].add(cluster)
            for clusters in clusters_by_class.values():
                assert_equal(
                    len(clusters),
                    n_clusters_per_class,
                    "Wrong number of clusters per class",
                )
            assert_equal(len(clusters_by_class), n_classes, "Wrong number of classes")

            assert_array_almost_equal(
                np.bincount(y) / len(y) // weights,
                [1] * n_classes,
                err_msg="Wrong number of samples " "per class",
            )

            # Ensure on vertices of hypercube
            for cluster in range(len(unique_signs)):
                centroid = X[cluster_index == cluster].mean(axis=0)
                if hypercube:
                    assert_array_almost_equal(
                        np.abs(centroid),
                        [class_sep] * n_informative,
                        decimal=0,
                        err_msg="Clusters are not " "centered on hypercube " "vertices",
                    )
                else:
                    assert_raises(
                        AssertionError,
                        assert_array_almost_equal,
                        np.abs(centroid),
                        [class_sep] * n_informative,
                        decimal=0,
                        err_msg="Clusters should not be cenetered "
                        "on hypercube vertices",
                    )

    assert_raises(
        ValueError,
        make,
        n_features=2,
        n_informative=2,
        n_classes=5,
        n_clusters_per_class=1,
    )

    assert_raises(
        ValueError,
        make,
        n_features=2,
        n_informative=2,
        n_classes=3,
        n_clusters_per_class=2,
    )
