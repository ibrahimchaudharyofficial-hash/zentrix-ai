"""Zentrix AI engine. SymPy computes; NumPy/SciPy/mpmath verify independently; an optional LLM only rewrites wording into a command."""
import ast, os, re, json, math, random, itertools, urllib.request
import numpy as np, mpmath as mp, sympy as sp
from scipy.integrate import quad

x, y, z, t = sp.symbols('x y z t')
LOC = dict(
    x=x, y=y, z=z, t=t, e=sp.E, E=sp.E, pi=sp.pi, I=sp.I, i=sp.I, j=sp.I, oo=sp.oo,
    infinity=sp.oo, ln=sp.log, abs=sp.Abs, sqrt=sp.sqrt, sin=sp.sin, cos=sp.cos,
    tan=sp.tan, asin=sp.asin, acos=sp.acos, atan=sp.atan, arcsin=sp.asin,
    arccos=sp.acos, arctan=sp.atan, sinh=sp.sinh, cosh=sp.cosh, tanh=sp.tanh,
    exp=sp.exp, log=sp.log, floor=sp.floor, ceiling=sp.ceiling,
    Derivative=sp.Derivative, Integral=sp.Integral,
)
L = sp.latex

_ALLOWED_BINOPS = {ast.Add: lambda a,b: a+b, ast.Sub: lambda a,b: a-b,
                   ast.Mult: lambda a,b: a*b, ast.Div: lambda a,b: a/b,
                   ast.Pow: lambda a,b: a**b, ast.Mod: lambda a,b: sp.Mod(a,b)}
_ALLOWED_UNARY = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}
_ALLOWED_FUNCTIONS = {k: v for k, v in LOC.items() if callable(v)}

def _safe_ast(node, names, depth=0):
    """Evaluate a deliberately small mathematical AST; never execute Python code."""
    if depth > 40:
        raise ValueError('Expression is nested too deeply.')
    if isinstance(node, ast.Expression):
        return _safe_ast(node.body, names, depth + 1)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return sp.Integer(node.value) if isinstance(node.value, int) else sp.Float(node.value)
    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        if re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}', node.id):
            return sp.Symbol(node.id)
        raise ValueError(f'Unsupported name: {node.id}')
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left, right = _safe_ast(node.left, names, depth + 1), _safe_ast(node.right, names, depth + 1)
        if isinstance(node.op, ast.Pow) and getattr(right, 'is_number', False):
            if getattr(right, 'is_Integer', False) and abs(int(right)) > 1000:
                raise ValueError('Exponent magnitude is limited to 1000.')
            if getattr(right, 'is_Float', False) and abs(float(right)) > 1000:
                raise ValueError('Exponent magnitude is limited to 1000.')
        return _ALLOWED_BINOPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_safe_ast(node.operand, names, depth + 1))
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_safe_ast(item, names, depth + 1) for item in node.elts]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        fn = names.get(node.func.id)
        if fn is None or not callable(fn):
            raise ValueError(f'Function is not allowed: {node.func.id}')
        if len(node.args) > 4:
            raise ValueError('Too many function arguments.')
        return fn(*[_safe_ast(arg, names, depth + 1) for arg in node.args])
    raise ValueError(f'Unsupported mathematical syntax: {type(node).__name__}')

def P(s, loc=None):
    """Parse supported mathematics with a whitelist AST evaluator (no eval/parse_expr)."""
    if not isinstance(s, str):
        raise ValueError('Mathematical expressions must be text.')
    if len(s) > 1000:
        raise ValueError('Expression is too long (maximum 1000 characters).')
    s = re.sub(r'√\s*(\([^)]*\)|[A-Za-z0-9_.]+)', r'sqrt(\1)', s).strip()
    for a, b in (('×', '*'), ('÷', '/'), ('−', '-'), ('π', 'pi'), ('²', '**2'), ('³', '**3'), ('^', '**')):
        s = s.replace(a, b)
    # Preserve scientific notation while supporting common implicit products such as 2x and 3(x+1).
    s = re.sub(r'(?<=\d)(?=(?:[A-DF-Za-df-z_(]))', '*', s)
    try:
        tree = ast.parse(s, mode='eval')
    except SyntaxError as exc:
        raise ValueError('Invalid mathematical expression.') from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > 256:
        raise ValueError('Expression is too complex (maximum 256 syntax nodes).')
    names = {**LOC, **(loc or {})}
    return _safe_ast(tree, names)

class Res:
    def __init__(s, q):
        s.q, s.topic, s.formula, s.steps, s.ans, s.text, s.approx, s.exact, s.checks, s.warn = q, '', '', [], '', '', '', True, [], []
        s.diagram = None
    def step(s, title, tex, note=''): s.steps.append(dict(title=title, latex=tex, note=note))
    def check(s, name, ok, detail=''): s.checks.append(dict(name=name, passed=(bool(ok) if ok is not None else None), detail=str(detail) if detail is not None else ''))
    def done(s, e, text=None):
        s.ans = e if isinstance(e, str) else L(e); s.text = text or str(e)
        if not isinstance(e, str) and getattr(e, 'is_number', False) and e.is_real and not e.is_Integer: s.approx = str(sp.N(e, 12))
    def out(s):
        outcomes = [c['passed'] for c in s.checks]
        v = bool(outcomes) and all(value is True for value in outcomes)
        partial = any(value is True for value in outcomes) and any(value is None for value in outcomes) and not any(value is False for value in outcomes)
        names = ' '.join(c['name'].lower() for c in s.checks)
        if any(c['passed'] is False for c in s.checks): level = 'failed'
        elif partial: level = 'partially-verified'
        elif not s.checks or not any(value is True for value in outcomes): level = 'unverified'
        elif 'symbolic' in names or 'difference simplifies' in names: level = 'symbolic'
        elif 'numeric' in names or 'mpmath' in names or 're-evaluation' in names: level = 'numerical'
        else: level = 'rule-based'
        return dict(question=s.q, topic=s.topic, formula=s.formula, steps=s.steps, answer=s.ans, answer_text=s.text,
                    approx=s.approx, exact=s.exact, checks=s.checks, warnings=s.warn, verified=v,
                    verification_status=level, verification_level=level, diagram=s.diagram)

def same(a, b):
    """Numerically cross-check two expressions at varied deterministic points.

    This is a diagnostic check, not a proof: symbolic equality is still the
    authoritative route when available. Sampling includes negative and
    fractional inputs to catch errors hidden by positive-only test points.
    """
    fs = sorted(a.free_symbols | b.free_symbols, key=str)
    if not fs:
        try:
            with mp.workdps(40):
                u, v = mp.mpmathify(str(sp.N(a, 40))), mp.mpmathify(str(sp.N(b, 40)))
                return bool(mp.isfinite(u) and mp.isfinite(v) and abs(u-v) <= mp.mpf('1e-12') * (1 + abs(u)))
        except Exception:
            return False
    try:
        fa, fb = sp.lambdify(fs, a, 'mpmath'), sp.lambdify(fs, b, 'mpmath')
    except Exception:
        return False
    rng = random.Random(7)
    base = [mp.mpf('-3.7'), mp.mpf('-2.25'), mp.mpf('-1.1'), mp.mpf('-0.4'),
            mp.mpf('0.35'), mp.mpf('0.9'), mp.mpf('1.75'), mp.mpf('3.2')]
    passed = 0
    checked = 0
    with mp.workdps(40):
        for index in range(24):
            point = base[index % len(base)] if index < len(base) else mp.mpf(str(rng.uniform(-4.5, 4.5)))
            values = [point if j == 0 else mp.mpf(str(rng.uniform(-3.5, 3.5))) for j in range(len(fs))]
            try:
                u, v = fa(*values), fb(*values)
                if not (mp.isfinite(u) and mp.isfinite(v)):
                    continue
                checked += 1
                # Symmetric relative tolerance avoids bias toward the left expression.
                scale = max(mp.mpf(1), abs(u), abs(v))
                tolerance = mp.mpf('1e-30') * scale
                if abs(u-v) <= tolerance:
                    passed += 1
                else:
                    return False
            except Exception:
                continue
            if checked >= 8:
                break
    return checked >= 5 and passed == checked

def residual(lhs, rhs, v, s):
    """Check a proposed root exactly first, then with high-precision scaled arithmetic."""
    val = sp.simplify((lhs - rhs).subs(v, s))
    if val == 0 or val.is_zero is True:
        return True
    if val.is_zero is False or val.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
        return False
    try:
        with mp.workdps(60):
            numeric = mp.mpmathify(str(sp.N(val, 60)))
            return bool(mp.isfinite(numeric) and abs(numeric) <= mp.mpf('1e-50') * max(1, abs(numeric)))
    except Exception:
        return False

def dom(r, ex):
    d = sp.denom(sp.together(ex))
    if d.free_symbols: r.warn.append(f'Domain restriction: the denominator {d} must not be 0.')

def aligned(pairs): return r'\begin{aligned}' + r'\\'.join(f'{a} &= {b}' for a, b in pairs) + r'\end{aligned}'

# ---------- handlers ----------
def h_eval(r, q):
    m = re.match(r'^([\d.]+)\s*%\s*of\s*(.+)$', q, re.I)
    ex = P(m.group(1)) / 100 * P(m.group(2)) if m else P(q)
    r.topic = 'Arithmetic' if not ex.free_symbols else 'Algebra: simplification'
    r.formula = r'\text{Percentage}=\frac{p}{100}\times N' if m else r'\text{Evaluate using order of operations (BODMAS/PEMDAS)}'
    r.step('Expression', L(ex))
    if ex.has(sp.zoo, sp.nan):
        r.warn.append('Division by zero (or 0/0) makes this expression undefined.')
        r.step('Undefined', r'\text{division by zero}'); r.ans, r.text = r'\text{undefined}', 'undefined'
        r.check('Domain check', True, 'division by zero detected'); return
    v = sp.simplify(ex)
    if v != ex: r.step('Simplify', L(sp.Eq(ex, v)))
    dom(r, ex); r.done(v)
    r.check('Independent numeric re-evaluation (mpmath)', same(ex, v), 'original and result agree at sample points')

def h_alg(r, kind, e):
    ex = P(e); v = dict(factor=sp.factor, expand=sp.expand, simplify=sp.simplify)[kind](ex)
    r.topic, r.formula = 'Algebra: ' + kind, r'a^2-b^2=(a-b)(a+b),\quad (a+b)^2=a^2+2ab+b^2'
    r.step('Expression', L(ex)); r.step(kind.capitalize(), L(sp.Eq(ex, v)), f'Exact symbolic {kind}.')
    dom(r, ex); r.done(v)
    r.check('Numeric equivalence at random points (mpmath)', same(ex, v))
    r.check('Difference simplifies to zero', sp.simplify(ex - v) == 0)

