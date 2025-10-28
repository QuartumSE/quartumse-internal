"""Utilities for handling observable specifications in experiment metadata."""

from __future__ import annotations

import ast
import math
import re
from collections import OrderedDict
from typing import Iterable, List, Mapping, Tuple

from quartumse.shadows.core import Observable

__all__ = [
    "expand_mermin_to_pauli",
    "metadata_defined_observables",
]


_PAULI_PATTERN = re.compile(r"(?<![A-Za-z0-9_])([IXYZ]+)(?![A-Za-z0-9_])")


class _PauliExpression:
    """Intermediate representation for Pauli linear combinations."""

    def __init__(self, terms: Mapping[str, float] | None = None):
        self._terms: "OrderedDict[str, float]" = OrderedDict()
        if terms:
            for pauli, coefficient in terms.items():
                self._add_term(pauli, coefficient)

    def copy(self) -> "_PauliExpression":
        return _PauliExpression(self._terms)

    @staticmethod
    def _normalise_pauli(pauli: str) -> str:
        cleaned = "".join(ch for ch in pauli.upper() if not ch.isspace())
        if not cleaned:
            raise ValueError("Pauli string cannot be empty")
        if any(ch not in "IXYZ" for ch in cleaned):
            raise ValueError(f"Invalid character in Pauli string '{pauli}'")
        return cleaned

    def _add_term(self, pauli: str, coefficient: float) -> None:
        if abs(float(coefficient)) < 1e-12:
            return
        normalised = self._normalise_pauli(pauli)
        if normalised in self._terms:
            updated = self._terms[normalised] + float(coefficient)
            if abs(updated) < 1e-12:
                del self._terms[normalised]
            else:
                self._terms[normalised] = updated
        else:
            self._terms[normalised] = float(coefficient)

    def __add__(self, other: "_PauliExpression") -> "_PauliExpression":
        if not isinstance(other, _PauliExpression):
            return NotImplemented
        result = self.copy()
        for pauli, coefficient in other._terms.items():
            result._add_term(pauli, coefficient)
        return result

    def __radd__(self, other: "_PauliExpression") -> "_PauliExpression":
        return self.__add__(other)

    def __sub__(self, other: "_PauliExpression") -> "_PauliExpression":
        if not isinstance(other, _PauliExpression):
            return NotImplemented
        return self + (-other)

    def __neg__(self) -> "_PauliExpression":
        result = _PauliExpression()
        for pauli, coefficient in self._terms.items():
            result._add_term(pauli, -coefficient)
        return result

    def __pos__(self) -> "_PauliExpression":
        return self.copy()

    def __mul__(self, scalar: float) -> "_PauliExpression":
        if isinstance(scalar, _PauliExpression):
            raise TypeError("Pauli expressions cannot be multiplied together")
        result = _PauliExpression()
        for pauli, coefficient in self._terms.items():
            result._add_term(pauli, coefficient * float(scalar))
        return result

    def __rmul__(self, scalar: float) -> "_PauliExpression":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "_PauliExpression":
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide Pauli expression by zero")
        return self * (1.0 / float(scalar))

    @classmethod
    def from_pauli(cls, pauli: str) -> "_PauliExpression":
        return cls({cls._normalise_pauli(pauli): 1.0})

    def items(self) -> Iterable[Tuple[str, float]]:
        return tuple(self._terms.items())


_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)
_ALLOWED_CALLS = {"_pauli", "sqrt"}
_ALLOWED_NAMES = {"sqrt"}


def _validate_ast(node: ast.AST) -> None:
    if isinstance(node, ast.Expression):
        _validate_ast(node.body)
        return

    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise ValueError("Unsupported operator in expression")
        _validate_ast(node.left)
        _validate_ast(node.right)
        return

    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARY):
            raise ValueError("Unsupported unary operator in expression")
        _validate_ast(node.operand)
        return

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_CALLS:
            for argument in node.args:
                _validate_ast(argument)
            for keyword in node.keywords:
                _validate_ast(keyword.value)
            return
        raise ValueError("Unsupported function in expression")

    if isinstance(node, ast.Name):
        if node.id not in _ALLOWED_NAMES:
            raise ValueError("Unknown identifier in expression")
        return

    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float, str)):
            raise ValueError("Unsupported literal in expression")
        return

    raise ValueError("Invalid syntax in expression")


