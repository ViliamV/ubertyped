from collections.abc import Callable
from typing import Final, TypeGuard, cast

from mypy.checker import TypeChecker
from mypy.errorcodes import TYPE_ARG
from mypy.nodes import Context, TypeInfo, Var
from mypy.plugin import (
    AnalyzeTypeContext,
    FunctionContext,
    MethodContext,
    Plugin,
)
from mypy.typeanal import TypeAnalyser
from mypy.types import (
    AnyType,
    Instance,
    Type,
    TypeAliasType,
    TypedDictType,
    TypeOfAny,
    TypeVarType,
    UnboundType,
    UninhabitedType,
)

_MIN_MYPY_VERSION = (1, 0, 1)
_TYPE_TO_ANALYZE: Final = "ubertyped.AsTypedDict"
_DATACLASS_TAG: Final = "dataclass_tag"  # Internally used by mypy to mark dataclasses


def _is_dataclass(obj: Instance) -> bool:
    return _DATACLASS_TAG in obj.type.metadata


def _dataclass_to_typeddict(instance: Instance, api: TypeAnalyser | TypeChecker) -> TypedDictType:
    items: dict[str, Type] = {}
    for cls in instance.type.mro:
        if _DATACLASS_TAG not in cls.metadata:
            continue
        for name, sym in cls.names.items():
            if isinstance(sym.node, Var) and sym.type is not None and not sym.plugin_generated:
                items[name] = (
                    _dataclass_to_typeddict(sym.type, api)
                    if isinstance(sym.type, Instance) and _is_dataclass(sym.type)
                    else sym.type
                )
    fallback = (
        api.named_type("typing._TypedDict", [])
        if isinstance(api, TypeAnalyser)
        else api.named_type("typing._TypedDict")
    )
    return TypedDictType(items, required_keys=set(items.keys()), fallback=fallback)


def _default_type_analysis(api: TypeAnalyser, type_: UnboundType) -> Type:
    """Mimics default mypy type analysis without recursion"""
    symbol_table_node = api.lookup_qualified(type_.name, type_)
    if symbol_table_node is None:
        return AnyType(TypeOfAny.special_form)
    node = symbol_table_node.node
    if isinstance(node, TypeInfo):
        return api.analyze_type_with_type_info(node, type_.args, type_)
    return AnyType(TypeOfAny.special_form)


def _is_type_to_analyze(obj: Type, /) -> TypeGuard[Instance]:
    return isinstance(obj, Instance) and obj.type.fullname == _TYPE_TO_ANALYZE


def _try_conversion(obj: Instance, api: TypeChecker | TypeAnalyser, context: Context) -> Type:
    type_name = obj.type.name
    if (args_len := len(obj.args)) != 1:
        api.fail(
            f'"{type_name}" expects 1 type argument, but {args_len} given',
            context,
            code=TYPE_ARG,
        )
        return UninhabitedType()
    argument = obj.args[0]
    if isinstance(argument, TypeAliasType) and (expanded := argument.expand_all_if_possible()) is not None:
        argument = expanded
    if isinstance(argument, TypeVarType):
        upper_bound = argument.upper_bound
        if isinstance(upper_bound, Instance) and _is_dataclass(upper_bound):
            return _dataclass_to_typeddict(upper_bound, api)
        return obj
    if not isinstance(argument, Instance):
        api.fail(
            f'Argument 1 to "{type_name}" has incompatible type "{argument}"',
            context,
        )
        return UninhabitedType()
    if not _is_dataclass(argument):
        api.fail(
            f'Argument 1 to "{type_name}" is not dataclass',
            context,
        )
        return UninhabitedType()
    return _dataclass_to_typeddict(argument, api)


def _analyze_type(ctx: AnalyzeTypeContext) -> Type:
    api = cast(TypeAnalyser, ctx.api)
    default = _default_type_analysis(api, ctx.type)
    if _is_type_to_analyze(default):
        return _try_conversion(default, api, ctx.context)
    return default


def _analyze_return_type(ctx: FunctionContext | MethodContext) -> Type:
    api = cast(TypeChecker, ctx.api)
    return_type = ctx.default_return_type
    if not isinstance(return_type, Instance):
        return return_type
    if _is_type_to_analyze(return_type):
        return _try_conversion(return_type, api, ctx.context)
    elif any(_is_type_to_analyze(arg) for arg in return_type.args):
        new_args: list[Type] = []
        for arg in return_type.args:
            if _is_type_to_analyze(arg):
                new_args.append(_try_conversion(arg, api, ctx.context))
            else:
                new_args.append(arg)
        return return_type.copy_modified(args=new_args)
    else:
        return return_type


class DataclassAsTypedDictPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str) -> Callable[[AnalyzeTypeContext], Type] | None:
        if fullname == _TYPE_TO_ANALYZE:
            return _analyze_type
        return None

    def get_function_hook(self, fullname: str) -> Callable[[FunctionContext], Type] | None:  # noqa: ARG002
        return _analyze_return_type

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:  # noqa: ARG002
        return _analyze_return_type


def _version_str_to_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.partition("+")[0].split("."))


def plugin(version: str) -> type[Plugin]:
    if _version_str_to_tuple(version) >= _MIN_MYPY_VERSION:
        return DataclassAsTypedDictPlugin
    return Plugin
