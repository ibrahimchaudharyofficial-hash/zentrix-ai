"""Cross-grade Pakistan school-maths regression benchmark (representative, not exhaustive)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
import engine

# Grade 6-9 foundations + common Grade 10 and extension topics. Each item is a
# deterministic problem with an independently specified expected answer fragment.
CASES = [
    # Number, operations, fractions, decimals, percentages, powers and roots
    ('3/4+2/3', '17/12'), ('sqrt(225)', '15'), ('(3^2)^3', '729'),
    ('15% of 80', '12'), ('1/3+1/4', '7/12'), ('2^5*2^3', '256'),
    # Factors, multiples and number properties
    ('gcd(84,126)', '42'), ('lcm(12,18)', '36'), ('prime factors of 84', '2**2 * 3**1 * 7**1'),
    ('isprime 97', 'True'),
    # Algebraic expressions, identities, factorisation and equations
    ('factor x^2+7x+12', '(x + 3)*(x + 4)'),
    ('expand (2x-3)^2', '4*x**2 - 12*x + 9'),
    ('simplify (x^2-9)/(x-3)', 'x + 3'),
    ('solve 4x+9=25', '[4]'), ('solve x^2-7x+10=0', '[2, 5]'),
    ('solve x+y=7, x-y=1', 'x: 4'), ('solve 2*x<10', '5'),
    # Trigonometry and functions
    ('sin(pi/6)', '1/2'), ('cos(pi/3)', '1/2'), ('tan(pi/4)', '1'),
    ('trig simplify sin(x)^2+cos(x)^2', '1'),
    ('function f(x)=3*x+2 at -1', '-1'),
    # Geometry/circle formula computations supported by the current command set
    ('circumference 5', '10*pi'), ('circle area 7', '49*pi'),
    ('arc length 7,90', '7*pi/2'), ('sector area 4,90', '4*pi'),
    # Vectors, matrices and data handling
    ('vector add [1,2] and [3,4]', '4'), ('dot product [1,2] and [3,4]', '11'),
    ('det of [[2,3],[1,4]]', '5'), ('rank of [[1,2],[2,4]]', '1'),
    ('mean of [4,6,8,10]', '7'), ('median [9,1,5,3]', '4'),
    ('mode [2,2,3,4]', '2'), ('probability 1/4', '1/4'),
    # Advanced capabilities already present in engine
    ('derivative of x^3', '3*x**2'), ('integrate 2*x', 'x**2'),
    ('limit sin(x)/x as x->0', '1'),
    ('series cos(x) around x=0 to 6', 'x**4/24 - x**2/2 + 1'),
]

for question, expected in CASES:
    result = engine.solve(question)
    assert expected in result['answer_text'], (question, result['answer_text'], result['warnings'])
    assert result['verified'], (question, result['checks'], result['warnings'])
    assert not any(c.get('passed') is False for c in result['checks']), (question, result['checks'])

print(f'{len(CASES)}/{len(CASES)} cross-grade curriculum benchmark cases passed')