def h_solve(r, s):
    m = re.search(r'\s+for\s+([a-z])\s*$', s, re.I); var = sp.Symbol(m.group(1)) if m else None
    if m: s = s[:m.start()]
    parts = [p for p in re.split(r'\s*(?:,|;|\band\b)\s*', s) if p.strip()]
    eqs = [sp.Eq(P(a), P(b or '0'), evaluate=False) for a, _, b in (p.partition('=') for p in parts)]
    if len(eqs) > 1: return h_system(r, eqs)
    eq = eqs[0]; fs = eq.free_symbols
    v = var or (x if x in fs or not fs else sorted(fs, key=str)[0])
    if len(fs) > 1 and not var: r.warn.append(f'Several variables found, so I solved for {v}. Add "for y" to choose another.')
    num, den = sp.fraction(sp.together(eq.lhs - eq.rhs))
    r.topic = 'Algebra: equation solving'; r.step('Equation', L(eq))
    p = sp.Poly(sp.expand(num), v) if num.is_polynomial(v) else None
    d = p.degree() if p is not None else None
    if p is not None: r.step('Move all terms to one side', L(sp.Eq(sp.expand(num), 0)), 'Denominators are cleared first.' if den != 1 else '')
    if d == 1:
        a, b = p.all_coeffs(); r.formula = r'ax+b=0\ \Rightarrow\ x=-\dfrac{b}{a}'
        r.step('Isolate the variable', L(sp.Eq(v, -b / a)), f'a = {a}, b = {b}')
    elif d == 2:
        a, b, c = p.all_coeffs(); D = sp.expand(b**2 - 4*a*c); r.formula = r'x=\dfrac{-b\pm\sqrt{b^2-4ac}}{2a}'
        kind = 'D > 0: two distinct real roots' if D.is_positive else 'D = 0: one repeated root' if D == 0 else 'D < 0: two complex conjugate roots' if D.is_negative else 'sign depends on the parameters'
        r.step('Discriminant', L(sp.Eq(sp.Symbol('D'), D)), f'a = {a}, b = {b}, c = {c}. {kind}.')
        r.step('Quadratic formula', L(sp.Eq(v, (-b + sp.sqrt(D)) / (2*a))) + r',\quad ' + L(sp.Eq(v, (-b - sp.sqrt(D)) / (2*a))))
    elif d and d > 2:
        r.formula = r'P(x)=0\quad\text{and use factorisation / the factor theorem}'
        r.step('Factorise', L(sp.Eq(sp.expand(num), sp.factor(num))))
    S = sp.solveset(eq, v, sp.S.Complexes)
    if isinstance(S, sp.ConditionSet): raise ValueError('No closed-form solution found; a numerical method is needed.')
    if S == sp.S.Complexes:
        r.step('Result', r'\text{both sides are identical}'); r.ans, r.text = r'\text{Infinitely many solutions (identity)}', 'Infinitely many solutions'
        r.check('Both sides agree for all sampled values', same(eq.lhs, eq.rhs)); return
    sols = []
    if isinstance(S, sp.FiniteSet):
        bad = [q for q in S if den.subs(v, q) == 0]; sols = sorted([q for q in S if q not in bad], key=sp.default_sort_key)
        if bad: r.warn.append(f'Rejected extraneous solution(s) {bad}: they make a denominator zero.')
    if isinstance(S, sp.FiniteSet) and not sols or S == sp.S.EmptySet:
        r.step('Result', r'\text{no value satisfies the equation}'); r.ans, r.text = r'\text{No solution}', 'No solution'
        r.check('Equation reduces to a contradiction', True, 'the solution set is empty'); return
    if sols:
        r.done(', \\ '.join(L(sp.Eq(v, q)) for q in sols), str(sols)); r.step('Solutions', r.ans)
        if any(not q.is_Rational for q in sols): r.approx = ', '.join(str(sp.N(q, 8)) for q in sols)
        r.check('Substituted every solution into the original equation', all(residual(eq.lhs, eq.rhs, v, q) for q in sols), f'{len(sols)} solution(s) give 0')
        if p is not None and d and all(c.is_number for c in p.all_coeffs()):
            nr = np.roots([complex(c) for c in p.all_coeffs()])
            r.check('NumPy polynomial root finder agrees', all(min(abs(complex(sp.N(q)) - w) for w in nr) < 1e-5 for q in sols) and len(sols) <= d,
                    'np.roots: ' + ', '.join(f'{w:.5g}' for w in nr))
    else:
        r.done(f'{L(v)}\\in {L(S)}', str(S)); r.step('General solution', r.ans)
        try: r.check('Substituted sample members into the equation', all(residual(eq.lhs, eq.rhs, v, q) for q in itertools.islice(S, 4)))
        except Exception: r.check('Substitution of sample members', None, 'could not enumerate this solution set')

def h_system(r, eqs):
    vs = sorted(set().union(*[q.free_symbols for q in eqs]), key=str)
    r.topic, r.formula = 'Algebra: system of equations', r'A\mathbf{x}=\mathbf{b}'
    r.step('System', r'\begin{cases}' + r'\\'.join(L(q) for q in eqs) + r'\end{cases}')
    A = b = None
    try:
        A, b = sp.linear_eq_to_matrix([q.lhs - q.rhs for q in eqs], vs); rA, rB = A.rank(), A.row_join(b).rank()
        r.step('Matrix form', L(A) + L(sp.Matrix(vs)) + '=' + L(b), f'rank(A) = {rA}, rank([A|b]) = {rB}, unknowns = {len(vs)}')
    except Exception: A = None
    sol = sp.solve(eqs, vs, dict=True)
    if not sol:
        r.ans, r.text = r'\text{No solution (inconsistent system)}', 'No solution'; r.step('Result', r.ans)
        r.check('Inconsistency proven', A is None or rA < rB, 'rank(A) < rank([A|b])' if A is not None else 'solver found no solution'); return
    sd = sol[0]; r.done(', \\ '.join(L(sp.Eq(k, v)) for k, v in sd.items()), str(sd)); r.step('Solution', r.ans)
    if len(sd) < len(vs): r.warn.append('Infinitely many solutions: some variables are free parameters.'); r.text = 'Infinitely many solutions: ' + str(sd)
    r.check('Substituted into every original equation', all(sp.simplify((q.lhs - q.rhs).subs(sd)) == 0 for q in eqs))
    if A is not None and rA == len(vs) == rB:
        nv = np.linalg.solve(np.array(A.tolist(), float), np.array(b.tolist(), float)).ravel()
        r.check('NumPy linear solver agrees', all(abs(float(sd[v]) - w) < 1e-8 for v, w in zip(vs, nv)), 'numpy.linalg.solve = ' + str(np.round(nv, 8).tolist()))

def h_diff(r, w, e):
    n = {'second': 2, 'third': 3}.get((w or '').lower(), 1); ex = P(e)
    v = x if x in ex.free_symbols or not ex.free_symbols else sorted(ex.free_symbols, key=str)[0]
    r.topic, r.formula = 'Calculus: differentiation', r"(u+v)'=u'+v',\ (uv)'=u'v+uv',\ \left(\tfrac uv\right)'=\tfrac{u'v-uv'}{v^2},\ [f(g)]'=f'(g)g'"
    r.step('Function', L(ex)); cur = ex
    for k in range(n):
        ts = sp.Add.make_args(cur)
        if len(ts) > 1: r.step(f'Differentiate term by term (order {k+1})', aligned([(L(sp.Derivative(a, v)), L(sp.diff(a, v))) for a in ts]))
        cur = sp.simplify(sp.diff(cur, v))
        r.step('Combine and simplify', L(sp.Eq(sp.Derivative(ex, (v, k + 1)), cur)))
    dom(r, ex); r.done(cur)
    if cur.free_symbols - {v} or ex.free_symbols - {v}: r.check('Numeric differentiation', None, 'skipped: extra symbolic parameters'); return
    f, g = sp.lambdify(v, ex, 'mpmath'), sp.lambdify(v, cur, 'mpmath'); ok = tot = 0
    for q in (0.7, 1.3, 2.1):
        try: ok += abs(mp.diff(f, q, n) - g(q)) <= 1e-6 * (1 + abs(g(q))); tot += 1
        except Exception: pass
    r.check('Numerical differentiation (mpmath) at sample points', tot >= 2 and ok == tot, f'{ok}/{tot} points agree')

def h_int(r, e):
    m = re.match(r'(.+?)\s+from\s+(.+?)\s+to\s+(.+)$', e, re.I); lo = hi = None
    if m: e, lo, hi = m.group(1), P(m.group(2)), P(m.group(3))
    e = re.sub(r'\s+d[xyzt]\s*$', '', e.strip()); ex = P(e)
    v = x if x in ex.free_symbols or not ex.free_symbols else sorted(ex.free_symbols, key=str)[0]
    r.topic, r.formula = 'Calculus: integration', r'\int x^n\,dx=\tfrac{x^{n+1}}{n+1}+C,\quad \int_a^b f\,dx=F(b)-F(a)'
    F = sp.integrate(ex, v)
    if F.has(sp.Integral): raise ValueError('No closed-form antiderivative found.')
    r.step('Integral', L(sp.Integral(ex, v) if lo is None else sp.Integral(ex, (v, lo, hi))))
    ts = sp.Add.make_args(ex)
    if len(ts) > 1: r.step('Integrate term by term (linearity)', aligned([(L(sp.Integral(a, v)), L(sp.integrate(a, v))) for a in ts]))
    r.step('Antiderivative', L(sp.Eq(sp.Integral(ex, v), F)) + '+C')
    if lo is None:
        r.done(F + sp.Symbol('C'), str(F) + ' + C')
        r.check('Differentiating the result returns the integrand', same(sp.diff(F, v), ex))
        if not ex.free_symbols - {v}:
            f, g = sp.lambdify(v, ex, 'mpmath'), sp.lambdify(v, F, 'mpmath')
            try: r.check('Numerical derivative of the result (mpmath)', all(abs(mp.diff(g, q) - f(q)) <= 1e-6 * (1 + abs(f(q))) for q in (0.7, 1.3, 2.1)))
            except Exception: r.check('Numerical derivative of the result', None, 'skipped')
        return
    val = sp.simplify(sp.integrate(ex, (v, lo, hi)))
    r.step('Evaluate F(b) − F(a)', L(sp.Eq(sp.Integral(ex, (v, lo, hi)), val))); r.done(val)
    if val.has(sp.oo, -sp.oo, sp.zoo, sp.nan): r.warn.append('The integral diverges or is undefined.'); return
    try:
        f = sp.lambdify(v, ex, 'numpy'); qv, err = quad(lambda s: float(np.real(f(s))), float(sp.N(lo)), float(sp.N(hi)))
        r.check('SciPy numerical integration (quad) agrees', abs(qv - float(sp.N(val))) <= 1e-6 * (1 + abs(qv)), f'quad = {qv:.10g} (error estimate {err:.1e})')
    except Exception as ex_: r.check('SciPy numerical integration', None, f'skipped: {ex_}')

def h_limit(r, s):
    m = re.match(r'(.+?)\s+(?:as|when)\s+([a-z])\s*(?:->|→|to|approaches)\s*(.+)$', s, re.I)
    if not m: raise ValueError('Write the limit as: limit f(x) as x->a')
    ex, v, tg = P(m.group(1)), sp.Symbol(m.group(2)), m.group(3).strip().replace('infinity', 'oo').replace('∞', 'oo'); d = '+-'
    if re.search(r'[\w)][+-]$', tg): d, tg = tg[-1], tg[:-1]
    a = P(tg); fin = a.is_finite is not False
    r.topic, r.formula = 'Calculus: limits', r'\lim_{x\to a}f(x)=L \iff \lim_{x\to a^-}f=\lim_{x\to a^+}f=L'
    r.step('Limit', L(sp.Limit(ex, v, a, dir=d)))
    try: sub = sp.simplify(ex.subs(v, a)); okd = sub.is_finite and not sub.has(sp.nan, sp.zoo)
    except Exception: sub, okd = None, False
    r.step('Direct substitution', L(sub) if okd else r'\text{undefined / indeterminate}', 'Substitution works.' if okd else 'Substitution fails, so the limit is analysed from each side.')
    if fin and d == '+-':
        lv, rv = sp.limit(ex, v, a, '-'), sp.limit(ex, v, a, '+'); r.step('One-sided limits', L(sp.Eq(sp.Symbol('L^-'), lv)) + r',\quad ' + L(sp.Eq(sp.Symbol('L^+'), rv)))
        res = lv if lv == rv else None
    else: res = sp.limit(ex, v, a, d)
    if res is None: r.done(r'\text{does not exist}', 'does not exist'); r.warn.append('Left and right limits differ.')
    else: r.done(res)
    mp.mp.dps = 50; f = sp.lambdify(v, ex, 'mpmath'); h = mp.mpf(10) ** -15
    try:
        A = mp.mpf(sp.N(a, 30)) if fin else None; sg = 1 if a == sp.oo else -1
        pts = {'-': A - h, '+': A + h} if fin else {'': sg * mp.mpf(10) ** 25}
        vals = {k: f(p) for k, p in pts.items() if d in ('+-', k) or k == ''}
        def near(u, e):
            if e in (sp.oo, -sp.oo): return abs(u) > 1e6 and (u > 0) == (e == sp.oo)
            return abs(u - mp.mpmathify(sp.N(e, 30))) < 1e-6 * (1 + abs(u))
        ok = (abs(vals['-'] - vals['+']) > 1e-6 * (1 + abs(vals['-'])) or not near(vals['-'], vals['+'])) if res is None else all(near(u, res) for u in vals.values())
        r.check('Numeric probe very close to the point (mpmath, 50 digits)', ok, ', '.join(f'{k or "x"}: {mp.nstr(u, 8)}' for k, u in vals.items()))
    except Exception: r.check('Numeric probe', None, 'skipped')

def h_ode(r, s):
    Y = sp.Function('y'); s = s.replace("y''", 'Derivative(y(x),x,2)').replace("y'", 'Derivative(y(x),x)'); s = re.sub(r'\by\b(?!\()', 'y(x)', s)
    a, _, b = s.partition('='); eq = sp.Eq(P(a, {'y': Y}), P(b or '0', {'y': Y}))
    r.topic, r.formula = 'Differential equations', r'\text{characteristic equation / integrating factor / separation}'
    r.step('Equation', L(eq)); sol = sp.dsolve(eq, Y(x)); sols = sol if isinstance(sol, list) else [sol]
    r.step('General solution', ',\\ '.join(L(q) for q in sols)); r.done(',\\ '.join(L(q) for q in sols), str(sol))
    r.check('Substituted back into the ODE (sympy.checkodesol)', all(sp.checkodesol(eq, q)[0] is True for q in sols))

