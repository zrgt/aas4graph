#  Copyright (C) 2021  Igor Garmaev, garmaev@gmx.net
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/

import inspect
import logging
import typing
from abc import ABCMeta
from collections import abc
from enum import Enum
from typing import Union, Tuple, Iterable, Type, Any, Dict, List

from basyx.aas.model import ModelReference, Reference, AssetAdministrationShell, Submodel, SubmodelElementList, \
    SubmodelElementCollection, ConceptDescription, ValueReferencePair

from aas_mapping.settings import IGNORED_PARENT_CLASSES

TYPING_TYPES = {typing.AbstractSet, typing.Callable, typing.Dict, typing.List, typing.NamedTuple,
                typing.NoReturn, typing.Set, typing.Sequence, typing.Tuple, typing.Type,
                typing.TypeVar, typing.Union}


def getOrigin(obj) -> typing.Type:
    """Return obj.__origin__ if it has it else return obj"""
    if hasattr(obj, "__origin__"):
        obj = obj.__origin__
    return obj


def getArgs(obj) -> typing.Tuple[typing.Type]:
    try:
        args = obj.__args__
    except AttributeError:
        args = tuple()
    return args


def isTypehint(obj) -> bool:
    obj = getOrigin(obj)
    try:
        if obj in TYPING_TYPES or type(obj) is typing.TypeVar:
            return True
    except TypeError as e:
        logging.exception(e)
    return inspect.isclass(obj)


def isUnion(typeHint):
    typ = getOrigin(typeHint)
    if typ == Union:
        return True
    return False


def isOptional(typeHint):
    if isUnion(typeHint):
        args = getArgs(typeHint)
        if type(None) in args:
            return True
    return False


def removeOptional(typehint):
    """Remove Nonetype from typehint if typehint is Optional[...], else return typehint"""
    if isOptional(typehint):
        args = list(getArgs(typehint))
        args.remove(type(None))
        typehint = args[0] if len(args) == 1 else typing.Union[tuple(args)]
    return typehint


def checkType(obj, typeHint):
    if typeHint is None:
        return True

    origin = getOrigin(typeHint)
    args = getArgs(typeHint)
    objType = type(obj)

    if objType == typeHint:
        return True

    if type(typeHint) is typing.ForwardRef:
        typeHintName = typeHint.__forward_arg__
        return getTypeName(type(obj)) == typeHintName

    if isUnion(typeHint):
        for typHint in args:
            if checkType(obj, typHint):
                return True
        else:
            return False

    if isinstance(obj, ModelReference):
        return checkTypeModelRef(obj, typeHint)

    if isIterableType(origin) and objType is origin:
        return True

    if origin is abc.Iterable:
        return isIterableType(objType)

    return isinstance(obj, origin)


def checkTypeModelRef(aasref, typehint):
    """Check if"""
    if not isinstance(aasref, ModelReference):
        raise TypeError("arg 1 must be of type ModelReference")

    origin = getOrigin(typehint)
    args = getArgs(typehint)

    if origin is ModelReference or type(aasref) is ModelReference:
        if args:
            if isinstance(args[0], typing.ForwardRef):
                arg = args[0].__forward_arg__
                return getTypeName(aasref.type) == arg
            try:
                return issubclass(aasref.type, args)
            except TypeError as e:
                logging.exception(f"Error occurred while checking: {aasref.type} and {args}", e)
                return False
        else:
            return True
    else:
        return False


def getTypeName(objType) -> str:
    if not isTypehint(objType) and not isoftype(objType, Enum):
        raise TypeError("Arg 1 must be type or typehint:", objType)

    nameAttrs = ("__name__", "_name", "name")
    for nameAttr in nameAttrs:
        try:
            res = getattr(objType, nameAttr)
            if res:
                break
        except (AttributeError, TypeError) as e:
            pass
    else:
        name = str(objType)
        # delete args if exist
        name = name.partition("[")[0]
        # delete type parents and return only type name
        res = name.rpartition(".")[2]
    return res


