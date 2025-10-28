from typing import Tuple

from aas_mapping.ast_nodes import *


def _convert_sme(root: str) -> Tuple[str, str]:
    if "$sme" not in root:
        raise ValueError(f"Root does not contain $sme: {root}")
    match_part: str = "(sm:Submodel)-[:submodelElements]->"
    last_root: str = ""
    depth = 0
    for part in root.split(".")[1:]:
        if "[" in part:
            for p in part.split("["):
                if "]" not in p:
                    if depth == 0:
                        match_part += f"(sme{depth}:SubmodelElement {{idShort: '{p}'}})"
                    else:
                        match_part += f"-[:value]->(sme{depth}:SubmodelElement {{idShort: '{p}'}})"
                elif len(p) > 1:
                    match_part += f"-[:value {{\'se_list_index\': {p[:-1]}}}]->(sme{depth}:SubmodelElement)"
                else:
                    match_part += f"-[:value]->(sme{depth}:SubmodelElement)"
        else:
            if depth == 0:
                match_part += f"(sme{depth}:SubmodelElement {{idShort: '{part}'}})"
            else:
                match_part += f"-[:value]->(sme{depth}:SubmodelElement {{idShort: '{part}'}})"
            last_root = f"sme{depth}"
        depth += 1
    if last_root != "":
        return match_part, last_root
    match_part += f"(sme: SubmodelElement)"
    last_root = "sme"
    return match_part, last_root


def _convert_root(root: str) -> Tuple[str, str]:
    match_part: str = ""
    last_root: str = ""
    match root:
        case "$aas":
            match_part += "(aas:AssetAdministrationShell)"
            last_root = "aas"
        case "$sm":
            match_part += "(sm:Submodel)"
            last_root = "sm"
        case "$cd":
            match_part += "(cd:ConceptDescription)"
            last_root = "cd"
        case _:
            match_part, last_root = _convert_sme(root)
    return match_part, last_root


def _convert_attribute_elements(attribute: str, last_root: str) -> Tuple[str, str, bool]:
    match_part: str = ""
    where_part: str = ""
    index = None
    isList = False
    for part in attribute.split("."):
        match part:
            case "id":
                where_part += f"{last_root}.id"
            case "idShort":
                where_part += f"{last_root}.idShort"
            case "assetInformation":
                # In specification, assetInformation can be chained
                match_part += "-[:assetInformation]->(assetInformation:AssetInformation)"
                last_root = "assetInformation"
            case "assetKind":
                where_part += f"{last_root}.assetKind"
            case "assetType":
                where_part += f"{last_root}.assetType"
            case "globalAssetId":
                where_part += f"{last_root}.globalAssetId"
            case "name":
                where_part += f"{last_root}.name"
            case "value":
                # If value is part of MultiLanguageProperty, we need to access value_type. We make sure last_root is multiLanguageProperty
                if last_root == "multiLanguageProperty":
                    where_part += f"{last_root}.value_text"
                    isList = True
                # If value is part of Reference, then value is part of keys.
                elif last_root == "reference":
                    if index is not None:
                        where_part += f"{last_root}.keys_value[{index}]"
                        index = None
                    else:
                        where_part += f"{last_root}.keys_value"
                        isList = True
                else:
                    where_part += f"{last_root}.value"
            case "externalSubjectId":
                match_part += "-[:externalSubjectId]->(externalSubjectId)"
                last_root = "externalSubjectId"
            case "type":
                # If type is part of Reference, then type is part of keys.
                if last_root == "reference":
                    if index is not None:
                        where_part += f"{last_root}.keys_type[{index}]"
                        index = None
                    else:
                        where_part += f"{last_root}.keys_type"
                        isList = True
                else:
                    where_part += f"{last_root}.type"
            case "submodels":
                match_part += "-[:submodels]->(submodels:Reference)"
                last_root = "submodels"
            case "semanticId":
                match_part += "-[:semanticId]->(semanticId)"
                last_root = "semanticId"
                if part.endswith("semanticId"):
                    where_part += f"{last_root}.keys_value[0]"
            case "valueType":
                where_part += f"{last_root}.valueType"
            case "language":
                where_part += f"{last_root}.value_language"
                isList = True
            case _ if part.startswith("keys"):
                last_root = "reference"
                if part.index("[") + 1 < len(part) - 1:
                    index = int(part[part.index("[") + 1: part.index("]")])
            case _ if part.startswith("specificAssetIds"):
                # specificAssetIds are relations. To access by index, we need order of them, which is not implemented yet.
                match_part += "-[:specificAssetIds]->(specificAssetIds)"
                last_root = "specificAssetIds"
            case _:
                raise ValueError(f"Unknown attribute element in field: {part}")

    return where_part, match_part, isList


def _convert_field(field: Field) -> Tuple[str, str, bool]:
    root, attribute = field.name.split("#")
    match_part, last_root = _convert_root(root)
    where_part, match_addition, isList = _convert_attribute_elements(attribute, last_root)
    match_part += match_addition
    return where_part, match_part, isList


def _convert_value(value: Value):
    match value:
        case Field():
            return _convert_field(value)
        case StrCast():
            raise NotImplementedError("StrCast not implemented yet")
        case NumCast():
            raise NotImplementedError("NumCast not implemented yet")
        case StringValue() | NumberValue() | BooleanValue():
            return value.value if isinstance(value.value, (int, float, bool)) else f"'{value.value}'", "", False
        case _:
            raise ValueError(f"Unsupported value type: {type(value)}")


def _convert_expression(exp: Expression):
    match exp:
        case BinaryExpression():
            left = _convert_value(exp.left)
            right = _convert_value(exp.right)
            operator = exp.get_operator()
            # If field returns a list, compare using IN operator
            if (left[2] or right[2]) and operator == "=":
                return f"{left[0]} IN {right[0]}", [left[1], right[1]]
            return f"{left[0]} {operator} {right[0]}", [left[1], right[1]]
        case Not():
            inner, fields = _convert_expression(exp.operand)
            return f"{exp.get_operator()} ({inner})", fields
        case And() | Or() | Match():
            inner = map(_convert_expression, exp.operands)
            inner = list(inner)
            operator = exp.get_operator()
            return f"{f' {operator} '.join(i[0] for i in inner)}", [f for i in inner for f in i[1]]
        case _:
            raise ValueError(f"Unsupported expression type: {type(exp)}")


def converter(ast: Condition):
    if isinstance(ast, Condition):
        where_field, match_field = _convert_expression(ast.expr)
        return f"MATCH {",".join(match_field)}\nWHERE {where_field}\nRETURN {match_field[0].split(':')[0][1:]}"
    else:
        raise ValueError(f"Expected Condition node, got {type(ast)}")