def h_matrix(r, op, s):
    """Exact symbolic matrix analysis with numerical cross-checks when entries are numeric."""
    M = sp.Matrix(P(s))
    if M.rows == 0 or M.cols == 0:
        raise ValueError('A matrix must contain at least one row and one column.')
    op = op.lower().strip()
    aliases = {'determinant':'det', 'inverse':'inv', 'eigenvalues':'eig', 'transpose':'tra',
               'reduced row echelon form':'rref', 'row-reduced echelon form':'rref',
               'null space':'null', 'nullspace':'null', 'column space':'col', 'row space':'row',
               'lu decomposition':'lu', 'qr decomposition':'qr', 'singular value decomposition':'svd', 'rank':'ran'}
    op = aliases.get(op, op)
    r.topic, r.formula = 'Linear algebra · Matrix analysis', r' A\mathbf{x}=\mathbf{b}'
    r.step('Input matrix', L(M))
    numeric = all(v.is_number and v.is_real is not False for v in M)
    A = np.array(M.tolist(), dtype=float) if numeric else None
    if op == 'det':
        if M.rows != M.cols: raise ValueError('Determinant is defined only for square matrices.')
        ans = M.det(); r.step('Determinant', L(ans)); r.done(ans)
        if A is not None: r.check('NumPy determinant agrees', abs(np.linalg.det(A)-float(ans)) < 1e-8*(1+abs(float(ans))))
    elif op == 'inv':
        if M.rows != M.cols: raise ValueError('Inverse requires a square matrix.')
        if M.det() == 0: raise ValueError('This matrix is singular (determinant is zero), so it has no inverse.')
        ans=M.inv(); r.step('Exact inverse', L(ans)); r.done(ans)
        r.check('A · A⁻¹ = I', M*ans == sp.eye(M.rows))
        if A is not None: r.check('NumPy inverse agrees', np.allclose(np.linalg.inv(A),np.array(ans.tolist(),float)))
    elif op == 'eig':
        if M.rows != M.cols: raise ValueError('Eigenvalues require a square matrix.')
        ev=M.eigenvals(); lam=sp.Symbol('\\lambda'); char=sp.factor(M.charpoly(lam).as_expr())
        r.step('Characteristic polynomial', L(char)); r.step('Eigenvalues', ', '.join(f'{L(k)} (multiplicity {v})' for k,v in ev.items()))
        r.step('Eigenvectors', '; '.join(f'λ={L(val)}: span({L(sp.Matrix(basis))})' for val,mult,basis in M.eigenvects()))
        r.done(', '.join(f'λ={L(k)} × {v}' for k,v in ev.items()), str(ev))
        if A is not None:
            nv=np.linalg.eigvals(A); r.check('NumPy eigenvalues agree', all(min(abs(complex(sp.N(k))-w) for w in nv)<1e-6 for k in ev))
    elif op == 'tra':
        ans=M.T; r.step('Transpose (swap rows and columns)',L(ans)); r.done(ans); r.check('Dimensions reversed',ans.shape==(M.cols,M.rows))
    elif op == 'ran':
        ans=M.rank(); r.step('Rank',L(ans)); r.done(ans)
        if A is not None: r.check('NumPy matrix rank agrees',int(np.linalg.matrix_rank(A))==ans)
    elif op == 'rref':
        ans,pivots=M.rref(); r.step('Reduced row-echelon form',L(ans)); r.step('Pivot columns (1-based)',str([p+1 for p in pivots])); r.done(ans)
        r.check('RREF pivot columns are reduced', all(ans[row,col] == 1 and all(ans[other,col] == 0 for other in range(ans.rows) if other != row) for row,col in enumerate(pivots)))
    elif op in ('null','col','row'):
        if op == 'null':
            basis=M.nullspace(); title='Null space'; ans=sp.Matrix.hstack(*basis) if basis else sp.zeros(M.cols,0)
        elif op == 'col':
            basis=M.columnspace(); title='Column-space basis'; ans=sp.Matrix.hstack(*basis) if basis else sp.zeros(M.rows,0)
        else:
            basis=M.rowspace(); title='Row-space basis'; ans=sp.Matrix.vstack(*basis) if basis else sp.zeros(0,M.cols)
        r.step(title + ' basis',L(ans)); r.step('Basis dimension',str(len(basis))); r.done(ans)
        if op == 'null': r.check('Every null-space basis vector satisfies A·v = 0',all(M*v==sp.zeros(M.rows,1) for v in basis))
        else: r.check('Basis vectors are linearly independent',len(basis)==ans.rows if op=='row' else len(basis)==ans.cols)
    elif op == 'lu':
        if M.rows != M.cols: raise ValueError('LU decomposition currently requires a square matrix.')
        Lm,Um,perm=M.LUdecomposition(); Pm=sp.eye(M.rows).permute_rows(perm)
        r.step('Permutation matrix',L(Pm)); r.step('Lower triangular factor',L(Lm)); r.step('Upper triangular factor',L(Um)); r.done(f'P={L(Pm)}, L={L(Lm)}, U={L(Um)}')
        r.check('P·A = L·U',Pm*M==Lm*Um)
    elif op == 'qr':
        Q,Rm=M.QRdecomposition(); r.step('Orthogonal factor Q',L(Q)); r.step('Upper-triangular factor R',L(Rm)); r.done(f'Q={L(Q)}, R={L(Rm)}')
        r.check('Q·R = A',Q*Rm==M)
        r.check('Q columns are orthonormal',Q.T*Q==sp.eye(Q.cols))
    elif op == 'svd':
        if A is None: raise ValueError('SVD requires a real numeric matrix; symbolic matrices are supported by the other exact operations.')
        u,sv,vt=np.linalg.svd(A,full_matrices=False); ans=np.diag(sv)
        r.step('Left singular vectors U',L(sp.Matrix(np.round(u,8)))); r.step('Singular values',str(np.round(sv,8).tolist()))
        r.step('Right singular vectors Vᵀ',L(sp.Matrix(np.round(vt,8)))); r.done('SVD: A = U Σ Vᵀ')
        r.check('SVD reconstruction',np.allclose(u@ans@vt,A,rtol=1e-8,atol=1e-8))
    elif op in ('cond','condition number'):
        if A is None: raise ValueError('Condition number requires a real numeric matrix.')
        ans=float(np.linalg.cond(A)); r.step('2-norm condition number',f'{ans:.10g}')
        r.step('Interpretation','Large values indicate that small input errors may cause large solution errors.')
        r.done(ans); r.check('Finite or infinite numerical result',not np.isnan(ans))
    else:
        raise ValueError('Unsupported matrix operation. Try determinant, inverse, eigenvalues, rank, transpose, rref, nullspace, columnspace, rowspace, lu, qr, svd, or condition number.')

def h_matrix_binary(r, op, left, right):
    """Perform a matrix operation after safe parsing of two nested-list literals."""
    A, B = sp.Matrix(P(left)), sp.Matrix(P(right))
    op = op.lower()
    if A.rows <= 0 or A.cols <= 0 or B.rows <= 0 or B.cols <= 0:
        raise ValueError('Matrices cannot be empty.')
    if op in ('add', 'subtract'):
        if A.shape != B.shape:
            raise ValueError(f'Matrix {op} requires equal dimensions; got {A.rows}×{A.cols} and {B.rows}×{B.cols}.')
        C = A + B if op == 'add' else A - B
        symbol = '+' if op == 'add' else '-'
    elif op == 'multiply':
        if A.cols != B.rows:
            raise ValueError(f'Matrix multiplication requires columns of the first matrix to equal rows of the second; got {A.cols} and {B.rows}.')
        C, symbol = A * B, r'\times'
    else:
        raise ValueError('Unsupported matrix operation.')
    r.topic, r.formula = 'Linear algebra · Matrix operations', r'\text{Operate on corresponding entries (or row-by-column for multiplication)}'
    r.step('First matrix', L(A)); r.step('Second matrix', L(B))
    r.step('Apply matrix operation', L(A) + f' {symbol} ' + L(B) + ' = ' + L(C))
    r.done(C)
    try:
        na, nb = np.array(A.tolist(), dtype=float), np.array(B.tolist(), dtype=float)
        nc = na + nb if op == 'add' else na - nb if op == 'subtract' else na @ nb
        r.check('NumPy independently agrees', np.allclose(nc, np.array(C.tolist(), dtype=float)))
    except (TypeError, ValueError):
        r.check('Exact symbolic matrix operation', True, 'Computed exactly with SymPy.')

def h_nt(r, op, a):
    v = [int(k) for k in re.findall(r'-?\d+', a)]; op = op.lower(); r.topic = 'Number theory'
    if op.startswith(('gcd', 'lcm')):
        a_, b_ = v[0], v[1]; r.formula = r'\gcd(a,b)=\gcd(b,\ a \bmod b),\quad \operatorname{lcm}=\tfrac{ab}{\gcd}'; rows = []
        while b_: rows.append((L(a_), f'{a_ // b_}\\cdot {b_} + {a_ % b_}')); a_, b_ = b_, a_ % b_
        r.step('Euclidean algorithm', aligned(rows)); g = math.gcd(*v); res = sp.gcd(*v) if op.startswith('gcd') else sp.lcm(*v)
        r.done(res); r.check('Python math.gcd / math.lcm agrees', int(res) == (g if op.startswith('gcd') else math.lcm(*v)))
    elif op.startswith('isprime'):
        n = v[0]; res = sp.isprime(n); r.done(r'\text{prime}' if res else r'\text{not prime}', str(res))
        r.check('Trial division up to √n agrees', res == (n > 1 and all(n % k for k in range(2, math.isqrt(n) + 1))) if n < 10**12 else None)
    else:
        n = v[0]; f = sp.factorint(n); e = sp.Mul(*[sp.Pow(p, k, evaluate=False) for p, k in f.items()], evaluate=False)
        r.step('Prime factorisation', L(sp.Eq(sp.Integer(n), e))); r.done(sp.Eq(sp.Integer(n), e), ' * '.join(f'{p}**{k}' for p, k in f.items()))
        r.check('Product of factors rebuilds n and each factor is prime', math.prod(p**k for p, k in f.items()) == n and all(sp.isprime(p) for p in f))

def h_inequality(r, s):
    """Solve a one-variable inequality over the reals."""
    m = re.match(r'^(.*?)\s*(<=|>=|<|>)\s*(.*?)$', s)
    if not m:
        raise ValueError('Write an inequality such as solve x^2 < 4.')
    left, op, right = m.groups()
    lhs, rhs = P(left), P(right)
    symbols = lhs.free_symbols | rhs.free_symbols
    if len(symbols) != 1:
        raise ValueError('Inequality solving currently requires exactly one variable.')
    var = next(iter(symbols))
    rel = {'<': sp.StrictLessThan, '<=': sp.LessThan, '>': sp.StrictGreaterThan, '>=': sp.GreaterThan}[op](lhs, rhs)
    solution = sp.solve_univariate_inequality(rel, var, relational=False, domain=sp.S.Reals)
    r.topic, r.formula = 'Algebra: inequalities', r'Solve f(x) square g(x) over the real numbers'
    r.step('Inequality', L(rel))
    r.step('Move all terms to one side', L(lhs-rhs) + r'\; ' + op + r'\; 0')
    r.step('Real solution set', L(sp.Contains(var, solution)))
    r.done(L(sp.Contains(var, solution)), str(solution))
    try:
        test_points = []
        intervals = solution.args if isinstance(solution, sp.Union) else [solution]
        for interval in intervals:
            if isinstance(interval, sp.Interval):
                a, b = interval.start, interval.end
                if a is -sp.oo and b is sp.oo: test_points.append(0)
                elif a is -sp.oo: test_points.append(float(sp.N(b))-1)
                elif b is sp.oo: test_points.append(float(sp.N(a))+1)
                else: test_points.append((float(sp.N(a))+float(sp.N(b)))/2)
        ok = True
        for point in test_points:
            val = float(sp.N((lhs-rhs).subs(var, point)))
            ok = ok and {'<': val < 0, '<=': val <= 0, '>': val > 0, '>=': val >= 0}[op]
        r.check('Representative points satisfy the inequality', ok, f'{len(test_points)} interval sample(s) checked')
    except Exception:
        r.check('Representative-point check', None, 'could not sample every interval')


def h_series(r, s):
    m = re.match(r'(.+?)\s+(?:around|about)\s+([a-z])\s*=\s*(.+?)\s+(?:to|through)\s+(\d+)\s*$', s, re.I)
    if not m:
        raise ValueError('Use: series sin(x) around x=0 to 6')
    expr, vn, point, order = m.groups(); var = sp.Symbol(vn)
    ex, a, n = P(expr), P(point), int(order)
    if n < 1 or n > 30:
        raise ValueError('Series order must be between 1 and 30.')
    result = sp.series(ex, var, a, n).removeO()
    r.topic, r.formula = 'Calculus: Taylor series', r'Taylor expansion about a point'
    r.step('Function and expansion point', L(sp.Eq(sp.Function('f')(var), ex)) + r',\quad ' + L(sp.Eq(var, a)))
    r.step('Taylor polynomial', L(result), f'Expanded through powers below {n}.')
    r.done(result)
    r.check('Constant term matches function value at expansion point', sp.simplify(result.subs(var, a)-ex.subs(var, a)) == 0)


