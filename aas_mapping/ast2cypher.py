from typing import Tuple

from aas_mapping.ast_nodes import *


def _convert_field(field: Field) -> Tuple[str, str]:
    root, attribute = field.name.split("#")
    match_part = ""
    where_part = ""
    last_root = None
    index = []
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
        case "$sme":
            match_part += "(sm:Submodel)-[:submodelElements]->(sme:SubmodelElement)"
            last_root = "sme"
        case _:
            if "$sme" in root:
                match_part += "(sm:Submodel)-[:submodelElements]->(sme:SubmodelElement)"
                last_root = "sme"
            else:
                raise ValueError(f"Unknown root in field: {field.name}")
    for part in attribute.split("."):
        match part:
            case "description":
                where_part += f"{last_root}.description_"
            case "assetInformation":
                match_part += f"-[:assetInformation]->(assetInformation:AssetInformation)"
                last_root = "assetInformation"
            case "semanticId":
                match_part += f"-[:semanticId]->(semanticId:Reference)"
                last_root = "semanticId"
            case "derivedFrom":
                match_part += f"-[:derivedFrom]->(derivedFrom:Reference)"
                last_root = "derivedFrom"
            case "administration":
                match_part += f"-[:administration]->(administration)"
                last_root = "administration"
            case "qualifiers":
                match_part += f"-[:qualifiers]->(qualifiers:Qualifier)"
                last_root = "qualifiers"
            case _:
                if "keys" in part:
                    where_part += f"{last_root}.keys_"
                    index.append(part[5:-1])
                if "specificAssetIds" in part:
                    match_part += f"-[:specificAssetIds]->(specificAssetIds)"
                    last_root = "specificAssetIds"
                if where_part == "":
                    where_part += f"{last_root}.{part}"
                else:
                    where_part += f".{part}"
    return where_part, match_part

def _convert_value(value: Value):
    match value:
        case Field():
            return _convert_field(value)
        case StrCast():
            raise NotImplementedError("StrCast not implemented yet")
        case NumCast():
            raise NotImplementedError("NumCast not implemented yet")
        case StringValue() | NumberValue() | BooleanValue():
            return value.value if isinstance(value.value, (int, float)) else f"'{value.value}'", ""
        case _:
            raise ValueError(f"Unsupported value type: {type(value)}")

def _convert_expression(exp: Expression):
    match exp:
        case BinaryExpression():
            left = _convert_value(exp.left)
            right = _convert_value(exp.right)
            operator = exp.get_operator()
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
        match_field = [x for x in match_field if not any((x != y and x in y) for y in match_field)]
        return f"MATCH {",".join(match_field)}\nWHERE {where_field}\nRETURN {match_field[0].split(':')[0][1:]}"
    else:
        raise ValueError(f"Expected Condition node, got {type(ast)}")