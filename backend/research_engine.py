"""Free, bounded research mathematics built on Zentrix's safe symbolic parser.

This module performs local symbolic differential analysis with SymPy and numerical
classification with NumPy. It never evaluates arbitrary Python or calls an AI API.
"""
import math
import re

import numpy as np
import sympy as sp

import engine as E

_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,7}$")


def _variables(values):
    if not isinstance(values, (list, tuple)) or not 1 <= len(values) <= 5:
        raise ValueError("Choose between 1 and 5 variables.")
    names = list(values)
    if len(set(names)) != len(names) or any(not isinstance(v, str) or not _NAME.fullmatch(v) for v in names):
        raise ValueError("Variable names must be unique simple names such as x, y and z.")
    return names, [sp.Symbol(name, real=True) for name in names]


def _point(names, point):
    if not isinstance(point, dict) or set(point) != set(names):
        raise ValueError("Provide one numeric point value for every selected variable.")
    values = {}
    for name in names:
        value = point[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or abs(float(value)) > 1e6:
            raise ValueError("Point coordinates must be finite numbers between -1,000,000 and 1,000,000.")
        values[name] = float(value)
    return values


def _numeric(expression, substitutions, precision):
    value = sp.N(expression.subs(substitutions), precision)
    if value.free_symbols or value.is_finite is False:
        raise ValueError("The expression is not finite and numeric at the supplied point.")
    return sp.sstr(value)


def _real_matrix(matrix, substitutions):
    evaluated = matrix.subs(substitutions).evalf(30)
    values = np.array(evaluated.tolist(), dtype=np.complex128)
    if not np.isfinite(values.real).all() or not np.isfinite(values.imag).all() or np.max(np.abs(values.imag), initial=0.0) > 1e-9:
        raise ValueError("The derivatives are not finite real values at the supplied point.")
    return values.real.astype(float)


def analyze_scalar_field(expression, variables, point, precision=30):
    """Return gradient, Hessian and local second-order diagnostics for f:R^n->R."""
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 1200:
        raise ValueError("Enter a mathematical expression of at most 1,200 characters.")
    if isinstance(precision, bool) or not isinstance(precision, int) or not 15 <= precision <= 80:
        raise ValueError("Precision must be an integer between 15 and 80 digits.")
    names, symbols = _variables(variables)
    coordinates = _point(names, point)
    substitutions = {symbol: sp.Float(coordinates[name], precision) for name, symbol in zip(names, symbols)}
    expr = E.P(expression, dict(zip(names, symbols)))
    if not isinstance(expr, sp.Expr) or expr.free_symbols - set(symbols):
        raise ValueError("Use one scalar expression containing only the selected variables.")
    if expr.is_real is False:
        raise ValueError("The research workbench currently requires a real-valued scalar function.")

    gradient = sp.Matrix([sp.diff(expr, symbol) for symbol in symbols])
    hessian = sp.hessian(expr, symbols)
    gradient_values = _real_matrix(gradient, substitutions).reshape(-1)
    hessian_values = _real_matrix(hessian, substitutions)
    eigenvalues = np.linalg.eigvalsh((hessian_values + hessian_values.T) / 2.0)
    tolerance = 10 ** (-min(precision // 2, 10))
    stationary = bool(np.max(np.abs(gradient_values), initial=0.0) <= tolerance)
    if not stationary:
        classification = "not_stationary"
    elif np.all(eigenvalues > tolerance):
        classification = "strict_local_minimum"
    elif np.all(eigenvalues < -tolerance):
        classification = "strict_local_maximum"
    elif np.any(eigenvalues > tolerance) and np.any(eigenvalues < -tolerance):
        classification = "saddle_point"
    else:
        classification = "degenerate_or_inconclusive"

    offsets = sp.symbols(" ".join("h_" + name for name in names), real=True)
    if len(names) == 1:
        offsets = (offsets,)
    offset_vector = sp.Matrix(offsets)
    f0 = expr.subs(substitutions)
    g0 = gradient.subs(substitutions)
    h0 = hessian.subs(substitutions)
    quadratic = sp.expand(f0 + (g0.T * offset_vector)[0] + (offset_vector.T * h0 * offset_vector)[0] / 2)
    return {
        "expression": sp.sstr(expr),
        "variables": names,
        "point": coordinates,
        "value_at_point": _numeric(expr, substitutions, precision),
        "gradient": [sp.sstr(value) for value in gradient],
        "gradient_latex": sp.latex(gradient),
        "gradient_at_point": [sp.N(value, precision).__str__() for value in gradient.subs(substitutions)],
        "hessian": [[sp.sstr(hessian[i, j]) for j in range(len(names))] for i in range(len(names))],
        "hessian_latex": sp.latex(hessian),
        "hessian_at_point": hessian_values.tolist(),
        "hessian_eigenvalues": [float(value) for value in eigenvalues],
        "hessian_determinant": sp.sstr(sp.factor(hessian.det())),
        "stationary": stationary,
        "classification": classification,
        "quadratic_taylor": sp.sstr(quadratic),
        "quadratic_taylor_latex": sp.latex(quadratic),
        "precision_digits": precision,
        "notes": [
            "The gradient and Hessian are exact symbolic derivatives.",
            "Hessian eigenvalues are numerical and classify only the local quadratic test at the supplied point.",
            "A degenerate Hessian is inconclusive; higher-order analysis or domain constraints may be needed.",
            "A local classification is not a global optimality proof."
        ]
    }


def analyze_vector_field(components, variables, point, precision=30):
    """Return Jacobian, divergence and (in 3D) curl for a square vector field."""
    names, symbols = _variables(variables)
    if not isinstance(components, (list, tuple)) or len(components) != len(names):
        raise ValueError("Provide exactly one vector-field component per variable.")
    if any(not isinstance(item, str) or not item.strip() or len(item) > 800 for item in components):
        raise ValueError("Each vector component must be non-empty text of at most 800 characters.")
    if isinstance(precision, bool) or not isinstance(precision, int) or not 15 <= precision <= 80:
        raise ValueError("Precision must be an integer between 15 and 80 digits.")
    coordinates = _point(names, point)
    substitutions = {symbol: sp.Float(coordinates[name], precision) for name, symbol in zip(names, symbols)}
    expressions = [E.P(item, dict(zip(names, symbols))) for item in components]
    if any(not isinstance(item, sp.Expr) or item.free_symbols - set(symbols) or item.is_real is False for item in expressions):
        raise ValueError("Use real scalar expressions containing only the selected variables.")
    field = sp.Matrix(expressions)
    jacobian = field.jacobian(symbols)
    jacobian_values = _real_matrix(jacobian, substitutions)
    divergence = sp.trace(jacobian)
    curl = None
    if len(names) == 3:
        curl_vector = sp.Matrix([
            sp.diff(expressions[2], symbols[1]) - sp.diff(expressions[1], symbols[2]),
            sp.diff(expressions[0], symbols[2]) - sp.diff(expressions[2], symbols[0]),
            sp.diff(expressions[1], symbols[0]) - sp.diff(expressions[0], symbols[1])
        ])
        curl = [sp.sstr(value) for value in curl_vector]
    return {
        "components": [sp.sstr(value) for value in expressions],
        "variables": names,
        "point": coordinates,
        "jacobian": [[sp.sstr(jacobian[i, j]) for j in range(len(names))] for i in range(len(names))],
        "jacobian_latex": sp.latex(jacobian),
        "jacobian_at_point": jacobian_values.tolist(),
        "divergence": sp.sstr(divergence),
        "divergence_at_point": _numeric(divergence, substitutions, precision),
        "curl": curl,
        "curl_note": "Curl is returned for three-dimensional vector fields only." if len(names) != 3 else "Curl uses the standard right-handed Cartesian convention.",
        "locally_conservative_test": bool(all(sp.simplify(jacobian[i, j] - jacobian[j, i]) == 0 for i in range(len(names)) for j in range(i + 1, len(names)))),
        "precision_digits": precision,
        "notes": [
            "The Jacobian and divergence are exact symbolic derivatives.",
            "The locally conservative test checks symmetry of the Jacobian; global conservativity also depends on the field's domain."
        ]
    }