def getTypeHintName(typehint) -> str:
    if not isTypehint(typehint):
        raise TypeError("Arg 1 must be type or typehint:", typehint)

    optional = isOptional(typehint)
    if optional:
        typehint = removeOptional(typehint)
        optional = True

    typ = getTypeName(typehint)
    try:
        args = []
        for arg in typehint.__args__:
            args.append(getTypeHintName(arg))
        res = f"{typ}{args}".replace("'", "")
    except AttributeError:
        res = typ

    if optional:
        res = f"Optional[{res}]"

    return res


def issubtype(typ, types: Union[type, Tuple[Union[type, tuple], ...]]) -> bool:
    """
    Return whether 'typ' is a derived from another class or is the same class.
    The function also supports typehints. Checks whether typ is subtype of Typehint origin
    :param typ: type to check
    :param types: class or type annotation or tuple of classes or type annotations
    :raise TypeError if arg 1 or arg2 are not types or typehints:"
    """
    if not isTypehint(typ):
        raise TypeError("Arg 1 must be type or typehint:", typ)

    if not isinstance(types, tuple):
        types = (types,)

    for tp in types:
        if not isTypehint(tp):
            raise TypeError("Arg 2 must be type, typehint or tuple of types/typehints:", types)

    for tp in types:
        if type(tp) == typing.TypeVar:
            tp = tp.__bound__
            if issubtype(typ, tp):
                return True
        elif _issubtype(typ, tp):
            return True
    return False

def isTypeVar(typehint):
    return type(typehint) is typing.TypeVar


def _issubtype(typ1, typ2: type) -> bool:
    if isTypeVar(typ1):
        typ1 = typ1.__bound__
    if isTypeVar(typ2):
        typ2 = typ2.__bound__

    typ1 = removeOptional(typ1)

    if isUnion(typ1):
        if isUnion(typ2):
            return True
        else:
            return False
    if isUnion(typ2):
        if hasattr(typ2, "__args__") and typ2.__args__:
            typ2 = typ2.__args__
            return issubtype(typ1, typ2)
        else:
            return isUnion(typ1)

    if getTypeName(typ2) == "Type" and hasattr(typ2, "__args__") and typ2.__args__:
        args = typ2.__args__ if not isUnion(typ2.__args__[0]) else typ2.__args__[0].__args__
        if str(args[0]) == "+CT_co":  # type2 is just Type without args TODO fix later
            return getTypeName(typ1) == "Type"
        return issubtype(typ1, args)

    if hasattr(typ1, "__args__") and typ1.__args__:
        typ1 = typ1.__origin__
    if hasattr(typ2, "__args__") and typ2.__args__:
        typ2 = typ2.__origin__

    if type(None) in (typ1, typ2):
        return typ1 == typ2

    try:
        return issubclass(typ1, typ2)
    except TypeError:
        return issubclass(typ1.__origin__, typ2)


def isoftype(obj, types: Union[type, Tuple[Union[type, tuple], ...]]) -> bool:
    try:
        for tp in types:
            if not isTypehint(tp):
                raise TypeError("Arg 2 must be type, typehint or tuple of types/typehints:", types)
    except TypeError:
        if not isTypehint(types):
            raise TypeError("Arg 2 must be type, typehint or tuple of types/typehints:", types)

    try:
        for tp in types:
            if _isoftype(obj, tp):
                return True
        return False
    except TypeError as e:
        return _isoftype(obj, types)


def _isoftype(obj, typ) -> bool:
    if isUnion(typ) and hasattr(typ, "__args__") and typ.__args__:
        types = typ.__args__
        return isoftype(obj, types)

    if getTypeName(typ) == "Type" and hasattr(typ, "__args__") and typ.__args__:
        args = typ.__args__ if not isUnion(typ.__args__[0]) else typ.__args__[0].__args__
        if type(obj) in (type, ABCMeta):
            return issubtype(obj, args)
        else:
            return False

    #  TypeVar
    if hasattr(typ, "__bound__"):
        typ = typ.__bound__
        return issubtype(obj, typ)

    if hasattr(typ, "__args__") and typ.__args__:
        typ = typ.__origin__

    return isinstance(obj, typ)


