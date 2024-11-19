"""
   Property-based tests are isolated to here
"""
from hypothesis import given, strategies
from tokamak.radix_tree import utils


@given(strategies.text(), strategies.text())
def test_nonequal_indices(left, right):  # type: ignore
    result = utils.first_nonequal_idx(left, right)
    assert result >= 0
    if left == right:
        assert result == len(left) == len(right)
    else:
        assert result <= min((len(left), len(right)))
