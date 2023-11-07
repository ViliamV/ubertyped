from dataclasses import dataclass
from typing import Self

import pytest

import ubertyped


@dataclass
class Base:
    base: bool


@dataclass
class IntWraper:
    value: int


@dataclass
class Data(Base):
    version: IntWraper
    command: str

    def as_typed_dict(self) -> ubertyped.AsTypedDict[Self]:
        return ubertyped.as_typed_dict(self)


@pytest.fixture
def data() -> Data:
    return Data(version=IntWraper(1), command="c", base=False)


@pytest.fixture
def data_typed_dict(data: Data) -> ubertyped.AsTypedDict[Data]:
    return ubertyped.as_typed_dict(data)


DataAsTypedDict = ubertyped.AsTypedDict[Data]