def _normalise_expression(expr: str) -> str:
    trimmed = expr.strip()
    lowered = trimmed.lower()
    if lowered.startswith("mermin:"):
        return trimmed.split(":", 1)[1].strip()
    if lowered.startswith("mermin(") and trimmed.endswith(")"):
        inner = trimmed[trimmed.find("(") + 1 : -1]
        return inner.strip()
    if lowered.startswith("mermin "):
        return trimmed.split(None, 1)[1].strip()
    return trimmed


def expand_mermin_to_pauli(expr: str) -> List[Tuple[str, float]]:
    """Expand a Mermin-style expression into weighted Pauli strings.

    The expression supports ``+``/``-`` combinations of Pauli strings with optional
    numeric coefficients, e.g. ``"mermin: XX - YY"`` or
    ``"0.5 * (XXX - XYY - YXY - YYX)"``.
    """

    if not isinstance(expr, str) or not expr.strip():
        raise ValueError("Expression must be a non-empty string")

    cleaned = _normalise_expression(expr)

    def _replace(match: re.Match[str]) -> str:
        pauli = match.group(1)
        return f"_pauli('{pauli}')"

    substituted = _PAULI_PATTERN.sub(_replace, cleaned)
    tree = ast.parse(substituted, mode="eval")
    _validate_ast(tree)

    environment = {
        "_pauli": _PauliExpression.from_pauli,
        "sqrt": math.sqrt,
    }

    result = eval(compile(tree, filename="<mermin>", mode="eval"), {"__builtins__": {}}, environment)
    if not isinstance(result, _PauliExpression):
        raise ValueError("Expression did not evaluate to Pauli terms")

    terms = list(result.items())
    if not terms:
        raise ValueError("Expression contains no Pauli terms")
    return terms


_EXPRESSION_KEYS = (
    "mermin",
    "mermin_expression",
    "mermin_expr",
    "expression",
    "expr",
    "definition",
    "operator",
)


def _extract_mermin_expressions(payload: object) -> Iterable[str]:
    expressions: List[str] = []

    def _maybe_add(candidate: object) -> None:
        if isinstance(candidate, str) and "mermin" in candidate.lower():
            expressions.append(candidate)

    if isinstance(payload, str):
        _maybe_add(payload)
    elif isinstance(payload, Mapping):
        type_hint = str(payload.get("type", "")).lower()
        for key in _EXPRESSION_KEYS:
            value = payload.get(key)
            if isinstance(value, str):
                if key != "expression" and key != "expr":
                    _maybe_add(value)
                elif "mermin" in type_hint or "mermin" in value.lower():
                    expressions.append(value)

        extra = payload.get("expressions")
        if isinstance(extra, Iterable) and not isinstance(extra, (str, bytes)):
            for entry in extra:
                _maybe_add(entry)

    return expressions


def metadata_defined_observables(metadata) -> List[Observable]:
    """Return additional observables derived from metadata definitions."""

    ground_truth = getattr(metadata, "ground_truth", None)
    if not isinstance(ground_truth, Mapping):
        return []

    candidate_maps: List[Mapping[str, object]] = [ground_truth]
    observables_section = ground_truth.get("observables")
    if isinstance(observables_section, Mapping):
        candidate_maps.append(observables_section)

    result: List[Observable] = []
    for mapping in candidate_maps:
        for payload in mapping.values():
            for expr in _extract_mermin_expressions(payload):
                try:
                    for pauli, coefficient in expand_mermin_to_pauli(expr):
                        result.append(Observable(pauli, coefficient=coefficient))
                except ValueError:
                    continue

    return result

