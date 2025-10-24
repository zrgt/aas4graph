from typing import Dict, Tuple, List
from aas_mapping.ast_nodes import *

class AASToCypherConverter:
    def __init__(self):
        # Maps node paths to aliases to avoid duplicate MATCHes
        self.alias_map: Dict[str, str] = {}
        self.alias_counter = 0
        self.match_clauses: List[str] = []
        self.where_clauses: List[str] = []

    def get_alias(self, path: str) -> str:
        """Return an alias for a node path, creating a new one if needed."""
        if path not in self.alias_map:
            self.alias_counter += 1
            alias = f"n{self.alias_counter}"
            self.alias_map[path] = alias
        return self.alias_map[path]

    def parse_field(self, field: Field) -> Tuple[str, str]:
        """
        Converts a Field into a (alias, property) pair.
        e.g. $aas#assetInformation.assetType -> (assetInformation, assetType)
        """
        path = field.name  # e.g., "$aas#assetInformation.assetType"
        if not path.startswith("$"):
            raise ValueError(f"Unexpected field format: {path}")

        path = path[1:]  # remove leading $
        root, *props = path.split("#")
        if not props:
            raise ValueError(f"No property in field: {field}")

        prop_path = props[0].split(".")  # e.g., ["assetInformation", "assetType"]
        current_node = root
        last_prop = prop_path[-1]

        for rel in prop_path[:-1]:
            # Build MATCH clauses for relationships
            parent_alias = self.get_alias(current_node)
            child_alias = self.get_alias(f"{current_node}.{rel}")
            match_clause = f"MATCH ({parent_alias}:{self.camelize(current_node)})-[:{rel}]->({child_alias})"
            if match_clause not in self.match_clauses:
                self.match_clauses.append(match_clause)
            current_node = f"{current_node}.{rel}"

        alias = self.get_alias(current_node)
        return alias, last_prop

    @staticmethod
    def camelize(name: str) -> str:
        """Convert a name like 'aas' to 'AssetAdministrationShell' if needed. Simplified here."""
        # You could extend this with actual type mapping if needed
        if name.lower() == "aas":
            return "AssetAdministrationShell"
        return name.capitalize()

    def parse_expression(self, expr: Expression) -> str:
        """Recursively parse an Expression into a Cypher WHERE string."""
        if isinstance(expr, BinaryExpression):
            left_alias, left_prop = self.parse_value(expr.left)
            right_alias, right_prop = self.parse_value(expr.right)
            operator = self.get_operator(expr)
            return f"{left_alias}.{left_prop} {operator} {right_alias}.{right_prop}"

        elif isinstance(expr, And):
            return "(" + " AND ".join(self.parse_expression(op) for op in expr.operands) + ")"

        elif isinstance(expr, Or):
            return "(" + " OR ".join(self.parse_expression(op) for op in expr.operands) + ")"

        elif isinstance(expr, Not):
            return f"NOT ({self.parse_expression(expr.operand)})"

        elif isinstance(expr, Match):
            # Treat Match like AND of operands
            return "(" + " AND ".join(self.parse_expression(op) for op in expr.operands) + ")"

        else:
            raise ValueError(f"Unsupported expression type: {expr}")

    def parse_value(self, val: Value) -> Tuple[str, str]:
        """Return (alias, property) for a value."""
        if isinstance(val, Field):
            return self.parse_field(val)
        elif isinstance(val, StringValue):
            return f"'{val.value}'", ""
        elif isinstance(val, NumberValue):
            return str(val.value), ""
        elif isinstance(val, BooleanValue):
            return str(val.value).lower(), ""
        elif isinstance(val, (StrCast, NumCast)):
            # Just recurse into inner
            return self.parse_value(val.inner)
        else:
            raise ValueError(f"Unsupported value type: {val}")

    @staticmethod
    def get_operator(expr: BinaryExpression) -> str:
        """Map AST binary expression to Cypher operator."""
        if isinstance(expr, Eq): return "="
        if isinstance(expr, Ne): return "<>"
        if isinstance(expr, Gt): return ">"
        if isinstance(expr, Ge): return ">="
        if isinstance(expr, Lt): return "<"
        if isinstance(expr, Le): return "<="
        if isinstance(expr, Contains): return "CONTAINS"
        if isinstance(expr, StartsWith): return "STARTS WITH"
        if isinstance(expr, EndsWith): return "ENDS WITH"
        if isinstance(expr, Regex): return "=~"
        raise ValueError(f"Unsupported binary expression: {expr}")

    def convert(self, condition: Condition) -> str:
        """Convert a Condition AST node into a full Cypher query string."""
        self.match_clauses = []
        self.alias_map = {}
        self.alias_counter = 0

        where_clause = self.parse_expression(condition.expr)
        query = "\n".join(self.match_clauses) + f"\nWHERE {where_clause}\nRETURN {', '.join(self.alias_map.values())}"
        return query