import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
import engine
def test_all_engine_regressions():
    CASES = [("2+3*4", "14"), ("1/3+1/4", "7/12"), ("15% of 80", "12"), ("1/0", "undefined"), ("sqrt(2)*sqrt(8)", "4"),
     ("2x+3=7", "[2]"), ("x^2-5x+6=0", "[2, 3]"), ("x^2+1=0", "I"), ("x^3-6x^2+11x-6=0", "[1, 2, 3]"), ("x+1=x+2", "No solution"),
     ("2(x+1)=2x+2", "Infinitely many"), ("1/x=0", "No solution"), ("solve x+y=3, x-y=1", "x: 2"), ("solve x+y=1, x+y=2", "No solution"),
     ("factor x^2-9", "(x - 3)*(x + 3)"), ("expand (x+1)^3", "x**3 + 3*x**2 + 3*x + 1"), ("derivative of x^3*sin(x)", "cos(x)"),
     ("second derivative of x^4", "12*x**2"), ("integrate x^2", "x**3/3"), ("integrate x*exp(x)", "exp(x)"), ("integrate x^2 from 0 to 3", "9"),
     ("integrate sin(x) from 0 to pi", "2"), ("limit sin(x)/x as x->0", "1"), ("limit (1+1/x)^x as x->oo", "E"), ("limit 1/x as x->0", "does not exist"),
     ("matrix subtract [[1,2],[-1,0]] and [[3,2],[1,-1]]", "Matrix([[-2, 0], [-2, 1]])"), ("matrix add [[1,2],[3,4]] and [[5,6],[7,8]]", "Matrix([[6, 8], [10, 12]])"), ("matrix multiply [[1,2],[3,4]] and [[5,6],[7,8]]", "Matrix([[19, 22], [43, 50]])"), ("det of [[1,2],[3,4]]", "-2"), ("inverse of [[2,0],[0,4]]", "1/2"), ("eigenvalues of [[2,0],[0,3]]", "2"), ("rank of [[1,2],[2,4]]", "1"),
     ("solve y'' + y = 0", "C1"), ("gcd(48, 18)", "6"), ("prime factors of 360", "2**3"), ("isprime 97", "True"), ("solve x^2 < 4", "Interval.open(-2, 2)"), ("series sin(x) around x=0 to 7", "x**5/120 - x**3/6 + x"), ("partial derivative of x^2*y + sin(y) with respect to x", "2*x*y"), ("sum k^2 from k=1 to 10", "385") ]
    # Parser regression and security checks: supported shorthand must remain valid,
    # while arbitrary Python syntax must be rejected before evaluation.
    for expr, expected in [("2x+3", "2*x + 3"), ("2(x+1)", "2*x + 2"),
                           ("1e-3", "0.001"), ("sqrt(2)", "sqrt(2)")]:
        got = engine.P(expr)
        assert engine.sp.simplify(got - engine.P(expected)) == 0, (expr, got, expected)
    for malicious in ["__import__('os').system('echo compromised')",
                       "open('/tmp/zentrix-pwned','w')", "x.__class__",
                       "(lambda: 1)()"]:
        try:
            engine.P(malicious)
        except (ValueError, SyntaxError):
            pass
        else:
            raise AssertionError(f'Unsafe expression unexpectedly accepted: {malicious}')

    # Punjab Board Class 10 (2026-27) topic coverage regression cases.
    CLASS10_CASES = [
        ('modulus 3+4i', '5'), ('conjugate 3+4i', '3 - 4*I'),
        ('solve x^2-5x+6=0', '[2, 3]'), ('solve x^2 < 9', 'Interval.open(-3, 3)'),
        ('det of [[1,2],[3,4]]', '-2'), ('inverse of [[2,0],[0,4]]', '1/2'),
        ('function f(x)=x^2+2x at 3', '15'), ('factor x^2-9', '(x - 3)*(x + 3)'),
        ('vector add [1,2] and [3,4]', '4'), ('dot product [1,2] and [3,4]', '11'),
        ('magnitude [3,4]', '5'), ('trig simplify sin(x)^2+cos(x)^2', '1'),
        ('mean of [2,4,6,8]', '5'), ('median [1,7,3,5]', '4'),
        ('mode of [1,2,2,3]', '2'), ('variance of [2,4,6]', '8/3'),
        ('probability 3 out of 52', '3/52'), ('circumference 7', '14*pi'),
        ('circle area 7', '49*pi'), ('arc length 7,90', '7*pi/2'),
        ('sector area 7,90', '49*pi/4'), ('chord length 7,60', '7'),
    ]
    for q, want in CLASS10_CASES:
        o = engine.solve(q)
        assert want in o['answer_text'], (q, o['answer_text'], o['warnings'])
        assert not any(c['passed'] is False for c in o['checks']), (q, o['checks'])
    print(f'{len(CLASS10_CASES)}/{len(CLASS10_CASES)} Class 10 coverage tests passed')


    # Named matrix definitions and direct operations must work without Gemini.
    named_matrix = engine.solve('A = [[1,2],[-1,0]]\nB = [[3,2],[1,-1]]\nfind A-B')
    assert 'Matrix([[-2, 0], [-2, 1]])' in named_matrix['answer_text'], named_matrix
    assert named_matrix['verified'], named_matrix
    transpose = engine.solve('transpose of [[1,2],[3,4]]')
    assert 'Matrix([[1, 3], [2, 4]])' in transpose['answer_text'], transpose

    bad = 0
    for q, want in CASES:
        o = engine.solve(q); fails = [c['name'] for c in o['checks'] if c['passed'] is False]
        ok = want in o['answer_text'] and not fails and o['verified']
        bad += not ok; print(('PASS' if ok else 'FAIL'), q, '->', o['answer_text'][:60], ('| failed checks: %s' % fails) if fails else '')
    print(f'\n{len(CASES) - bad}/{len(CASES)} passed'); assert bad == 0, f'{bad} regression cases failed'


