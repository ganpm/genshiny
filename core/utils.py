# flake8: noqa: E701
from typing import Any
import numpy as np

from core.text import TEXT


def norm_dict(
        data: dict[Any, float],
        total: float = 1.0,
        precision: int = 2,
        ) -> dict[int, float]:
    """Normalize the values in the dictionary to sum to 1.0."""

    total = total or sum(data.values())
    if total == 0:
        return {k: 0.0 for k in data}

    if precision is None:
        return {k: v / total for k, v in data.items()}

    return {k: round(v / total * 100, precision) for k, v in data.items()}


def convert_dict(
        data: dict[int, float],
        mode: str,
        ) -> dict[int, float]:
    """Convert the values in the dictionary according to the specified mode."""

    out = {}

    match mode:
        case TEXT.LE:
            out = {k: sum(v for key, v in data.items() if key <= k) for k in data}
        case TEXT.LT:
            out = {k: sum(v for key, v in data.items() if key < k) for k in data}
        case TEXT.GE:
            out = {k: sum(v for key, v in data.items() if key >= k) for k in data}
        case TEXT.GT:
            out = {k: sum(v for key, v in data.items() if key > k) for k in data}
        case TEXT.EQ:
            out = data.copy()
        case _:
            raise ValueError(f"Unknown conversion mode: {mode}")

    return out


def array_2d_from_dict(
        data: dict[tuple[int, int], float],
        x_labels: list[int],
        y_labels: list[int],
        ) -> np.ndarray:
    """Build a 2D numpy array from a dictionary."""
    
    size = (len(y_labels), len(x_labels))

    array = np.zeros(size, dtype=float)
    for y, b in enumerate(y_labels):
        for x, a in enumerate(x_labels):
            array[y, x] = data.get((b, a), 0.0)

    return array


def joint_pmf_variant(
        p: np.ndarray,
        opx: str,
        opy: str,
        ) -> np.ndarray:
    """
    Compute 2D array of `P(X <opx> x_i, Y <opy> y_j)` for all `i, j`.

    Parameters
    ----------
    `p` : 2D numpy array
        Joint PMF such that `p[i, j] = P(X=x_i, Y=y_j)`.
        Assumes `X` and `Y` are sorted ascending.
    `opx`, `opy` : string containing an operation

    Returns
    -------
    `numpy.ndarray`
        2D array of same shape as `p` giving `P(X <opx> x_i, Y <opy> y_j)`.
    """
    
    n, m = p.shape

    # Function to get slice range for an operator
    def get_slices(op, size):
        if op == TEXT.LT:  return lambda i: slice(0, i)
        if op == TEXT.LE:  return lambda i: slice(0, i+1)
        if op == TEXT.EQ:  return lambda i: slice(i, i+1)
        if op == TEXT.GT:  return lambda i: slice(i+1, size)
        if op == TEXT.GE:  return lambda i: slice(i, size)
        raise ValueError(f"Invalid operator: {op}")

    sy = get_slices(opy, n)
    sx = get_slices(opx, m)

    # Compute via slicing directly (no fancy flips)
    out = np.zeros_like(p)
    for i in range(n):
        for j in range(m):
            out[i, j] = p[sy(i), sx(j)].sum()

    return out
