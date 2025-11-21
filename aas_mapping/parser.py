from aas_mapping.ast_nodes import *

def parse_value(data: dict) -> Value:
    """
    Parse AASQL value dictionary into an AST Value node.

    Args:
        data (dict): The AASQL value represented as a dictionary.
    Returns:
        Value: The AST node representing the value.
    Raises:
        ValueError: If the value type is unknown.
    """
    if "$field" in data: return Field(data["$field"])
    if "$strVal" in data: return StringValue(data["$strVal"])
    if "$numVal" in data: return NumberValue(data["$numVal"])
    if "$boolean" in data: return BooleanValue(data["$boolean"])
    if "$strCast" in data: return StrCast(parse_value(data["$strCast"]))
    if "$numCast" in data: return NumCast(parse_value(data["$numCast"]))
    if "$hexCast" in data: return HexCast(parse_value(data["$hexCast"]))
    if "$boolCast" in data: return BoolCast(parse_value(data["$boolCast"]))
    if "$dateTimeCast" in data: return DateTimeCast(parse_value(data["$dateTimeCast"]))
    if "$timeCast" in data: return TimeCast(parse_value(data["$timeCast"]))
    raise ValueError(f"Unknown value type: {data}")

def parse_expression(expr: dict) -> Expression:
    """
    Parse AASQL expression dictionary into an AST Expression node.

    Args:
        expr (dict): The AASQL expression represented as a dictionary.
    Returns:
        Expression: The AST node representing the expression.
    Raises:
        ValueError: If the expression contains unsupported operations.
    """
    if "$match" in expr: return Match([parse_expression(e) for e in expr["$match"]])
    if "$and" in expr: return And([parse_expression(e) for e in expr["$and"]])
    if "$or" in expr: return Or([parse_expression(e) for e in expr["$or"]])
    if "$not" in expr: return Not(parse_expression(expr["$not"]))

    for op, cls in [("$eq", Eq), ("$ne", Ne), ("$gt", Gt), ("$ge", Ge),
                    ("$lt", Lt), ("$le", Le), ("$contains", Contains),
                    ("$starts-with", StartsWith), ("$ends-with", EndsWith),
                    ("$regex", Regex)]:
        if op in expr:
            a, b = expr[op]
            return cls(parse_value(a), parse_value(b))

    raise ValueError(f"Unsupported expression: {expr}")

def parse_query(query: dict) -> Condition:
    """
    Parse AASQL query dictionary into an AST Condition node.

    Args:
        query (dict): The AASQL query represented as a dictionary.
    Returns:
        Condition: The root AST node representing the query condition.
    """
    expr = parse_expression(query["$condition"])
    return Condition(expr)