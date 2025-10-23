from aas_mapping.ast_nodes import *

def parse_value(data: dict) -> Value:
    if "$field" in data: return Field(data["$field"])
    if "$strVal" in data: return StringValue(data["$strVal"])
    if "$numVal" in data: return NumberValue(data["$numVal"])
    if "$boolean" in data: return BooleanValue(data["$boolean"])
    if "$strCast" in data: return StrCast(parse_value(data["$strCast"]))
    if "$numCast" in data: return NumCast(parse_value(data["$numCast"]))
    raise ValueError(f"Unknown value type: {data}")

def parse_expression(expr: dict) -> Expression:
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
    expr = parse_expression(query["$condition"])
    return Condition(expr)
