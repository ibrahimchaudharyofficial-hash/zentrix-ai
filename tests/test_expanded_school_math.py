"""Regression tests for v0.8 geometry, mensuration, statistics and utilities."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
import engine

CASES = [
    ('pythagoras 3,4', '5'), ('heron area 3,4,5', '6'),
    ('triangle area 10,6', '30'), ('distance 0,0,3,4', '5'),
    ('midpoint 0,2,4,6', '(2, 4)'), ('slope 1,2,3,6', '2'),
    ('rectangle area 5,4', '20'), ('rectangle perimeter 5,4', '18'),
    ('parallelogram area 5,4', '20'), ('cube volume 3', '27'),
    ('cube surface area 3', '54'), ('cuboid volume 2,3,4', '24'),
    ('cuboid surface area 2,3,4', '52'), ('cylinder volume 2,5', '20*pi'),
    ('cylinder surface area 2,5', '28*pi'), ('cone volume 3,4', '12*pi'),
    ('sphere volume 3', '36*pi'), ('sphere surface area 3', '36*pi'),
    ('permutation 5,2', '20'), ('combination 5,2', '10'),
    ('grouped mean values [10,20,30] frequencies [2,3,1]', '55/3'),
    ('convert 2.5 km to m', '2500 m'),
    ('prove (x+1)^2 = x^2+2*x+1', 'Identity verified'),
    ('word problem: A car travels 120 km in 2 hours; find speed', '60'),
    ('word problem: simple interest on 1000 at 5% for 2 years', '100'),
    ('word problem: increase 200 by 15%', '230'),
    ('word problem: decrease 200 by 15%', '170'),
    ('word problem: sum of two consecutive integers is 25', '(12, 13)'),
]
for question, expected in CASES:
    result=engine.solve(question)
    assert expected in result['answer_text'], (question,result['answer_text'],result['warnings'])
    assert result['verified'], (question,result['checks'],result['warnings'])
    assert not any(c.get('passed') is False for c in result['checks']), (question,result['checks'])
print(f'{len(CASES)}/{len(CASES)} expanded school mathematics cases passed')
