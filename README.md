# Übertyped

Convert `dataclass` to `TypedDict` for fun and type safety 🪄

> **uber-** _/ˈuːbə/_ to a great or extreme degree

## Requirements

- `python>=3.11`
- `mypy>=1.0.1`

## Installation

```shell
pip install ubertyped
```

### Mypy plugin

Add `ubertyped.mypy_plugin` to the list of plugins in your [mypy config file](https://mypy.readthedocs.io/en/latest/config_file.html)
(for example `pyproject.toml`)

```toml
[tool.mypy]
python_version = "3.11"
plugins = ["ubertyped.mypy_plugin"]
```

## Features

- ✅ `AsTypedDict[T]` generic type converting `dataclasse`s to `TypeDict`s
- ✅ `as_typed_dict` utility function wrapping `dataclasses.asdict`
- ✅ Support for usage with `TypeVar`s
- ✅ Nested dataclasses
- ✅ Compatibility with other typecheckers such as `Pylance` and `Pyright`
- ✅ Zero dependencies

## Usage

```python
from dataclasses import asdict, dataclass
from typing import Self, reveal_type

from ubertyped import AsTypedDict, as_typed_dict


@dataclass
class Base:
    base: bool


@dataclass
class IntWrapper:
    value: int


@dataclass
class Data(Base):
    version: IntWrapper
    command: str

    def as_typed_dict(self) -> AsTypedDict[Self]:
        return as_typed_dict(self)


data = Data(version=IntWrapper(1), command="c", base=False)

# 🎉 Type-safe conversion!
td = as_typed_dict(data)
reveal_type(td)
# Revealed type is "TypedDict({'base': builtins.bool, 'version': TypedDict({'value': builtins.int}), 'command': builtins.str})"

# 🎉 Works with nested dataclasses too!
reveal_type(td["version"]["value"])
# Revealed type is "builtins.int"


# 🎉 Binding `Self` in methods is resolved correctly!
reveal_type(data.as_typed_dict)
# Revealed type is "def () -> TypedDict({'base': builtins.bool, 'version': TypedDict({'value': builtins.int}), 'command': builtins.str})"

# 🎉 At runtime, `as_typed_dict` is just a wrapper around `dataclasses.asdict`!
if asdict(data) == data.as_typed_dict():
    print("✅")
else:
    print("❌")
```