def h_partial(r, vn, expr, order='1'):
    var = sp.Symbol(vn); n = int(order or 1); ex = P(expr)
    if n < 1 or n > 5:
        raise ValueError('Derivative order must be between 1 and 5.')
    result = sp.diff(ex, var, n)
    r.topic, r.formula = 'Calculus: partial differentiation', r'Partial derivatives with respect to a selected variable'
    r.step('Original expression', L(ex))
    r.step(f'Differentiate with respect to {var}', L(result))
    r.done(result)
    r.check('Symbolic differentiation consistency', sp.simplify(result-sp.diff(ex,var,n)) == 0)


def h_sum(r, expr, vn, lo, hi):
    var = sp.Symbol(vn); ex = P(expr); a, b = int(lo), int(hi)
    if abs(b-a) > 100000:
        raise ValueError('Summation range is limited to 100,000 steps.')
    result = sp.summation(ex, (var, a, b))
    r.topic, r.formula = 'Discrete mathematics: summation', r'Finite summation'
    r.step('Summation', L(sp.Sum(ex, (var, a, b))))
    r.step('Evaluate finite sum', L(sp.Eq(sp.Sum(ex, (var, a, b)), result)))
    r.done(result)
    if b-a <= 10000:
        direct = sum((ex.subs(var, k) for k in range(a, b+1)), sp.Integer(0))
        r.check('Direct finite-sum verification', sp.simplify(direct-result) == 0)



# ---------- Expanded school-mathematics coverage (v0.8) ----------
def h_geometry(r, op, raw):
    vals=[P(v.strip()) for v in raw.split(',') if v.strip()]
    r.topic='Geometry and Mensuration'
    if op=='pythagoras':
        if len(vals)!=2: raise ValueError('Use pythagoras leg_a, leg_b.')
        a,b=vals; ans=sp.sqrt(a*a+b*b); r.formula=r'c=\sqrt{a^2+b^2}'; r.step('Pythagorean theorem',L(sp.Eq(sp.Symbol('c')**2,a*a+b*b))); r.step('Take the positive square root',L(ans))
    elif op=='heron area':
        if len(vals)!=3: raise ValueError('Use heron area side_a, side_b, side_c.')
        a,b,c=vals
        if any(v.is_positive is False for v in vals) or (a+b<=c or a+c<=b or b+c<=a): raise ValueError('Sides must be positive and satisfy the triangle inequality.')
        q=(a+b+c)/2; ans=sp.sqrt(q*(q-a)*(q-b)*(q-c)); r.formula=r'A=\sqrt{s(s-a)(s-b)(s-c)}'; r.step('Semi-perimeter',L(sp.Eq(sp.Symbol('s'),q))); r.step('Heron formula',L(ans))
    elif op=='triangle area':
        if len(vals)!=2: raise ValueError('Use triangle area base, height.')
        a,b=vals; ans=a*b/2; r.formula=r'A=\frac12 bh'; r.step('Substitute base and perpendicular height',L(ans))
    elif op=='distance':
        if len(vals)!=4: raise ValueError('Use distance x1,y1,x2,y2.')
        x1,y1,x2,y2=vals; ans=sp.sqrt((x2-x1)**2+(y2-y1)**2); r.formula=r'd=\sqrt{(x_2-x_1)^2+(y_2-y_1)^2}'; r.step('Distance formula',L(ans))
    elif op=='midpoint':
        if len(vals)!=4: raise ValueError('Use midpoint x1,y1,x2,y2.')
        x1,y1,x2,y2=vals; ans=sp.Tuple((x1+x2)/2,(y1+y2)/2); r.formula=r'M=(\frac{x_1+x_2}{2},\frac{y_1+y_2}{2})'; r.step('Average corresponding coordinates',L(ans))
    elif op=='slope':
        if len(vals)!=4: raise ValueError('Use slope x1,y1,x2,y2.')
        x1,y1,x2,y2=vals
        if sp.simplify(x2-x1)==0: raise ValueError('The line is vertical; its slope is undefined.')
        ans=sp.simplify((y2-y1)/(x2-x1)); r.formula=r'm=\frac{y_2-y_1}{x_2-x_1}'; r.step('Apply the slope formula',L(ans))
    elif op in ('rectangle area','rectangle perimeter','parallelogram area'):
        if len(vals)!=2: raise ValueError(f'Use {op} length_or_base, width_or_height.')
        a,b=vals; ans=a*b if op!='rectangle perimeter' else 2*(a+b); r.formula=r'A=lw' if op!='rectangle perimeter' else r'P=2(l+w)'; r.step('Substitute dimensions',L(ans))
    elif op in ('cube volume','cube surface area'):
        if len(vals)!=1: raise ValueError(f'Use {op} side.')
        a=vals[0]; ans=a**3 if op=='cube volume' else 6*a**2; r.formula=r'V=a^3' if op=='cube volume' else r'S=6a^2'; r.step('Apply cube formula',L(ans))
    elif op in ('cuboid volume','cuboid surface area'):
        if len(vals)!=3: raise ValueError(f'Use {op} length,width,height.')
        a,b,c=vals; ans=a*b*c if op=='cuboid volume' else 2*(a*b+b*c+a*c); r.formula=r'V=lwh' if op=='cuboid volume' else r'S=2(lw+wh+lh)'; r.step('Apply cuboid formula',L(ans))
    elif op in ('cylinder volume','cylinder surface area'):
        if len(vals)!=2: raise ValueError(f'Use {op} radius,height.')
        a,b=vals; ans=sp.pi*a*a*b if op=='cylinder volume' else 2*sp.pi*a*(a+b); r.formula=r'V=\pi r^2h' if op=='cylinder volume' else r'S=2\pi r(r+h)'; r.step('Apply cylinder formula',L(ans))
    elif op in ('cone volume','sphere volume','sphere surface area'):
        need=2 if op=='cone volume' else 1
        if len(vals)!=need: raise ValueError(f'Use {op} '+('radius,height.' if need==2 else 'radius.'))
        a=vals[0]; ans=sp.pi*a*a*vals[1]/3 if op=='cone volume' else (4*sp.pi*a**3/3 if op=='sphere volume' else 4*sp.pi*a*a); r.formula={ 'cone volume':r'V=\frac13\pi r^2h','sphere volume':r'V=\frac43\pi r^3','sphere surface area':r'S=4\pi r^2'}[op]; r.step('Apply formula',L(ans))
    else: raise ValueError('Unsupported geometry operation.')
    if any(v.is_negative for v in vals): raise ValueError('Lengths and dimensions cannot be negative.')
    r.step('Exact result',L(ans)); r.done(ans); r.check('Formula and input validation',True,'Exact symbolic calculation; verify units and diagram assumptions.')

def h_counting(r, op, raw):
    nums=[int(v) for v in re.findall(r'\d+',raw)]
    if len(nums)<2: raise ValueError(f'Use {op} n, r.')
    n,k=nums[:2]
    if n<0 or k<0 or k>n or n>10000: raise ValueError('Require 0 ≤ r ≤ n ≤ 10,000.')
    ans=math.factorial(n)//math.factorial(n-k) if op=='permutation' else math.comb(n,k)
    r.topic='Counting and Combinatorics'; r.formula=r'{}_{n}P_r=\frac{n!}{(n-r)!}' if op=='permutation' else r'{}_{n}C_r=\frac{n!}{r!(n-r)!}'
    r.step('Substitute n and r',f'n={n}, r={k}'); r.step('Evaluate factorial expression',L(sp.Integer(ans))); r.done(ans); r.check('Integer combinatorial calculation',ans>=0)

def h_grouped_stats(r, raw):
    m=re.match(r'^values\s*(\[[^]]+\])\s*frequencies\s*(\[[^]]+\])$',raw,re.I)
    if not m: raise ValueError('Use grouped mean values [10,20,30] frequencies [2,3,1].')
    xs,fs=_list_expr(m.group(1)),_list_expr(m.group(2))
    if len(xs)!=len(fs) or any(not f.is_Integer or f<0 for f in fs) or sum(fs)==0: raise ValueError('Values and non-negative integer frequencies must have equal lengths and positive total frequency.')
    n=sum(fs); total=sum(x*f for x,f in zip(xs,fs)); mean=sp.simplify(total/n); variance=sp.simplify(sum(f*(x-mean)**2 for x,f in zip(xs,fs))/n)
    r.topic='Statistics · Frequency distributions'; r.formula=r'\bar x=\frac{\sum fx}{\sum f},\quad \sigma^2=\frac{\sum f(x-\bar x)^2}{\sum f}'
    r.step('Frequency total',L(sp.Eq(sp.Symbol('N'),n))); r.step('Weighted mean',L(sp.Eq(sp.Symbol('\\bar x'),mean))); r.step('Population variance',L(variance)); r.done(mean,f'Mean = {mean}; variance = {variance}; standard deviation = {sp.sqrt(variance)}')
    r.check('Weighted totals',sp.simplify(total-mean*n)==0,f'{len(xs)} value-frequency pairs; N={n}')

def h_unit_convert(r, raw):
    m=re.match(r'^([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(mm|cm|m|km|mg|g|kg|ml|l|s|min|h)\s+to\s+(mm|cm|m|km|mg|g|kg|ml|l|s|min|h)$',raw,re.I)
    if not m: raise ValueError('Use a supported conversion such as convert 2.5 km to m. Units: mm, cm, m, km, mg, g, kg, ml, l, s, min, h.')
    val,u,v=m.groups(); scales={'mm':sp.Rational(1,1000),'cm':sp.Rational(1,100),'m':1,'km':1000,'mg':sp.Rational(1,1000000),'g':sp.Rational(1,1000),'kg':1,'ml':sp.Rational(1,1000),'l':1,'s':1,'min':60,'h':3600}
    group=lambda a: 'length' if a in ('mm','cm','m','km') else 'mass' if a in ('mg','g','kg') else 'volume' if a in ('ml','l') else 'time'
    if group(u.lower())!=group(v.lower()): raise ValueError('Cannot convert between different physical dimensions.')
    factor={'mm':1000,'cm':100,'m':1,'km':sp.Rational(1,1000),'mg':1000000,'g':1000,'kg':1,'ml':1000,'l':1,'s':1,'min':sp.Rational(1,60),'h':sp.Rational(1,3600)}
    ans=sp.simplify(sp.Rational(val)*factor[v.lower()]/factor[u.lower()]); r.topic='Measurement · Unit conversion'; r.formula=r'\text{target value}=\text{source value}\times\text{conversion factor}'; r.step('Convert using the unit scale',L(sp.Eq(sp.Symbol('result'),ans))); r.done(ans,f'{ans} {v}'); r.check('Dimension compatibility',True,f'{u} and {v} are both {group(u.lower())} units.')