def isSimpleIterableType(objType):
    COMPLEX_ITERABLE_TYPES = (AssetAdministrationShell, Submodel, SubmodelElementList, SubmodelElementCollection,
                              ConceptDescription)
    if not isTypehint(objType):
        raise TypeError("Arg 1 must be type or typehint:", objType)
    return False if issubtype(objType, COMPLEX_ITERABLE_TYPES) else isIterableType(objType)


def isIterableType(objType):
    return issubtype(objType, Iterable) and not issubtype(objType, (str, bytes, bytearray))


def isIterable(obj):
    return isIterableType(type(obj))


def getAttrTypeHint(objType, attr, delOptional=True):
    params = getReqParams4init(objType, rmDefParams=False, delOptional=delOptional)

    # Determine type hint from initialization parameters or property type hint
    try:
        typeHint = params.get(attr, params.get(f"{attr}_", None))
        if typeHint is None:
            func = getattr(objType, attr)
            typehints = typing.get_type_hints(func.fget)
            typeHint = typehints["return"]
    except KeyError:
        raise KeyError(f"Attribute {attr} not found in {objType}")
    except Exception as e:
        logging.exception(e)
        raise KeyError(f"Failed to get type hint for attribute {attr} in {objType}")

    # Process type hint arguments to remove Ellipsis if present
    try:
        args = list(getArgs(typeHint))
        if Ellipsis in args:
            args.remove(Ellipsis)
            origin = typing.get_origin(typeHint)
            if origin:
                typeHint = origin[tuple(args)]
    except AttributeError as e:
        logging.exception(e)

    return typeHint


def getIterItemTypeHint(iterableTypehint):
    """Return typehint for item which should be in iterable"""
    if not isTypehint(iterableTypehint):
        raise TypeError("Arg 1 must be type or typehint:", iterableTypehint)

    iterableTypehint = removeOptional(iterableTypehint)
    origin = getOrigin(iterableTypehint)
    args = getArgs(iterableTypehint)

    if args:
        if len(args) > 1:
            raise KeyError("Typehint of iterable has more then one attribute:", args)
        attrType = args[0]

    if not isTypehint(attrType):
        raise TypeError("Found value is not type or typehint:", attrType)

    return attrType


def typeHintToType(typeHint):
    if issubtype(typeHint, typing.Dict):
        return dict
    elif issubtype(typeHint, typing.List):
        return list
    elif issubtype(typeHint, typing.Tuple):
        return tuple
    elif issubtype(typeHint, typing.Set):
        return set
    elif issubtype(typeHint, typing.Iterable):
        return list
    else:
        return typeHint


def typecast(val, typ):
    if type(val) is typ:
        return val
    elif typ in (type, None):
        return val
    elif typ in (type(None),):
        return None
    else:
        return typ(val)


def getParamsAndTypehints4init(objType: Type, withDefaults=True) -> tuple[dict[str, Any], dict[str, Any]] | dict[
    str, Any]:
    """Return params for init with their type and default values"""
    objType = resolveBaseType(objType)

    g = getfullargspecoftypeinit(objType)
    paramsAndTypehints = g.annotations.copy()
    if 'return' in paramsAndTypehints:
        paramsAndTypehints.pop('return')
    paramsAndTypehints = replaceForwardRefsWithTypes(paramsAndTypehints)

    if withDefaults:
        defaults = g.defaults
        paramsDefaults = _getDefaultValuesOfParams(paramsAndTypehints.keys(), defaults)
        return paramsAndTypehints, paramsDefaults

    return paramsAndTypehints


def resolveBaseType(objType: Type) -> Type:
    origin = typing.get_origin(objType)
    return origin if origin else objType


