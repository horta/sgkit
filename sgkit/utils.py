from typing import Any, List, Set, Tuple, Union

import numpy as np

from .typing import ArrayLike, DType


def check_array_like(
    a: Any,
    dtype: Union[None, DType, Set[DType]] = None,
    kind: Union[None, str, Set[str]] = None,
    ndim: Union[None, int, Set[int]] = None,
) -> None:
    """Raise an error if an array does not match given attributes (dtype, kind, dimensions).

    Parameters
    ----------
    a : Any
        Array of any type.
    dtype : Union[None, DType, Set[DType]], optional
        The dtype the array must have, by default None (don't check)
        If a set, then the array must have one of the dtypes in the set.
    kind : Union[None, str, Set[str]], optional
        The dtype kind the array must be, by default None (don't check).
        If a set, then the array must be one of the kinds in the set.
    ndim : Union[None, int, Set[int]], optional
        Number of dimensions the array must have, by default None (don't check)
        If a set, then the array must have one of the number of dimensions in the set.

    Raises
    ------
    TypeError
        * If `a` does not have the attibutes `dtype`, `shape`, and `ndim`.
        * If `a` does not have a dtype that matches `dtype`.
        * If `a` is not a dtype kind that matches `kind`.
    ValueError
        If the number of dimensions of `a` does not match `ndim`.
    """
    array_attrs = "ndim", "dtype", "shape"
    for k in array_attrs:
        if not hasattr(a, k):
            raise TypeError(f"Not an array. Missing attribute '{k}'")
    if dtype is not None:
        if isinstance(dtype, set):
            dtype = {np.dtype(t) for t in dtype}
            if a.dtype not in dtype:
                raise TypeError(
                    f"Array dtype ({a.dtype}) does not match one of {dtype}"
                )
        elif a.dtype != np.dtype(dtype):
            raise TypeError(f"Array dtype ({a.dtype}) does not match {np.dtype(dtype)}")
    if kind is not None:
        if isinstance(kind, set):
            if a.dtype.kind not in kind:
                raise TypeError(
                    f"Array dtype kind ({a.dtype.kind}) does not match one of {kind}"
                )
        elif a.dtype.kind != kind:
            raise TypeError(f"Array dtype kind ({a.dtype.kind}) does not match {kind}")
    if ndim is not None:
        if isinstance(ndim, set):
            if a.ndim not in ndim:
                raise ValueError(
                    f"Number of dimensions ({a.ndim}) does not match one of {ndim}"
                )
        elif ndim != a.ndim:
            raise ValueError(f"Number of dimensions ({a.ndim}) does not match {ndim}")


def encode_array(x: ArrayLike) -> Tuple[ArrayLike, List[Any]]:
    """Encode array values as integers indexing unique values.

    The codes created for each unique element in the array correspond
    to order of appearance, not the natural sort order for the array
    dtype.

    Examples
    --------

    >>> encode_array(['c', 'a', 'a', 'b'])
    (array([0, 1, 1, 2]), array(['c', 'a', 'b'], dtype='<U1'))

    Parameters
    ----------
    x : (M,) array-like
        Array of elements to encode of any type.

    Returns
    -------
    indexes : (M,) ndarray
        Encoded values as integer indices.
    values : ndarray
        Unique values in original array in order of appearance.
    """
    # argsort not implemented in dask: https://github.com/dask/dask/issues/4368
    names, index, inverse = np.unique(x, return_index=True, return_inverse=True)
    index = np.argsort(index)
    rank = np.empty_like(index)
    rank[index] = np.arange(len(index))
    return rank[inverse], names[index]


def split_array_chunks(n: int, blocks: int) -> Tuple[int, ...]:
    """Compute chunk sizes for an array split into blocks.

    This is similar to `numpy.split_array` except that it
    will compute the sizes of the resulting splits rather
    than explicitly partitioning an array.

    Parameters
    ----------
    n : int
        Number of array elements.
    blocks : int
        Number of partitions to generate chunk sizes for.

    Examples
    --------
    >>> split_array_chunks(7, 2)
    (4, 3)
    >>> split_array_chunks(7, 3)
    (3, 2, 2)
    >>> split_array_chunks(7, 1)
    (7,)
    >>> split_array_chunks(7, 7)
    (1, 1, 1, 1, 1, 1, 1)

    Raises
    ------
    ValueError
        * If `blocks` > `n`.
        * If `n` <= 0.
        * If `blocks` <= 0.

    Returns
    -------
    chunks : Tuple[int, ...]
        Number of elements associated with each block.
        This will equal `n//blocks` or `n//blocks + 1` for
        each block, depending on how many of the latter
        are necessary to make the partitioning complete.
    """
    if blocks > n:
        raise ValueError(
            f"Number of blocks ({blocks}) cannot be greater "
            f"than number of elements ({n})"
        )
    if n <= 0:
        raise ValueError(f"Number of elements ({n}) must be >= 0")
    if blocks <= 0:
        raise ValueError(f"Number of blocks ({blocks}) must be >= 0")
    n_div, n_mod = np.divmod(n, blocks)
    chunks = n_mod * (n_div + 1,) + (blocks - n_mod) * (n_div,)
    return chunks  # type: ignore[no-any-return]