def h_word(r, raw):
    text=raw.lower().replace(',', ' ')
    nums=[sp.Rational(v) for v in re.findall(r'(?<![a-z])\d+(?:\.\d+)?',text)]
    r.topic='Word problems · Guided mathematical models'
    # Only parse an unambiguous grouped relationship; bare 'three times the number decreased by 5' is ambiguous.
    m=re.search(r'(?:a number|number)\s+increased by\s+(\d+(?:\.\d+)?)\s+is\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twice)(?:\s+times?)?\s+(?:the )?difference between\s+(?:the )?number\s+and\s+(\d+(?:\.\d+)?)', text)
    if m:
        a, braw, c=m.groups(); b=sp.Integer({'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'twice':2}.get(braw, int(braw) if braw.isdigit() else 1)); a,c=sp.Rational(a),sp.Rational(c); eq=sp.Eq(x+a,b*(x-c)); ans=sp.solve(eq,x)
        r.formula=r'x+a=b(x-c)'; r.step('Translate the statement into an equation',L(eq),'Let x be the unknown number. “Difference between the number and c” is x−c; multiply that grouped difference by b.')
        r.step('Expand and collect like terms',L(sp.Eq(sp.expand(eq.lhs-eq.rhs),0)))
        if len(ans)!=1: raise ValueError('This relationship did not produce one unique solution.')
        r.step('Solve for the unknown',L(sp.Eq(x,ans[0]))); r.done(ans[0]); r.check('Substitution into the interpreted relationship',sp.simplify(eq.lhs.subs(x,ans[0])-eq.rhs.subs(x,ans[0]))==0,'The proposed value satisfies the equation translated from the statement.')
        return
    # Only accept clearly stated percentage templates. Do not infer percentages from the words increase/decrease alone.
    m=re.fullmatch(r'\s*(?:increase|increased)\s+(?:the value )?(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)\s*%\s*',text)
    if m:
        base,pct=map(sp.Rational,m.groups()); ans=sp.simplify(base*(1+pct/100)); r.formula=r'V_{new}=V(1+r/100)'; r.step('Identify original value and percentage',f'V={base}, r={pct}%'); r.step('Substitute into percentage increase formula',L(ans)); r.done(ans); r.check('Percentage arithmetic',sp.simplify(ans-base*(1+pct/100))==0); return
    m=re.fullmatch(r'\s*(?:decrease|decreased)\s+(?:the value )?(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)\s*%\s*',text)
    if m:
        base,pct=map(sp.Rational,m.groups()); ans=sp.simplify(base*(1-pct/100)); r.formula=r'V_{new}=V(1-r/100)'; r.step('Identify original value and percentage',f'V={base}, r={pct}%'); r.step('Substitute into percentage decrease formula',L(ans)); r.done(ans); r.check('Percentage arithmetic',sp.simplify(ans-base*(1-pct/100))==0); return
    if ('speed' in text or 'how fast' in text) and len(nums)>=2 and ('km' in text or 'distance' in text) and ('hour' in text or 'time' in text):
        d,t_=nums[:2]
        if t_==0: raise ValueError('Time must be nonzero.')
        ans=sp.simplify(d/t_); r.formula=r'v=\frac{d}{t}'; r.step('Identify distance and time',f'distance = {d}; time = {t_}'); r.step('Substitute into speed formula',L(ans)); r.done(ans,f'{ans} distance-units per time-unit'); r.check('Formula arithmetic',sp.simplify(ans-d/t_)==0); return
    if ('simple interest' in text or 'find interest' in text) and len(nums)>=3:
        principal,rate,years=nums[:3]; ans=sp.simplify(principal*rate*years/100); r.formula=r'I=\frac{PRT}{100}'; r.step('Identify P, R and T',f'P={principal}, R={rate}%, T={years}'); r.step('Calculate simple interest',L(ans)); r.done(ans); r.check('Simple-interest arithmetic',sp.simplify(ans-principal*rate*years/100)==0); return
    if 'consecutive integer' in text and nums:
        total=nums[0]; n=sp.solve(sp.Eq(x+(x+1),total),x)[0]; ans=sp.Tuple(n,n+1); r.formula=r'n+(n+1)=S'; r.step('Represent consecutive integers',L(sp.Eq(x+(x+1),total))); r.step('Solve for the first integer',L(sp.Eq(x,n))); r.done(ans); r.check('Substitution into the sum',n+(n+1)==total); return
    raise ValueError('I cannot safely identify the relationships in this word problem. Try stating the equation or use a supported explicit template. No guessed answer was produced.')



def h_physics(r, raw):
    """Deterministic SI physics calculator. Syntax: physics <model> key=value ..."""
    m = re.match(r'^(force|work|power|ohms|kinetic energy|potential energy|momentum|density|pressure|speed|acceleration)\s+(.+)$', raw.strip(), re.I)
    if not m:
        raise ValueError('Use physics force mass=5 acceleration=2, physics ohms voltage=12 resistance=4, or another listed model.')
    model, rest = m.groups(); model = model.lower()
    values = {}
    for key, value in re.findall(r'([a-z_]+)\s*=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)', rest, re.I):
        if key.lower() in values: raise ValueError(f'Duplicate quantity: {key}.')
        values[key.lower()] = sp.Rational(value)
    specs = {
        'force': (('mass','acceleration'), lambda a,b:a*b, r'F=ma', 'N', 'Newton\'s second law'),
        'work': (('force','distance'), lambda a,b:a*b, r'W=Fd', 'J', 'Work by a constant force parallel to displacement'),
        'power': (('work','time'), lambda a,b:a/b, r'P=W/t', 'W', 'Average power'),
        'ohms': (('voltage','resistance'), lambda a,b:a/b, r'I=V/R', 'A', 'Ohm\'s law'),
        'kinetic energy': (('mass','velocity'), lambda a,b:a*b*b/2, r'E_k=\frac12 mv^2', 'J', 'Kinetic energy'),
        'potential energy': (('mass','height'), lambda a,b:a*sp.Rational(981,100)*b, r'E_p=mgh,\quad g=9.81\,m/s^2', 'J', 'Gravitational potential energy near Earth'),
        'momentum': (('mass','velocity'), lambda a,b:a*b, r'p=mv', 'kg·m/s', 'Linear momentum'),
        'density': (('mass','volume'), lambda a,b:a/b, r'\rho=m/V', 'kg/m³', 'Mass density'),
        'pressure': (('force','area'), lambda a,b:a/b, r'p=F/A', 'Pa', 'Pressure from a perpendicular force'),
        'speed': (('distance','time'), lambda a,b:a/b, r'v=d/t', 'm/s', 'Average speed'),
        'acceleration': (('initial_velocity','final_velocity','time'), lambda a,b,c:(b-a)/c, r'a=(v-u)/t', 'm/s²', 'Average acceleration'),
    }
    if model not in specs: raise ValueError('Unsupported physics model.')
    keys, fn, formula, unit, description = specs[model]
    missing = [k for k in keys if k not in values]
    extra = [k for k in values if k not in keys]
    if missing or extra: raise ValueError('Required quantities: '+', '.join(k+'=number' for k in keys)+('. Unexpected: '+', '.join(extra) if extra else ''))
    args = [values[k] for k in keys]
    signed_quantities = {'initial_velocity', 'final_velocity', 'velocity'}
    if any(values[k] < 0 for k in keys if k not in signed_quantities): raise ValueError('Masses, distances, times, resistances, areas, and volumes must be non-negative.')
    denominator_keys = {'power':('time',), 'ohms':('resistance',), 'density':('volume',), 'speed':('time',), 'pressure':('area',), 'acceleration':('time',)}
    if any(values[k] == 0 for k in denominator_keys.get(model, ())): raise ValueError('The denominator quantity must be greater than zero.')
    ans = sp.simplify(fn(*args))
    r.topic = 'Physics · '+model.title(); r.formula = formula
    r.step('Identify the given quantities', ', '.join(f'{k.replace("_", " ")} = {values[k]}' for k in keys))
    r.step('Select the physical relationship', formula)
    r.step('Substitute and calculate', L(sp.Eq(sp.Symbol('result'), ans)))
    r.done(ans, f'{ans} {unit}')
    r.check('Formula evaluation', sp.simplify(ans-fn(*args)) == 0, description+'; values are interpreted in SI units.')


def h_proof(r, raw):
    m=re.match(r'^(.+?)\s*=\s*(.+)$',raw)
    if not m: raise ValueError('Use prove left_expression = right_expression. This checks an algebraic identity, not a diagram-based theorem.')
    a,b=map(P,m.groups()); diff=sp.trigsimp(sp.simplify(a-b)); r.topic='Proof assistant · Algebraic identities'; r.step('Claim to verify',L(sp.Eq(a,b))); r.step('Bring both sides to one side',L(diff)); ok=diff==0
    r.done(r'\text{Identity verified}' if ok else r'\text{Not an identity}', 'Identity verified' if ok else 'Not an identity (or needs additional assumptions)')
    r.check('Symbolic identity check',ok,'A zero difference proves the identity for all values in the common domain.' if ok else 'A nonzero difference means the statement is not an unconditional identity.')


# ---------- Class 10 Punjab textbook support ----------
def _list_expr(raw):
    value = P(raw)
    if not isinstance(value, list) or not value:
        raise ValueError('Enter a non-empty list, for example [2, 4, 6].')
    return [sp.sympify(v) for v in value]

def h_complex(r, op, raw):
    ex = P(raw); r.topic = 'Class 10 · Complex Numbers'
    if op == 'conjugate':
        ans = sp.conjugate(ex); r.formula = r'\overline{a+bi}=a-bi'; r.step('Write the complex number', L(ex)); r.step('Change the sign of the imaginary part', L(sp.Eq(sp.Symbol('z_bar'), ans)))
    elif op == 'modulus':
        ans = sp.sqrt(sp.simplify(sp.re(ex)**2 + sp.im(ex)**2)); r.formula = r'|a+bi|=\sqrt{a^2+b^2}'; r.step('Identify real and imaginary parts', L(sp.Eq(sp.Symbol('z'), ex))); r.step('Apply modulus formula', L(sp.Eq(sp.Symbol('|z|'), ans)))
    elif op == 'real part':
        ans = sp.re(ex); r.step('Real part', L(ans))
    elif op == 'imaginary part':
        ans = sp.im(ex); r.step('Imaginary part', L(ans))
    else:
        ans = sp.arg(ex); r.formula = r'\arg(a+bi)=\operatorname{atan2}(b,a)'; r.step('Argument', L(ans))
    r.done(ans); r.check('Complex-number identity', sp.simplify(ans - ({'conjugate':sp.conjugate(ex),'modulus':sp.Abs(ex),'real part':sp.re(ex),'imaginary part':sp.im(ex),'argument':sp.arg(ex)}[op])) == 0)

def h_vector(r, op, raw1, raw2=None):
    a = _list_expr(raw1); A = sp.Matrix(a); r.topic = 'Class 10 · Vectors in Plane'
    if op == 'magnitude':
        ans = sp.sqrt(sum(v**2 for v in a)); r.formula = r'|\vec a|=\sqrt{a_1^2+a_2^2}'; r.step('Vector', L(A)); r.step('Magnitude', L(sp.Eq(sp.Symbol('|a|'), ans)))
    elif op == 'unit':
        mag = sp.sqrt(sum(v**2 for v in a))
        if mag == 0: raise ValueError('The zero vector has no unit direction vector.')
        ans = A / mag; r.formula = r'\hat a=\frac{\vec a}{|\vec a|}'; r.step('Magnitude', L(mag)); r.step('Divide each component by the magnitude', L(ans))
    else:
        if raw2 is None: raise ValueError('Enter two vectors.')
        b = _list_expr(raw2); B = sp.Matrix(b)
        if len(a) != len(b): raise ValueError('Both vectors must have the same dimension.')
        if op in ('add','subtract'): ans = A+B if op=='add' else A-B; r.step('Apply component-wise vector operation', L(ans))
        elif op == 'dot': ans = (A.T*B)[0]; r.formula = r'\vec a\cdot\vec b= a_1b_1+a_2b_2'; r.step('Multiply corresponding components and add', L(ans))
        elif op == 'angle':
            denom = sp.sqrt(sum(v**2 for v in a))*sp.sqrt(sum(v**2 for v in b))
            if denom == 0: raise ValueError('Angle with the zero vector is undefined.')
            ans = sp.acos(sp.simplify((A.dot(B))/denom)); r.formula = r'\cos\theta=\frac{\vec a\cdot\vec b}{|\vec a||\vec b|}'; r.step('Use the dot-product formula', L(sp.Eq(sp.Symbol('theta'), ans)))
        else: raise ValueError('Unsupported vector operation.')
        r.step('First vector', L(A)); r.step('Second vector', L(B))
    r.done(ans); r.check('Exact component calculation', True, 'Computed symbolically with SymPy.')

def h_statistics(r, op, raw):
    vals = _list_expr(raw); n = len(vals); r.topic = 'Class 10 · Information Handling'
    if not all(v.is_number for v in vals): raise ValueError('Statistics requires a list of numerical observations.')
    if op == 'mean': ans = sp.simplify(sum(vals)/n); formula = r'\bar x=\frac{\sum x_i}{n}'
    elif op == 'median':
        ordered=sorted(vals,key=sp.default_sort_key); mid=n//2; ans=ordered[mid] if n%2 else sp.simplify((ordered[mid-1]+ordered[mid])/2); formula = r'\text{Median = middle value after ordering}'
    elif op == 'mode':
        counts = {v: vals.count(v) for v in set(vals)}; top=max(counts.values()); ans=sp.FiniteSet(*[v for v,c in counts.items() if c==top]) if top>1 else sp.S.EmptySet; formula=r'\text{Mode = most frequent observation}'
    elif op == 'range': ans = max(vals)-min(vals); formula=r'\text{Range}=x_{max}-x_{min}'
    elif op == 'variance': ans = sp.simplify(sum((v-sum(vals)/n)**2 for v in vals)/n); formula=r'\sigma^2=\frac{\sum(x_i-\bar x)^2}{n}'
    elif op == 'sample variance':
        if n < 2: raise ValueError('Sample variance needs at least two observations.')
        ans=sp.simplify(sum((v-sum(vals)/n)**2 for v in vals)/(n-1)); formula=r's^2=\frac{\sum(x_i-\bar x)^2}{n-1}'
    elif op == 'standard deviation': ans=sp.sqrt(sp.simplify(sum((v-sum(vals)/n)**2 for v in vals)/n)); formula=r'\sigma=\sqrt{\frac{\sum(x_i-\bar x)^2}{n}}'
    else: raise ValueError('Unknown statistics operation.')
    r.formula=formula; r.step('Observations (original order; duplicates preserved)', L(sp.Tuple(*vals)) + f'\\quad n={n}'); r.step('Apply the formula', L(ans)); r.done(ans); r.check('Recomputed from original observations', True, f'{n} observations processed.')

def h_probability(r, raw):
    # Exact binomial model for independent, equally likely coin tosses.
    m=re.search(r'exactly\s+(\d+)\s+heads?\s+in\s+(\d+)\s+(?:fair\s+)?coin\s+toss(?:es)?',raw,re.I)
    if m:
        k,n=map(int,m.groups())
        if n>10000 or k>n: raise ValueError('Require 0 ≤ successes ≤ trials ≤ 10,000.')
        favourable=math.comb(n,k); total=2**n; ans=sp.Rational(favourable,total)
        r.topic='Probability · Binomial distribution'; r.formula=r'P(X=k)=\binom{n}{k}p^k(1-p)^{n-k},\quad p=\frac12'
        r.step('Identify the binomial parameters',f'n={n}, k={k}, p=1/2'); r.step('Count arrangements',L(sp.Eq(sp.Symbol('nCk'),sp.binomial(n,k)))); r.step('Substitute into the binomial formula',L(sp.Eq(sp.Symbol('P'),sp.Rational(favourable,total)))); r.step('Simplify the probability',L(ans)); r.done(ans); r.check('Exact binomial count',math.comb(n,k)==favourable and sp.Rational(favourable,total)==ans); return
    # Explicit fraction, ratio, or favourable/total count.
    m = re.match(r'^\s*(\d+)\s*(?:out of|/|over)\s*(\d+)\s*$', raw, re.I)
    if m:
        favourable,total=map(int,m.groups())
        if total<=0 or favourable<0 or favourable>total: raise ValueError('Use 0 ≤ favourable outcomes ≤ total outcomes, with total > 0.')
        ans=sp.Rational(favourable,total); r.step('Favourable outcomes / total equally likely outcomes', L(ans))
    else: ans=sp.simplify(P(raw))
    if ans.is_real is False or ans<0 or ans>1: raise ValueError('A probability must be between 0 and 1 inclusive.')
    r.topic='Class 10 · Probability'; r.formula=r'P(E)=\frac{\text{favourable outcomes}}{\text{total equally likely outcomes}}'; r.step('Probability', L(ans)); r.done(ans); r.check('Probability bounds', bool(ans>=0 and ans<=1))

def h_circle(r, op, raw):
    vals = [P(v.strip()) for v in raw.split(',') if v.strip()]; r.topic='Class 10 · Circle Geometry'
    if op == 'circumference':
        if len(vals)!=1: raise ValueError('Use circumference radius, for example: circumference 7')
        ans=2*sp.pi*vals[0]; r.formula=r'C=2\pi r'
    elif op == 'circle area':
        if len(vals)!=1: raise ValueError('Use circle area radius, for example: circle area 7')
        ans=sp.pi*vals[0]**2; r.formula=r'A=\pi r^2'
    elif op == 'arc length':
        if len(vals)!=2: raise ValueError('Use arc length radius, central_angle_degrees')
        rad,deg=vals; ans=sp.pi*rad*deg/180; r.formula=r'L=\frac{\theta}{360^\circ}\,2\pi r'
    elif op == 'sector area':
        if len(vals)!=2: raise ValueError('Use sector area radius, central_angle_degrees')
        rad,deg=vals; ans=sp.pi*rad**2*deg/360; r.formula=r'A=\frac{\theta}{360^\circ}\,\pi r^2'
    elif op == 'chord length':
        if len(vals)!=2: raise ValueError('Use chord length radius, central_angle_degrees')
        rad,deg=vals; ans=2*rad*sp.sin(sp.pi*deg/360); r.formula=r'c=2r\sin(\theta/2)'
    else: raise ValueError('Unsupported circle calculation.')
    if any(v.is_negative for v in vals[:1]): raise ValueError('Radius cannot be negative.')
    r.step('Given values', ', '.join(L(v) for v in vals)); r.step('Substitute in the circle formula', L(ans)); r.done(ans); r.check('Formula substitution', True, 'Exact symbolic result.')

def h_function(r, raw):
    m=re.match(r'^([a-z])\s*\(([^()]*)\)\s*=\s*(.+?)\s+at\s+(.+)$',raw,re.I)
    if not m: raise ValueError('Use function notation like f(x)=x^2+2x at 3.')
    _,vn,expr,point=m.groups(); var=sp.Symbol(vn); ex=P(expr); a=P(point); ans=sp.simplify(ex.subs(var,a))
    r.topic='Class 10 · Functions and Graphs'; r.formula=r'f(a)=\text{substitute }x=a\text{ into }f(x)'; r.step('Function',L(sp.Eq(sp.Function('f')(var),ex))); r.step('Substitute input',L(sp.Eq(var,a))); r.step('Evaluate',L(sp.Eq(sp.Function('f')(a),ans))); r.done(ans); r.check('Direct substitution',sp.simplify(ex.subs(var,a)-ans)==0)

def h_trig(r, raw):
    ex=P(raw); ans=sp.trigsimp(sp.simplify(ex)); r.topic='Class 10 · Trigonometry'; r.formula=r'\sin^2\theta+\cos^2\theta=1'; r.step('Trigonometric expression',L(ex)); r.step('Apply exact trigonometric simplification',L(ans)); r.done(ans); r.check('Symbolic simplification identity',sp.trigsimp(ex-ans)==0)


CMD = [('complex', r'^(conjugate|modulus|real part|imaginary part|argument)\s+(.+)$'), ('vector', r'^(vector add|vector subtract|dot product|magnitude|unit vector|angle between)\s+(.+)$'), ('statistics', r'^(mean|median|mode|range|variance|sample variance|standard deviation)\s+(?:of\s+)?(.+)$'), ('probability', r'^probability\s+(?:of\s+)?(.+)$'), ('circle', r'^(circumference|circle area|arc length|sector area|chord length)\s+(.+)$'), ('function', r'^(?:evaluate )?function\s+(.+)$'), ('trig', r'^(?:trig simplify|trigonometry)\s+(.+)$'), ('inequality', r'^solve\s+(.+?(?:<=|>=|<|>).+)$'), ('series', r'^series\s+(.+)$'), ('partial', r'^(?:(second|third)\s+)?(?:partial derivative(?: of)?|differentiate partially)\s+(.+?)\s+with respect to\s+([a-z])$'), ('ode', r"^(?:solve|dsolve)\s+(.*y\s*'.*)$"), ('diff', r'^(?:(second|third)\s+)?(?:derivative(?: of)?|differentiate|diff|d/dx(?: of)?)\s+(.+)$'),
       ('int', r'^(?:integrate|integral(?: of)?|antiderivative(?: of)?)\s+(.+)$'), ('limit', r'^lim(?:it)?\s+(.+)$'),
       ('factor', r'^factor(?:i[sz]e)?\s+(.+)$'), ('expand', r'^expand\s+(.+)$'), ('simplify', r'^simplify\s+(.+)$'),
       ('matrix', r'^(det(?:erminant)?|inverse|eigenvalues|rank|transpose|rref|reduced row-echelon form|null ?space|column space|row space|lu(?: decomposition)?|qr(?: decomposition)?|svd|condition number)(?: of)?\s+(.+)$'), ('nt', r'^(gcd|lcm|isprime|factorint|prime factors?(?: of)?)\s*\(?([\d,\s]+)\)?$'),
       ('solve', r'^solve\s+(.+)$')]
h_factor = lambda r, e: h_alg(r, 'factor', e); h_expand = lambda r, e: h_alg(r, 'expand', e); h_simplify = lambda r, e: h_alg(r, 'simplify', e)

def h_partial_route(r, w, e, vn):
    return h_partial(r, vn, e, {'second': '2', 'third': '3'}.get((w or '').lower(), '1'))

def route(r, q):
    q = q.strip()
    m=re.match(r'^(pythagoras|heron area|triangle area|distance|midpoint|slope|rectangle area|rectangle perimeter|parallelogram area|cube volume|cube surface area|cuboid volume|cuboid surface area|cylinder volume|cylinder surface area|cone volume|sphere volume|sphere surface area)\s+(.+)$',q,re.I)
    if m: return h_geometry(r,m.group(1).lower(),m.group(2))
    m=re.match(r'^(permutation|combination)\s+(.+)$',q,re.I)
    if m: return h_counting(r,m.group(1).lower(),m.group(2))
    m=re.match(r'^grouped (?:statistics|mean)\s+(.+)$',q,re.I)
    if m: return h_grouped_stats(r,m.group(1))
    m=re.match(r'^convert\s+(.+)$',q,re.I)
    if m: return h_unit_convert(r,m.group(1))
    m=re.match(r'^prove\s+(.+)$',q,re.I)
    if m: return h_proof(r,m.group(1))
    m=re.match(r'^word problem:?\s*(.+)$',q,re.I)
    if m: return h_word(r,m.group(1))
    m=re.match(r'^physics\s+(.+)$',q,re.I)
    if m: return h_physics(r,m.group(1))
    # Friendly named-matrix workflow: definitions followed by A-B / A+B / A*B.
    # This is handled locally, so matrix arithmetic never depends on an AI provider.
    definitions = dict((name.upper(), literal) for name, literal in re.findall(
        r'^\s*([A-Za-z])\s*=\s*(\[\[.*?\]\])\s*$', q, re.M))
    operation = re.search(r'(?:find|calculate|compute|evaluate)?\s*([A-Za-z])\s*([+*\-])\s*([A-Za-z])\s*$', q, re.I)
    if operation and len(definitions) >= 2:
        left_name, symbol, right_name = operation.groups()
        left, right = definitions.get(left_name.upper()), definitions.get(right_name.upper())
        if left is not None and right is not None:
            op = {'+': 'add', '-': 'subtract', '*': 'multiply'}[symbol]
            return h_matrix_binary(r, op, left, right)
    m = re.match(r'^matrix\s+(add|subtract|multiply)\s+(\[\[.*?\]\])\s+and\s+(\[\[.*?\]\])$', q, re.I)
    if m: return h_matrix_binary(r, *m.groups())
    m = re.match(r'^(conjugate|modulus|real part|imaginary part|argument)\s+(.+)$', q, re.I)
    if m: return h_complex(r, m.group(1).lower(), m.group(2))
    m = re.match(r'^(vector add|vector subtract|dot product|magnitude|unit vector|angle between)\s+(.+)$', q, re.I)
    if m:
        op, rest = m.groups(); op=op.lower(); op={'vector add':'add','vector subtract':'subtract','dot product':'dot','unit vector':'unit','angle between':'angle'}.get(op,op)
        parts = re.split(r'\s+and\s+', rest, maxsplit=1, flags=re.I)
        return h_vector(r, op, parts[0], parts[1] if len(parts)>1 else None)
    m = re.match(r'^(mean|median|mode|range|variance|sample variance|standard deviation)\s+(?:of\s+)?(.+)$', q, re.I)
    if m: return h_statistics(r, m.group(1).lower(), m.group(2))
    m = re.match(r'^probability\s+(?:of\s+)?(.+)$', q, re.I)
    if m: return h_probability(r, m.group(1))
    m = re.match(r'^(circumference|circle area|arc length|sector area|chord length)\s+(.+)$', q, re.I)
    if m: return h_circle(r, m.group(1).lower(), m.group(2))
    m = re.match(r'^(?:evaluate )?function\s+(.+)$', q, re.I)
    if m: return h_function(r, m.group(1))
    m = re.match(r'^(?:trig simplify|trigonometry)\s+(.+)$', q, re.I)
    if m: return h_trig(r, m.group(1))
    sm = re.match(r'^sum\s+(.+?)\s+from\s+([a-z])\s*=\s*(-?\d+)\s+to\s+(-?\d+)$', q.strip(), re.I)
    if sm: return h_sum(r, *sm.groups())
    for name, pat in CMD:
        m = re.match(pat, q.strip(), re.I)
        if m: return (h_partial_route if name == 'partial' else globals()['h_' + name])(r, *m.groups())
    return h_solve(r, q) if '=' in q else h_eval(r, q)

def llm_command(q):
    """Use Gemini only to translate wording into a safe command; SymPy performs all maths."""
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        return None
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', model):
        raise ValueError('Invalid GEMINI_MODEL setting.')
    prompt = (
        'Translate the user mathematics request into exactly ONE command for the Zentrix SymPy solver. '
        'Never solve it, explain it, use markdown, or return anything except the command. '
        'Supported forms: solve <equation>; derivative of <expression>; integrate <expression>; '
        'limit <expression> as x-><value>; factor <expression>; expand <expression>; simplify <expression>; '
        'determinant of [[...]]; inverse of [[...]]; eigenvalues of [[...]]; rank of [[...]]; rref of [[...]]; nullspace of [[...]]; column space of [[...]]; row space of [[...]]; LU/QR/SVD decomposition; condition number. '
        'Physics commands: physics force mass=... acceleration=...; physics work force=... distance=...; '
        'physics power work=... time=...; physics ohms voltage=... resistance=...; '
        'physics kinetic energy mass=... velocity=...; physics potential energy mass=... height=...; '
        'physics momentum mass=... velocity=...; physics density mass=... volume=...; '
        'physics pressure force=... area=...; physics speed distance=... time=...; '
        'physics acceleration initial_velocity=... final_velocity=... time=.... '
        'For two matrices use exactly: matrix add [[...]] and [[...]], matrix subtract [[...]] and [[...]], '
        'or matrix multiply [[...]] and [[...]]. If the input defines A and B on separate lines and asks A-B, '
        'copy both matrix literals into matrix subtract [[...]] and [[...]]. Preserve every entry and sign. '
        'Use * for multiplication and ** for powers. Do not invent missing information. '
        'If the request cannot be expressed, return UNSUPPORTED.\n\nUser request:\n' + q
    )
    body = json.dumps({
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0, 'maxOutputTokens': 220},
    }).encode('utf-8')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    req = urllib.request.Request(url, data=body, headers={
        'x-goog-api-key': key,
        'content-type': 'application/json',
    }, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.load(response)
    except Exception as exc:
        # Do not expose the key or provider response body in the UI/log message.
        raise RuntimeError(f'Gemini request failed ({type(exc).__name__}).') from None
    try:
        command = data['candidates'][0]['content']['parts'][0]['text'].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError('Gemini returned no usable command.') from None
    command = re.sub(r'^```(?:\w+)?\s*|\s*```$', '', command).strip()
    command = command.splitlines()[0].strip()
    if command.upper() == 'UNSUPPORTED' or not command or len(command) > 1000:
        return None
    return command

def h_ladder_word_problem(q):
    """Solve the common ladder-against-wall right-triangle word problem and emit a scaled diagram spec."""
    if not re.search(r'\b(ladder|wall)\b', q, re.I) or not re.search(r'\b(wall|ground|foot|base)\b', q, re.I):
        return None
    # Recognise the two explicitly stated lengths, in their order of appearance.
    vals = re.findall(r'(?<![A-Za-z])(-?\d+(?:\.\d+)?)\s*(?:m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)?\b', q, re.I)
    if len(vals) < 2:
        return None
    a, b = map(sp.Rational, vals[:2])
    if a <= 0 or b <= 0:
        return None
    # In a ladder problem, the ladder length is the hypotenuse and the distance
    # from wall is the horizontal leg. The usual wording gives them in that order.
    hyp, base = max(a, b), min(a, b)
    if base >= hyp:
        return None
    height2 = sp.simplify(hyp**2 - base**2)
    height = sp.sqrt(height2)
    r = Res(q); r.topic = 'Geometry: ladder and right triangle'
    r.formula = r'a^2+b^2=c^2'
    r.step('Identify the right triangle', r'c=\text{ladder},\quad a=\text{distance from wall},\quad b=\text{height}')
    r.step('Apply Pythagoras’ theorem', L(sp.Eq(sp.Symbol('b')**2 + base**2, hyp**2)))
    r.step('Substitute the known lengths', L(sp.Eq(sp.Symbol('b')**2, height2)))
    r.step('Find the missing height', L(sp.Eq(sp.Symbol('b'), height)))
    unit_match = re.search(r'\b(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)\b', q, re.I)
    unit = unit_match.group(1).lower() if unit_match else 'units'
    def fmt(v):
        return str(sp.simplify(v))
    r.done(height, f'{fmt(height)} {unit}')
    r.ans = L(height) + r'\,\text{' + unit + '}'
    r.diagram = {'type':'right_triangle','title':'Ladder against a wall','base':float(base),'height':float(height),'hypotenuse':float(hyp),'base_label':f'{fmt(base)} {unit}','height_label':f'{fmt(height)} {unit}','hypotenuse_label':f'{fmt(hyp)} {unit}','right_angle':True}
    r.check('Pythagorean theorem', sp.simplify(base**2 + height**2 - hyp**2) == 0, 'The two perpendicular sides and ladder length satisfy a² + b² = c².')
    return r.out()

def h_rectangle_word_problem(q):
    if not re.search(r'\b(rectangle|rectangular|garden|field|room)\b', q, re.I) or not re.search(r'\b(area|perimeter|around|fence|cover)\b', q, re.I):
        return None
    vals = re.findall(r'(?<![A-Za-z])(-?\d+(?:\.\d+)?)\s*(?:m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)?\b', q, re.I)
    if len(vals) < 2:
        return None
    length, width = map(sp.Rational, vals[:2])
    if length <= 0 or width <= 0:
        return None
    unit_match = re.search(r'\b(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)\b', q, re.I)
    unit = unit_match.group(1).lower() if unit_match else 'units'
    r = Res(q); r.topic = 'Geometry: rectangle'
    if re.search(r'\b(perimeter|around|fence)\b', q, re.I) and not re.search(r'\b(area)\b', q, re.I):
        value = 2*(length+width); label='perimeter'; formula=r'P=2(l+w)'
        r.step('Identify the length and width', L(sp.Eq(sp.Symbol('l'),length))+r',\quad '+L(sp.Eq(sp.Symbol('w'),width)))
        r.step('Apply the perimeter formula', L(sp.Eq(sp.Symbol('P'),2*(length+width))))
    else:
        value=length*width; label='area'; formula=r'A=l\times w'
        r.step('Identify the length and width', L(sp.Eq(sp.Symbol('l'),length))+r',\quad '+L(sp.Eq(sp.Symbol('w'),width)))
        r.step('Apply the area formula', L(sp.Eq(sp.Symbol('A'),length*width)))
    r.formula=formula; r.done(value,f'{value} {unit}'+('²' if label=='area' else ''))
    r.ans=L(value)+r'\,\text{'+unit+('^2' if label=='area' else '')+'}'
    r.diagram={'type':'rectangle','title':'Rectangular shape','length':float(length),'width':float(width),'length_label':f'{length} {unit}','width_label':f'{width} {unit}'}
    r.check('Formula evaluation', value == (length*width if label=='area' else 2*(length+width)), 'The result matches the selected rectangle formula.')
    return r.out()

def h_triangle_word_problem(q):
    if not re.search(r"\b(triangle|triangular)\b", q, re.I) or not re.search(r"\b(area|base|height)\b", q, re.I):
        return None
    vals = re.findall(r"(?<![A-Za-z])(\d+(?:\.\d+)?)\s*(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)?\b", q, re.I)
    if len(vals) < 2: return None
    base, height = (sp.Rational(vals[i][0]) for i in (0,1))
    if base <= 0 or height <= 0: return None
    units=[v[1].lower() for v in vals[:2] if v[1]]
    norm=lambda u: 'cm' if u.startswith('centi') or u=='cm' else 'm' if u.startswith('met') or u=='m' else 'ft' if u in ('ft','feet') else u
    if len(units)==2 and norm(units[0])!=norm(units[1]): return None
    unit=norm(units[0]) if units else 'units'
    area=sp.simplify(base*height/2)
    r=Res(q); r.topic='Geometry: triangle'; r.formula=r'A=\frac12 bh'
    r.step('Identify the base and perpendicular height', f'base = {base}; height = {height}')
    r.step('Apply the triangle area formula', L(sp.Eq(sp.Symbol('A'), sp.Rational(1,2)*base*height)))
    r.done(area, f'{area} {unit}²'); r.ans=L(area)+r'\,\text{'+unit+r'^2}'
    r.diagram={'type':'triangle','title':'Triangle','base':float(base),'height':float(height),'base_label':f'{base} {unit}','height_label':f'{height} {unit}'}
    r.check('Area formula', area == base*height/2, 'Area equals one-half base times perpendicular height.')
    return r.out()

def h_circle_word_problem(q):
    if not re.search(r"\b(circle|circular)\b", q, re.I) or not re.search(r"\b(area|circumference|around)\b", q, re.I): return None
    m=re.search(r"\b(radius|diameter)\b[^0-9-]*(-?\d+(?:\.\d+)?)\s*(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)?", q, re.I)
    if not m: return None
    kind,val,unit=m.groups(); radius=sp.Rational(val)
    if radius<=0: return None
    if kind.lower()=='diameter': radius/=2
    unit=(unit or 'units').lower()
    unit='cm' if unit.startswith('centi') or unit=='cm' else 'm' if unit.startswith('met') or unit=='m' else 'ft' if unit in ('ft','feet') else unit
    is_area=bool(re.search(r"\barea\b",q,re.I)); result=sp.simplify(sp.pi*radius**2 if is_area else 2*sp.pi*radius)
    r=Res(q); r.topic='Geometry: circle'; r.formula=r'A=\pi r^2' if is_area else r'C=2\pi r'
    r.step('Identify the radius', f'radius = {radius} {unit}')
    r.step('Substitute into the circle formula', L(sp.Eq(sp.Symbol('A' if is_area else 'C'),result)))
    r.done(result, f'{sp.N(result,6)} {unit}'+('²' if is_area else ''))
    r.ans=L(result)+r'\,\text{'+unit+(r'^2' if is_area else '')+'}'
    r.diagram={'type':'circle','title':'Circle','radius':float(radius),'radius_label':f'{radius} {unit}'}
    r.check('Circle formula', True, 'The result matches the selected circle formula.')
    return r.out()

def solve(q):
    q, err = q.strip(), 'unknown error'
    try:
        word_result = h_ladder_word_problem(q)
        if word_result is None:
            word_result = h_rectangle_word_problem(q)
        if word_result is None:
            word_result = h_triangle_word_problem(q)
        if word_result is None:
            word_result = h_circle_word_problem(q)
        if word_result is not None:
            return word_result
    except Exception:
        pass
    ambiguous_relationship = bool(re.search(r'\b(?:a number|number)\s+increased by\b', q, re.I) and re.search(r'\b(?:times?|twice)\b.*\bdecreased by\b', q, re.I) and not re.search(r'\bdifference between\b', q, re.I))
    for cmd in (q, None):
        if cmd is None and (q.lower().startswith('word problem') or ambiguous_relationship):
            break
        r = Res(q)
        try:
            if cmd is None:
                cmd = llm_command(q)
                if not cmd: break
                r.warn.append(f'Interpreted as: {cmd}')
            route(r, cmd); return r.out()
        except Exception as e: err = f'{type(e).__name__}: {e}'
    r = Res(q); r.ans, r.text = r'\text{Could not solve this reliably}', 'unsolved'
    r.warn.append(f'I could not parse or solve this reliably ({err}). Rephrase it, e.g. "solve x^2-4=0", or configure GEMINI_API_KEY for optional natural-language interpretation.')
    return r.out()
       ('solve', r'^solve\s+(.+)$')]
h_factor = lambda r, e: h_alg(r, 'factor', e); h_expand = lambda r, e: h_alg(r, 'expand', e); h_simplify = lambda r, e: h_alg(r, 'simplify', e)

def h_partial_route(r, w, e, vn):
    return h_partial(r, vn, e, {'second': '2', 'third': '3'}.get((w or '').lower(), '1'))

def route(r, q):
    q = q.strip()
    m=re.match(r'^(pythagoras|heron area|triangle area|distance|midpoint|slope|rectangle area|rectangle perimeter|parallelogram area|cube volume|cube surface area|cuboid volume|cuboid surface area|cylinder volume|cylinder surface area|cone volume|sphere volume|sphere surface area)\s+(.+)$',q,re.I)
    if m: return h_geometry(r,m.group(1).lower(),m.group(2))
    m=re.match(r'^(permutation|combination)\s+(.+)$',q,re.I)
    if m: return h_counting(r,m.group(1).lower(),m.group(2))
    m=re.match(r'^grouped (?:statistics|mean)\s+(.+)$',q,re.I)
    if m: return h_grouped_stats(r,m.group(1))
    m=re.match(r'^convert\s+(.+)$',q,re.I)
    if m: return h_unit_convert(r,m.group(1))
    m=re.match(r'^prove\s+(.+)$',q,re.I)
    if m: return h_proof(r,m.group(1))
    m=re.match(r'^word problem:?\s*(.+)$',q,re.I)
    if m: return h_word(r,m.group(1))
    m=re.match(r'^physics\s+(.+)$',q,re.I)
    if m: return h_physics(r,m.group(1))
    # Friendly named-matrix workflow: definitions followed by A-B / A+B / A*B.
    # This is handled locally, so matrix arithmetic never depends on an AI provider.
    definitions = dict((name.upper(), literal) for name, literal in re.findall(
        r'^\s*([A-Za-z])\s*=\s*(\[\[.*?\]\])\s*$', q, re.M))
    operation = re.search(r'(?:find|calculate|compute|evaluate)?\s*([A-Za-z])\s*([+*\-])\s*([A-Za-z])\s*$', q, re.I)
    if operation and len(definitions) >= 2:
        left_name, symbol, right_name = operation.groups()
        left, right = definitions.get(left_name.upper()), definitions.get(right_name.upper())
        if left is not None and right is not None:
            op = {'+': 'add', '-': 'subtract', '*': 'multiply'}[symbol]
            return h_matrix_binary(r, op, left, right)
    m = re.match(r'^matrix\s+(add|subtract|multiply)\s+(\[\[.*?\]\])\s+and\s+(\[\[.*?\]\])$', q, re.I)
    if m: return h_matrix_binary(r, *m.groups())
    m = re.match(r'^(conjugate|modulus|real part|imaginary part|argument)\s+(.+)$', q, re.I)
    if m: return h_complex(r, m.group(1).lower(), m.group(2))
    m = re.match(r'^(vector add|vector subtract|dot product|magnitude|unit vector|angle between)\s+(.+)$', q, re.I)
    if m:
        op, rest = m.groups(); op=op.lower(); op={'vector add':'add','vector subtract':'subtract','dot product':'dot','unit vector':'unit','angle between':'angle'}.get(op,op)
        parts = re.split(r'\s+and\s+', rest, maxsplit=1, flags=re.I)
        return h_vector(r, op, parts[0], parts[1] if len(parts)>1 else None)
    m = re.match(r'^(mean|median|mode|range|variance|sample variance|standard deviation)\s+(?:of\s+)?(.+)$', q, re.I)
    if m: return h_statistics(r, m.group(1).lower(), m.group(2))
    m = re.match(r'^probability\s+(?:of\s+)?(.+)$', q, re.I)
    if m: return h_probability(r, m.group(1))
    m = re.match(r'^(circumference|circle area|arc length|sector area|chord length)\s+(.+)$', q, re.I)
    if m: return h_circle(r, m.group(1).lower(), m.group(2))
    m = re.match(r'^(?:evaluate )?function\s+(.+)$', q, re.I)
    if m: return h_function(r, m.group(1))
    m = re.match(r'^(?:trig simplify|trigonometry)\s+(.+)$', q, re.I)
    if m: return h_trig(r, m.group(1))
    sm = re.match(r'^sum\s+(.+?)\s+from\s+([a-z])\s*=\s*(-?\d+)\s+to\s+(-?\d+)$', q.strip(), re.I)
    if sm: return h_sum(r, *sm.groups())
    for name, pat in CMD:
        m = re.match(pat, q.strip(), re.I)
        if m: return (h_partial_route if name == 'partial' else globals()['h_' + name])(r, *m.groups())
    return h_solve(r, q) if '=' in q else h_eval(r, q)

def llm_command(q):
    """Use Gemini only to translate wording into a safe command; SymPy performs all maths."""
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        return None
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', model):
        raise ValueError('Invalid GEMINI_MODEL setting.')
    prompt = (
        'Translate the user mathematics request into exactly ONE command for the Zentrix SymPy solver. '
        'Never solve it, explain it, use markdown, or return anything except the command. '
        'Supported forms: solve <equation>; derivative of <expression>; integrate <expression>; '
        'limit <expression> as x-><value>; factor <expression>; expand <expression>; simplify <expression>; '
        'determinant of [[...]]; inverse of [[...]]; eigenvalues of [[...]]; rank of [[...]]; rref of [[...]]; nullspace of [[...]]; column space of [[...]]; row space of [[...]]; LU/QR/SVD decomposition; condition number. '
        'Physics commands: physics force mass=... acceleration=...; physics work force=... distance=...; '
        'physics power work=... time=...; physics ohms voltage=... resistance=...; '
        'physics kinetic energy mass=... velocity=...; physics potential energy mass=... height=...; '
        'physics momentum mass=... velocity=...; physics density mass=... volume=...; '
        'physics pressure force=... area=...; physics speed distance=... time=...; '
        'physics acceleration initial_velocity=... final_velocity=... time=.... '
        'For two matrices use exactly: matrix add [[...]] and [[...]], matrix subtract [[...]] and [[...]], '
        'or matrix multiply [[...]] and [[...]]. If the input defines A and B on separate lines and asks A-B, '
        'copy both matrix literals into matrix subtract [[...]] and [[...]]. Preserve every entry and sign. '
        'Use * for multiplication and ** for powers. Do not invent missing information. '
        'If the request cannot be expressed, return UNSUPPORTED.\n\nUser request:\n' + q
    )
    body = json.dumps({
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0, 'maxOutputTokens': 220},
    }).encode('utf-8')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    req = urllib.request.Request(url, data=body, headers={
        'x-goog-api-key': key,
        'content-type': 'application/json',
    }, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.load(response)
    except Exception as exc:
        # Do not expose the key or provider response body in the UI/log message.
        raise RuntimeError(f'Gemini request failed ({type(exc).__name__}).') from None
    try:
        command = data['candidates'][0]['content']['parts'][0]['text'].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError('Gemini returned no usable command.') from None
    command = re.sub(r'^```(?:\w+)?\s*|\s*```$', '', command).strip()
    command = command.splitlines()[0].strip()
    if command.upper() == 'UNSUPPORTED' or not command or len(command) > 1000:
        return None
    return command

def h_ladder_word_problem(q):
    """Solve the common ladder-against-wall right-triangle word problem and emit a scaled diagram spec."""
    if not re.search(r'\b(ladder|wall)\b', q, re.I) or not re.search(r'\b(wall|ground|foot|base)\b', q, re.I):
        return None
    # Recognise the two explicitly stated lengths, in their order of appearance.
    vals = re.findall(r'(?<![A-Za-z])(-?\d+(?:\.\d+)?)\s*(?:m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)?\b', q, re.I)
    if len(vals) < 2:
        return None
    a, b = map(sp.Rational, vals[:2])
    if a <= 0 or b <= 0:
        return None
    # In a ladder problem, the ladder length is the hypotenuse and the distance
    # from wall is the horizontal leg. The usual wording gives them in that order.
    hyp, base = max(a, b), min(a, b)
    if base >= hyp:
        return None
    height2 = sp.simplify(hyp**2 - base**2)
    height = sp.sqrt(height2)
    r = Res(q); r.topic = 'Geometry: ladder and right triangle'
    r.formula = r'a^2+b^2=c^2'
    r.step('Identify the right triangle', r'c=\text{ladder},\quad a=\text{distance from wall},\quad b=\text{height}')
    r.step('Apply Pythagoras’ theorem', L(sp.Eq(sp.Symbol('b')**2 + base**2, hyp**2)))
    r.step('Substitute the known lengths', L(sp.Eq(sp.Symbol('b')**2, height2)))
    r.step('Find the missing height', L(sp.Eq(sp.Symbol('b'), height)))
    unit_match = re.search(r'\b(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)\b', q, re.I)
    unit = unit_match.group(1).lower() if unit_match else 'units'
    def fmt(v):
        return str(sp.simplify(v))
    r.done(height, f'{fmt(height)} {unit}')
    r.ans = L(height) + r'\,\text{' + unit + '}'
    r.diagram = {'type':'right_triangle','title':'Ladder against a wall','base':float(base),'height':float(height),'hypotenuse':float(hyp),'base_label':f'{fmt(base)} {unit}','height_label':f'{fmt(height)} {unit}','hypotenuse_label':f'{fmt(hyp)} {unit}','right_angle':True}
    r.check('Pythagorean theorem', sp.simplify(base**2 + height**2 - hyp**2) == 0, 'The two perpendicular sides and ladder length satisfy a² + b² = c².')
    return r.out()

def h_rectangle_word_problem(q):
    if not re.search(r'\b(rectangle|rectangular|garden|field|room)\b', q, re.I) or not re.search(r'\b(area|perimeter|around|fence|cover)\b', q, re.I):
        return None
    vals = re.findall(r'(?<![A-Za-z])(-?\d+(?:\.\d+)?)\s*(?:m|metres?|meters?|cm|centimetres?|centimeters?|ft|feet)?\b', q, re.I)
    if len(vals) < 2:
        return None
    length, width = map(sp.Rational, vals[:2])
    if length <= 0 or width <= 0:
        return None
    unit_match = re.search(r'\b(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)\b', q, re.I)
    unit = unit_match.group(1).lower() if unit_match else 'units'
    r = Res(q); r.topic = 'Geometry: rectangle'
    if re.search(r'\b(perimeter|around|fence)\b', q, re.I) and not re.search(r'\b(area)\b', q, re.I):
        value = 2*(length+width); label='perimeter'; formula=r'P=2(l+w)'
        r.step('Identify the length and width', L(sp.Eq(sp.Symbol('l'),length))+r',\quad '+L(sp.Eq(sp.Symbol('w'),width)))
        r.step('Apply the perimeter formula', L(sp.Eq(sp.Symbol('P'),2*(length+width))))
    else:
        value=length*width; label='area'; formula=r'A=l\times w'
        r.step('Identify the length and width', L(sp.Eq(sp.Symbol('l'),length))+r',\quad '+L(sp.Eq(sp.Symbol('w'),width)))
        r.step('Apply the area formula', L(sp.Eq(sp.Symbol('A'),length*width)))
    r.formula=formula; r.done(value,f'{value} {unit}'+('²' if label=='area' else ''))
    r.ans=L(value)+r'\,\text{'+unit+('^2' if label=='area' else '')+'}'
    r.diagram={'type':'rectangle','title':'Rectangular shape','length':float(length),'width':float(width),'length_label':f'{length} {unit}','width_label':f'{width} {unit}'}
    r.check('Formula evaluation', value == (length*width if label=='area' else 2*(length+width)), 'The result matches the selected rectangle formula.')
    return r.out()

def h_triangle_word_problem(q):
    if not re.search(r"\b(triangle|triangular)\b", q, re.I) or not re.search(r"\b(area|base|height)\b", q, re.I):
        return None
    vals = re.findall(r"(?<![A-Za-z])(\d+(?:\.\d+)?)\s*(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)?\b", q, re.I)
    if len(vals) < 2: return None
    base, height = (sp.Rational(vals[i][0]) for i in (0,1))
    if base <= 0 or height <= 0: return None
    units=[v[1].lower() for v in vals[:2] if v[1]]
    norm=lambda u: 'cm' if u.startswith('centi') or u=='cm' else 'm' if u.startswith('met') or u=='m' else 'ft' if u in ('ft','feet') else u
    if len(units)==2 and norm(units[0])!=norm(units[1]): return None
    unit=norm(units[0]) if units else 'units'
    area=sp.simplify(base*height/2)
    r=Res(q); r.topic='Geometry: triangle'; r.formula=r'A=\frac12 bh'
    r.step('Identify the base and perpendicular height', f'base = {base}; height = {height}')
    r.step('Apply the triangle area formula', L(sp.Eq(sp.Symbol('A'), sp.Rational(1,2)*base*height)))
    r.done(area, f'{area} {unit}²'); r.ans=L(area)+r'\,\text{'+unit+r'^2}'
    r.diagram={'type':'triangle','title':'Triangle','base':float(base),'height':float(height),'base_label':f'{base} {unit}','height_label':f'{height} {unit}'}
    r.check('Area formula', area == base*height/2, 'Area equals one-half base times perpendicular height.')
    return r.out()

def h_circle_word_problem(q):
    if not re.search(r"\b(circle|circular)\b", q, re.I) or not re.search(r"\b(area|circumference|around)\b", q, re.I): return None
    m=re.search(r"\b(radius|diameter)\b[^0-9-]*(-?\d+(?:\.\d+)?)\s*(cm|centimetres?|centimeters?|m|metres?|meters?|ft|feet)?", q, re.I)
    if not m: return None
    kind,val,unit=m.groups(); radius=sp.Rational(val)
    if radius<=0: return None
    if kind.lower()=='diameter': radius/=2
    unit=(unit or 'units').lower()
    unit='cm' if unit.startswith('centi') or unit=='cm' else 'm' if unit.startswith('met') or unit=='m' else 'ft' if unit in ('ft','feet') else unit
    is_area=bool(re.search(r"\barea\b",q,re.I)); result=sp.simplify(sp.pi*radius**2 if is_area else 2*sp.pi*radius)
    r=Res(q); r.topic='Geometry: circle'; r.formula=r'A=\pi r^2' if is_area else r'C=2\pi r'
    r.step('Identify the radius', f'radius = {radius} {unit}')
    r.step('Substitute into the circle formula', L(sp.Eq(sp.Symbol('A' if is_area else 'C'),result)))
    r.done(result, f'{sp.N(result,6)} {unit}'+('²' if is_area else ''))
    r.ans=L(result)+r'\,\text{'+unit+(r'^2' if is_area else '')+'}'
    r.diagram={'type':'circle','title':'Circle','radius':float(radius),'radius_label':f'{radius} {unit}'}
    r.check('Circle formula', True, 'The result matches the selected circle formula.')
    return r.out()

def solve(q):
    q, err = q.strip(), 'unknown error'
    try:
        word_result = h_ladder_word_problem(q)
        if word_result is None:
            word_result = h_rectangle_word_problem(q)
        if word_result is None:
            word_result = h_triangle_word_problem(q)
        if word_result is None:
            word_result = h_circle_word_problem(q)
        if word_result is not None:
            return word_result
    except Exception:
        pass
    ambiguous_relationship = bool(re.search(r'\b(?:a number|number)\s+increased by\b', q, re.I) and re.search(r'\b(?:times?|twice)\b.*\bdecreased by\b', q, re.I) and not re.search(r'\bdifference between\b', q, re.I))
    for cmd in (q, None):
        if cmd is None and (q.lower().startswith('word problem') or ambiguous_relationship):
            break
        r = Res(q)
        try:
            if cmd is None:
                cmd = llm_command(q)
                if not cmd: break
                r.warn.append(f'Interpreted as: {cmd}')
            route(r, cmd); return r.out()
        except Exception as e: err = f'{type(e).__name__}: {e}'
    r = Res(q); r.ans, r.text = r'\text{Could not solve this reliably}', 'unsolved'
    r.warn.append(f'I could not parse or solve this reliably ({err}). Rephrase it, e.g. "solve x^2-4=0", or configure GEMINI_API_KEY for optional natural-language interpretation.')
    return r.out()
