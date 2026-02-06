import numpy as np
from scipy.sparse import csr_matrix

from quartumse.observables import Observable


def test_observable_sparse_matrix_round_trip() -> None:
    observable = Observable(pauli_string="XYZI", coefficient=-0.5)

    dense = observable.to_matrix()
    sparse_mat = observable.to_sparse_matrix()

    assert isinstance(sparse_mat, csr_matrix)
    np.testing.assert_allclose(dense, sparse_mat.toarray())


def test_observable_sparse_matrix_identity() -> None:
    observable = Observable(pauli_string="IIII", coefficient=2.0)

    dense = observable.to_matrix()
    sparse_mat = observable.to_sparse_matrix()

    expected = 2.0 * np.eye(2**len(observable.pauli_string), dtype=complex)
    np.testing.assert_allclose(dense, expected)
    np.testing.assert_allclose(sparse_mat.toarray(), expected)
