import pytest
from hypothesis import given, strategies
from tokamak import methods


@given(strategies.sampled_from(methods.Method))
def test_method_prop(meth):
    assert methods.Method.read(meth.value) is meth
    assert methods.Method.read(meth.value.lower()) is meth


@pytest.mark.parametrize(
    "val,result",
    (
        ("CoNnECT", methods.Method.CONNECT),
        ("", None),
        (None, None),
    ),
)
def test_method_read(val, result):
    assert methods.Method.read(val) is result
