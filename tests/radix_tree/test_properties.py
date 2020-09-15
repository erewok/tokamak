"""
   Property-based tests are isolated to here
"""
import re

from hypothesis import given
from hypothesis import strategies

from tokamak.radix_tree import node, tree, utils


@given(strategies.text(), strategies.text())
def test_nonequal_indices(left, right):  # type: ignore
    result = utils.first_nonequal_idx(left, right)
    assert result >= 0
    if left == right:
        assert result == len(left) == len(right)
    else:
        assert result <= min((len(left), len(right)))
