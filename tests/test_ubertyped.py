from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import reveal_type

import pytest

from ubertyped import AsTypedDict, DataclassInstance, as_typed_dict

from .conftest import Data, DataAsTypedDict, IntWrapper


def test_as_typed_dict_runtime_behavior(data: Data) -> None:
    assert data.as_typed_dict() == asdict(data)
    assert as_typed_dict(data) == asdict(data)


def test_type_in_runtime() -> None:
    with pytest.raises(TypeError):
        AsTypedDict()
    with pytest.raises(TypeError):

        class _SubClass(AsTypedDict[Data]):
            ...


@pytest.mark.mypy_testing
def test_type(data_typed_dict: DataAsTypedDict) -> None:
    _x: DataAsTypedDict = data_typed_dict
    reveal_type(
        _x  # N: Revealed type is "TypedDict({'base': builtins.bool, 'version': TypedDict({'value': builtins.int}), 'command': builtins.str})"
    )
    _y: AsTypedDict[Data] = data_typed_dict
    reveal_type(
        _y  # N: Revealed type is "TypedDict({'base': builtins.bool, 'version': TypedDict({'value': builtins.int}), 'command': builtins.str})"
    )
    _z: AsTypedDict[IntWrapper] = data_typed_dict["version"]
    reveal_type(_z)  # N: Revealed type is "TypedDict({'value': builtins.int})"


@pytest.mark.mypy_testing
def test_sequences(data: Data) -> None:
    def as_typed_dicts(objects: Sequence[DataclassInstance]) -> list[AsTypedDict[DataclassInstance]]:
        return [as_typed_dict(obj) for obj in objects]

    converted = as_typed_dicts([data.version, data.version])
    reveal_type(converted)  # N: Revealed type is "builtins.list[TypedDict({'value': builtins.int})]"
    first = converted[0]
    reveal_type(first)  # N: Revealed type is "TypedDict({'value': builtins.int})"


@pytest.mark.mypy_testing
def test_mappings(data: Data) -> None:
    def as_typed_dicts_by_index(objects: Sequence[DataclassInstance]) -> dict[int, AsTypedDict[DataclassInstance]]:
        return {i: as_typed_dict(obj) for i, obj in enumerate(objects)}

    converted = as_typed_dicts_by_index([data])
    reveal_type(
        converted  # N: Revealed type is "builtins.dict[builtins.int, TypedDict({'base': builtins.bool, 'version': TypedDict({'value': builtins.int}), 'command': builtins.str})]"
    )
    first = converted[0]
    reveal_type(
        first  # N: Revealed type is "TypedDict({'base': builtins.bool, 'version': TypedDict({'value': builtins.int}), 'command': builtins.str})"
    )


@pytest.mark.mypy_testing
def test_method_return_type(data: Data) -> None:
    reveal_type(
        data.as_typed_dict  # N: Revealed type is "def () -> TypedDict({'base': builtins.bool, 'version': TypedDict({'value': builtins.int}), 'command': builtins.str})"
    )


@pytest.mark.mypy_testing
def test_overriding_fields() -> None:
    @dataclass
    class FloatWrapper(IntWrapper):
        value: float  # type: ignore[assignment]

    _x = as_typed_dict(FloatWrapper(1.1))
    reveal_type(
        _x  # N: Revealed type is "TypedDict({'value': builtins.float})"
    )