def test_numeric_cross_check_uses_negative_and_fractional_domain_points():
    assert engine.same(engine.P('x'), engine.P('x')) is True
    assert engine.same(engine.P('x'), engine.P('x^2')) is False
    assert engine.same(engine.P('1/3'), engine.P('0.3333333333333333333333333333333333333333')) is True



def test_multivariable_research_gradient_hessian_and_minimum():
    from research_engine import analyze_scalar_field
    result = analyze_scalar_field("x^2 + x*y + y^2", ["x", "y"], {"x": 0, "y": 0})
    assert result["gradient"] == ["2*x + y", "x + 2*y"]
    assert result["hessian"] == [["2", "1"], ["1", "2"]]
    assert result["stationary"] is True
    assert result["classification"] == "strict_local_minimum"
    assert result["hessian_eigenvalues"] == [1.0, 3.0]


def test_multivariable_research_detects_saddle_and_nonstationary_points():
    from research_engine import analyze_scalar_field
    saddle = analyze_scalar_field("x*y", ["x", "y"], {"x": 0, "y": 0})
    assert saddle["classification"] == "saddle_point"
    nonstationary = analyze_scalar_field("x^2 + y", ["x", "y"], {"x": 0, "y": 0})
    assert nonstationary["classification"] == "not_stationary"


def test_multivariable_research_quadratic_taylor_and_three_variables():
    from research_engine import analyze_scalar_field
    result = analyze_scalar_field("x^2 + y^2 + z^2", ["x", "y", "z"], {"x": 1, "y": 2, "z": 3})
    assert "h_x**2" in result["quadratic_taylor"]
    assert result["classification"] == "not_stationary"
    assert len(result["hessian"]) == 3


def test_vector_field_jacobian_divergence_and_conservativity():
    from research_engine import analyze_vector_field
    result = analyze_vector_field(["x^2*y", "x*y^2"], ["x", "y"], {"x": 1, "y": 2})
    assert result["jacobian"] == [["2*x*y", "x**2"], ["y**2", "2*x*y"]]
    assert result["divergence"] == "4*x*y"
    assert result["divergence_at_point"] == "8.00000000000000000000000000000"
    assert result["locally_conservative_test"] is False


def test_vector_field_three_dimensional_curl_and_divergence():
    from research_engine import analyze_vector_field
    result = analyze_vector_field(["x", "y", "z"], ["x", "y", "z"], {"x": 1, "y": 2, "z": 3})
    assert result["curl"] == ["0", "0", "0"]
    assert result["divergence"] == "3"
    assert result["locally_conservative_test"] is True


def test_research_engine_rejects_invalid_variables_points_and_unsafe_input():
    import pytest
    from research_engine import analyze_scalar_field, analyze_vector_field
    with pytest.raises(ValueError):
        analyze_scalar_field("__import__('os').system('whoami')", ["x"], {"x": 0})
    with pytest.raises(ValueError):
        analyze_scalar_field("x+y", ["x", "x"], {"x": 0})
    with pytest.raises(ValueError):
        analyze_scalar_field("x+y", ["x", "y"], {"x": 0})
    with pytest.raises(ValueError):
        analyze_vector_field(["x"], ["x", "y"], {"x": 0, "y": 0})