def getfullargspecoftypeinit(objType: Type) -> inspect.FullArgSpec:
    if not (hasattr(objType, "__init__") or hasattr(objType, "__new__")):
        raise TypeError(f"no init or new func in objectType: {objType}")

    if hasattr(objType, "__init__"):
        g = inspect.getfullargspec(objType.__init__)
        if hasattr(objType, "__new__") and not g.annotations:
            g = inspect.getfullargspec(objType.__new__)
    else:
        raise TypeError(f"no init or new func in objectType: {objType}")

    if g.kwonlydefaults:
        g.defaults = g.defaults + tuple(g.kwonlydefaults.values())
    return g


def replaceForwardRefsWithTypes(paramsTypehints: Dict[str, Any]) -> Dict[str, Any]:
    for param in paramsTypehints:
        typeHint = paramsTypehints[param]
        paramsTypehints[param] = resolveForwardRef(typeHint)
    return paramsTypehints


def resolveForwardRef(typeHint: Any) -> Any:
    types = {
        "Reference": AssetAdministrationShell,
        "AssetAdministrationShell": AssetAdministrationShell,
        "ValueReferencePair": ValueReferencePair,
    }

    origin = typing.get_origin(typeHint)
    args = typing.get_args(typeHint)

    if origin is None and not args:
        # It's neither a generic type nor a Union
        if type(typeHint) is typing.ForwardRef:
            fullReferencedTypeName = typeHint.__forward_arg__
            referencedTypeName = fullReferencedTypeName.split(".")[-1]
            typeHint = types[referencedTypeName]
        return typeHint

    # Replace ForwardRefs in the arguments
    new_args = tuple(resolveForwardRef(arg) for arg in args)

    if origin:
        # Reconstruct generic types like Optional or Tuple
        return origin[new_args]
    else:
        raise TypeError(f"no origin in typeHint, only args: {typeHint}")


def _getDefaultValuesOfParams(params: Iterable[str], defaults: Tuple[Any]) -> Dict[str, Any]:
    params = list(params)
    paramsDefaults = {}
    if params and defaults:
        paramsWithDefaults = params[len(params) - len(defaults):]
        paramsDefaults = dict(zip(paramsWithDefaults, defaults))
    return paramsDefaults


def getReqParams4init(objType: Type, rmDefParams=True,
                      attrsToHide=None, delOptional=True) -> Dict[str, Type]:
    """Return required params for init with their type"""
    paramsTypehints, paramsDefaults = getParamsAndTypehints4init(objType)

    if rmDefParams and paramsDefaults:
        for i in range(len(paramsDefaults)):
            paramsTypehints.popitem()

    if delOptional:
        for param in paramsTypehints:
            typeHint = paramsTypehints[param]
            paramsTypehints[param] = removeOptional(typeHint)

    if attrsToHide:
        for attr in attrsToHide:
            try:
                paramsTypehints.pop(attr)
            except KeyError:
                continue

    return paramsTypehints


def nameIsSpecial(method_name):
    """Returns true if the method name starts with underscore"""
    return method_name.startswith('_')


def getAttrs(obj, exclSpecial=True, exclCallable=True) -> List[str]:
    attrs: List[str] = dir(obj)
    if exclSpecial:
        attrs[:] = [attr for attr in attrs if not nameIsSpecial(attr)]
    if exclCallable:
        attrs[:] = [attr for attr in attrs
                    if type(getattr(obj, attr)) in (type, ABCMeta)
                    or not callable(getattr(obj, attr))]
    return attrs


def getParams4init(objType: Type) -> List[str]:
    """Return params for init"""
    objType = resolveBaseType(objType)
    g = getfullargspecoftypeinit(objType)
    paramsAndTypehints = g.annotations.copy()
    if "return" in paramsAndTypehints:
        paramsAndTypehints.pop("return")
    return list(paramsAndTypehints.keys())


def get_all_parent_classes(obj):
    parent_classes = obj.__class__.__mro__
    return [cls.__name__ for cls in parent_classes if cls not in IGNORED_PARENT_CLASSES]
