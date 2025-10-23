from __future__ import annotations
from dataclasses import dataclass
from typing import List
from abc import ABC, abstractmethod


class Node(ABC):
    pass


class Value(Node, ABC):
    pass


class Expression(Node, ABC):
    pass


@dataclass
class Field(Value):
    name: str

    def __repr__(self): return f'Field("{self.name}")'


@dataclass
class StringValue(Value):
    value: str

    def __repr__(self): return f'StringValue("{self.value}")'


@dataclass
class NumberValue(Value):
    value: float

    def __repr__(self): return f'NumberValue({self.value})'


@dataclass
class BooleanValue(Value):
    value: bool

    def __repr__(self): return f'BooleanValue({self.value})'


@dataclass
class StrCast(Value):
    inner: Value

    def __repr__(self): return f"Str({self.inner})"


@dataclass
class NumCast(Value):
    inner: Value

    def __repr__(self): return f"Num({self.inner})"


@dataclass
class BinaryExpression(Expression):
    left: Value
    right: Value

    @staticmethod
    @abstractmethod
    def get_operator() -> str:
        pass


@dataclass
class Eq(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "="

    def __repr__(self): return f"Eq({self.left}, {self.right})"


@dataclass
class Ne(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "<>"

    def __repr__(self): return f"Ne({self.left}, {self.right})"


@dataclass
class Gt(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return ">"

    def __repr__(self): return f"Gt({self.left}, {self.right})"


@dataclass
class Ge(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return ">="

    def __repr__(self): return f"Ge({self.left}, {self.right})"


@dataclass
class Lt(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "<"

    def __repr__(self): return f"Lt({self.left}, {self.right})"


@dataclass
class Le(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "<="

    def __repr__(self): return f"Le({self.left}, {self.right})"


@dataclass
class Contains(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "CONTAINS"

    def __repr__(self): return f"Contains({self.left}, {self.right})"


@dataclass
class StartsWith(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "STARTS WITH"

    def __repr__(self): return f"StartsWith({self.left}, {self.right})"


@dataclass
class EndsWith(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "ENDS WITH"

    def __repr__(self): return f"EndsWith({self.left}, {self.right})"


@dataclass
class Regex(BinaryExpression):
    @staticmethod
    def get_operator() -> str:
        return "=~"

    def __repr__(self): return f"Regex({self.left}, {self.right})"


@dataclass
class Match(Expression):
    operands: List[Expression]

    @staticmethod
    def get_operator() -> str:
        return "AND"

    def __repr__(self): return f"Match([{', '.join(map(str, self.operands))}])"


@dataclass
class And(Expression):
    operands: List[Expression]

    @staticmethod
    def get_operator() -> str:
        return "AND"

    def __repr__(self): return f"And([{', '.join(map(str, self.operands))}])"


@dataclass
class Or(Expression):
    operands: List[Expression]

    @staticmethod
    def get_operator() -> str:
        return "OR"

    def __repr__(self): return f"Or([{', '.join(map(str, self.operands))}])"


@dataclass
class Not(Expression):
    operand: Expression

    @staticmethod
    def get_operator() -> str:
        return "NOT"

    def __repr__(self): return f"Not({self.operand})"


@dataclass
class Condition(Node):
    expr: Expression

    def __repr__(self): return f"Condition({self.expr})"
