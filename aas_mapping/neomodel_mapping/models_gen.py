import datetime
import inspect
from enum import Enum

import basyx.aas.model.submodel as submodel_types
from basyx.aas.model import Reference, MultiLanguageNameType, LangStringSet, ModelReference
from dateutil.relativedelta import relativedelta

from aas_mapping.settings import NODE_TYPES, RELATIONSHIP_TYPES, ATTRS_TO_IGNORE
from aas_mapping.util_type import getParamsAndTypehints4init, issubtype, isUnion, removeOptional, \
    resolveBaseType, resolveForwardRef, isOptional, isSimpleIterableType

TYPE_NODE_MAP = {
    str: 'StringProperty',
    bytes: 'StringProperty',
    Enum: 'StringProperty',
    LangStringSet: 'StringProperty',
    MultiLanguageNameType: 'StringProperty',
    relativedelta: 'StringProperty',
    bool: 'BooleanProperty',
    int: 'IntegerProperty',
    float: 'FloatProperty',
    datetime.datetime: 'DateTimeProperty',
}

SUBMODEL_TYPES = [obj for name, obj in inspect.getmembers(submodel_types, inspect.isclass) if obj not in NODE_TYPES]
SUBMODEL_TYPES.sort(key=lambda cls: inspect.getsourcelines(cls)[1])

TYPES = RELATIONSHIP_TYPES + NODE_TYPES + tuple(SUBMODEL_TYPES)

def get_property_or_rel_type_def(param, annotation):
    optional = isOptional(annotation)
    iterable = isSimpleIterableType(annotation)

    annotation = removeOptional(annotation)
    annotation = resolveForwardRef(annotation)
    print(annotation)

    if isUnion(annotation):
        property_type = 'StringProperty'
    elif resolveBaseType(annotation) == type:
        property_type = 'StringProperty'
    elif issubtype(annotation, NODE_TYPES) or issubtype(annotation, RELATIONSHIP_TYPES):
        return get_relationship_type_def(param, annotation, optional, iterable)
    else:
        for type_, property_type in TYPE_NODE_MAP.items():
            if issubtype(annotation, type_):
                property_type = property_type
                break
        else:
            if isSimpleIterableType(annotation):
                if issubtype(annotation.__args__[0], NODE_TYPES) or issubtype(annotation.__args__[0],
                                                                              RELATIONSHIP_TYPES):
                    return get_relationship_type_def(param, annotation, optional, iterable)
                else:
                    property_type = 'ArrayProperty'

    if optional:
        return f"{property_type}()"
    else:
        return f"{property_type}()"#(required=True)"

    return annotation


def get_relationship_type_def(param, annotation, optional, iterable):
    if iterable:
        annotation = annotation.__args__[0]

    if issubtype(annotation, ModelReference):
        model = "ModelReferenceRel"
        try:
            target_type = annotation.__args__[0].__name__
        except AttributeError:
            target_type = "ReferableNode"
    elif issubtype(annotation, Reference):
        model = "ReferenceRel"
        try:
            target_type = annotation.__args__[0].__name__
        except AttributeError:
            target_type = "ANY"
    elif issubtype(annotation, NODE_TYPES):
        model = None
        target_type = annotation.__name__

    if optional and iterable:
        cardinality = "ZeroOrMore"
    elif optional:
        cardinality = "ZeroOrOne"
    elif iterable:
        cardinality = "OneOrMore"
    else:
        cardinality = "One"

    if model:
        return f"RelationshipTo('{target_type}Node', '{param}', model={model}, cardinality={cardinality})"
    else:
        return f"RelationshipTo('{target_type}Node', '{param}', cardinality={cardinality})"


def get_property_definitions(typ):
    paramsAndTypehints = getParamsAndTypehints4init(typ, withDefaults=False)
    property_defs = ""
    for param, typehint in paramsAndTypehints.items():
        param = param if param == "id_" else param.strip('_')
        if param in ATTRS_TO_IGNORE:
            continue
        property_type = get_property_or_rel_type_def(param, typehint)
        property_defs += f"\n    {param} = {property_type}"
    if not property_defs:
        property_defs = "\n    pass"
    return property_defs


def main():
    import_line = "from neomodel import StructuredNode, StringProperty, RelationshipTo, BooleanProperty, DateTimeProperty, ArrayProperty, StructuredRel, ZeroOrOne, ZeroOrMore, OneOrMore, One\n\n"
    generated_code = import_line + "\n\n"

    for typ in TYPES:
        if issubclass(typ, NODE_TYPES):
            # check if typ has a direct parent class in TYPES
            if typ.__bases__[0] in TYPES:
                parent = typ.__bases__[0].__name__ + "Node"
            else:
                parent = "StructuredNode"
            class_def = f"class {typ.__name__}Node({parent}):"
        elif issubclass(typ, RELATIONSHIP_TYPES):
            # check if typ has a direct parent class in TYPES
            if typ.__bases__[0] in TYPES:
                parent = typ.__bases__[0].__name__ + "Rel"
            else:
                parent = "StructuredRel"
            class_def = f"class {typ.__name__}Rel({parent}):"
        else:
            continue
        class_def += get_property_definitions(typ)
        generated_code += class_def + "\n\n"

    generated_code += """
class ANYNode(StructuredNode):
    name = StringProperty()
    """

    # Save the generated code to a file named 'generated_code.py'
    with open('aas_neomodel.py', 'w') as f:
        f.write(generated_code)


if __name__ == '__main__':
    main()
