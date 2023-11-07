from dataclasses import Field, asdict
from typing import Any, ClassVar, Generic, NoReturn, Protocol, TypeVar, cast

__all__ = ("AsTypedDict", "as_typed_dict")


_T = TypeVar("_T")


class AsTypedDict(dict[str, Any], Generic[_T]):
    """
    Class used as a marker for mypy plugin to convert dataclasses to TypedDicts.
    """

    def __new__(cls, *_args: Any, **_kwargs: Any) -> NoReturn:
        raise TypeError("Type AsTypedDict cannot be instantiated.")

    def __init_subclass__(cls, *_args: Any, **_kwargs: Any) -> NoReturn:
        raise TypeError("Cannot subclass AsTypedDict.")


class DataclassProtocol(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


DataclassInstance = TypeVar("DataclassInstance", bound=DataclassProtocol)


def as_typed_dict(obj: DataclassInstance, /) -> AsTypedDict[DataclassInstance]:
    """
    Converts the dataclass object to a TypedDict.
    Uses `dataclasses.asdict` and casts result to the appropriate type.
    """
    return cast(AsTypedDict[DataclassInstance], asdict(obj))
