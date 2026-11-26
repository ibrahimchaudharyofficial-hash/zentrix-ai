import sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.engine import solve

cases=[]
def add(section, level, q, expected, note='', options=None, correct_choice=None):
    cases.append({'section':section,'level':level,'q':q,'expected':expected,'note':note,'options':options or [],'correct_choice':correct_choice})

# 25 probability: 8 easy, 9 medium, 8 hard/extreme
prob=[
('easy','probability 1/2','1/2'),('easy','probability 3/4','3/4'),('easy','probability 2 out of 5','2/5'),('easy','probability 7/10','7/10'),('easy','probability 0/8','0'),('easy','probability 8/8','1'),('easy','probability 5 out of 20','1/4'),('easy','probability 9/12','3/4'),
('medium','probability exactly 2 heads in 5 fair coin tosses','5/16'),('medium','probability exactly 3 heads in 6 fair coin tosses','5/16'),('medium','probability exactly 0 heads in 4 fair coin tosses','1/16'),('medium','probability exactly 4 heads in 6 fair coin tosses','15/64'),('medium','combination 10,3','120'),('medium','permutation 7,3','210'),('medium','probability 6/36','1/6'),('medium','probability 15/52','15/52'),('medium','probability 11 out of 40','11/40'),
('hard','probability exactly 5 heads in 10 fair coin tosses','63/256'),('hard','probability exactly 1 heads in 8 fair coin tosses','1/32'),('hard','probability exactly 7 heads in 12 fair coin tosses','99/512'),('hard','probability 1/1000','1/1000'),('hard','probability 0.125','0.125'),('hard','probability 21/28','3/4'),('hard','combination 20,10','184756'),('hard','permutation 9,4','3024')]
for level,q,e in prob:add('Probability (25)',level,q,e)

alg=[
('medium','solve 7*x-19=30','7'),('medium','solve 3*x+11=2*x+17','6'),('medium','solve x^2-9*x+20=0','[4, 5]'),('medium','factor x^2-16','(x - 4)*(x + 4)'),('medium','expand (2*x-3)^3','8*x**3 - 36*x**2 + 54*x - 27'),('medium','simplify (x^2-9)/(x-3)','x + 3'),
('hard','solve 2*x^2-7*x+3=0','[1/2, 3]'),('hard','solve x^3-6*x^2+11*x-6=0','[1, 2, 3]'),('hard','solve x^4-5*x^2+4=0','[-2, -1, 1, 2]'),('hard','solve x^2+4=0','[-2*I, 2*I]'),('hard','solve 2*x+3*y=12, x-y=1','{x: 3, y: 2}'),('hard','solve x+y+z=6, 2*x-y+z=3, x+2*y-z=2','{x: 1, y: 2, z: 3}'),
('hard','solve x^2-5*x+6>0','Union(Interval.open(-oo, 2), Interval.open(3, oo))'),('hard','solve x^2+2*x-8<=0','Interval(-4, 2)'),('hard','inverse of [[2,1],[5,3]]','Matrix([[3, -1], [-5, 2]])'),('hard','eigenvalues of [[4,1],[2,3]]','{5: 1, 2: 1}'),('hard','determinant of [[3,2,1],[0,4,5],[0,0,2]]','24'),('hard','matrix multiply [[1,2],[3,4]] and [[2,0],[1,2]]','Matrix([[4, 4], [10, 8]])'),
('extreme','partial derivative of x^2*y+sin(x*y) with respect to x','2*x*y + y*cos(x*y)'),('extreme','derivative of exp(x)*sin(x^2)','exp(x)*(2*x*cos(x**2)+sin(x**2))'),('extreme','integrate x^3-2*x from 0 to 2','0'),('extreme','limit (x^2-1)/(x-1) as x->1','2'),('extreme','series sin(x) around x=0 to 6','x - x**3/6 + x**5/120'),('extreme','word problem: A number increased by 7 is three times the difference between the number and 5. Find the number.','11'),('extreme','solve (x^2-1)/(x-1)=3 for x','2')]
for level,q,e in alg:add('Advanced algebra (25)',level,q,e)

basic=[
('easy','25% of 240','60'),('easy','144/12','12'),('easy','simplify 18/24','3/4'),('easy','gcd 84,126','42'),('easy','lcm 12,18','36'),('easy','pythagoras 3,4','5'),('easy','rectangle area 12,5','60'),('easy','rectangle perimeter 12,5','34'),('easy','triangle area 10,8','40'),('easy','cube volume 4','64'),
('medium','mean of 2,4,6,8,10','6'),('medium','median of 3,7,9,11,20','9'),('medium','standard deviation of 2,4,4,4,5,5,7,9','2'),('medium','slope 1,2,5,10','2'),('medium','midpoint 2,4,8,10','(5, 7)'),('medium','distance 0,0,3,4','5'),('medium','circle area 7','49*pi'),('medium','circumference 7','14*pi'),('medium','function f(x)=x^2+2*x at 3','15'),('medium','trig simplify sin(x)^2+cos(x)^2','1'),
('hard','heron area 13,14,15','84'),('hard','sphere volume 3','36*pi'),('hard','cylinder volume 2,5','20*pi'),('hard','convert 2.5 km to m','2500'),('hard','dot product [1,2,3] and [4,5,6]','32'),('hard','physics force mass=5 acceleration=2','10'),('hard','physics kinetic energy mass=1200 velocity=20','240000'),('hard','solve 5*(x-2)=3*x+8','9'),('hard','factor 4*x^2-25','(2*x - 5)*(2*x + 5)'),('hard','solve 2*x/3+4=10','9')]
for level,q,e in basic:add('Grade 8–10 maths (30)',level,q,e)

mcq=[
('hard','solve 3*x^2-12*x+9=0','[1, 3]'),('hard','factor x^3-8','(x - 2)*(x**2 + 2*x + 4)'),('hard','solve 2*x^2+5*x-3=0','[-3, 1/2]'),('hard','determinant of [[2,1,0],[1,3,2],[0,2,4]]','12'),('hard','eigenvalues of [[2,0],[0,7]]','{2: 1, 7: 1}'),('hard','solve x^2-2*x-15=0','[-3, 5]'),('hard','derivative of ln(x^2+1)','2*x/(x**2 + 1)'),('hard','integrate 6*x^2-4*x+1','2*x**3 - 2*x**2 + x + C'),('hard','limit (x^2-4)/(x-2) as x->2','4'),('hard','solve x^2+1=0','[-I, I]'),
('extreme','solve x^3-2*x^2-x+2=0','[-1, 1, 2]'),('extreme','inverse of [[1,2],[3,7]]','Matrix([[7, -2], [-3, 1]])'),('extreme','combination 12,4','495'),('extreme','permutation 8,3','336'),('extreme','probability exactly 3 heads in 8 fair coin tosses','7/32'),('extreme','partial derivative of x^2*y^3 with respect to y','3*x**2*y**2'),('extreme','solve 2*x+3*y=7, 4*x-y=5','{x: 11/7, y: 9/7}'),('extreme','pythagoras 5,12','13'),('extreme','sphere surface area 4','64*pi'),('extreme','word problem: A number increased by 4 is twice the difference between the number and 2. Find the number.','8')]
mcq_options=[
['x=1 or x=3','x=-1 or x=3','x=1 or x=4','x=0 or x=3'],
['(x-2)(x^2+2x+4)','(x+2)(x^2-2x+4)','(x-2)(x^2-2x+4)','(x+2)(x^2+2x+4)'],
['x=-3 or x=1/2','x=3 or x=-1/2','x=-1 or x=3/2','x=1 or x=-3/2'],
['10','12','14','18'],
['λ=2,7','λ=3,6','λ=-2,7','λ=2,5'],
['x=-3 or x=5','x=-5 or x=3','x=-3 or x=4','x=3 or x=5'],
['2x/(x^2+1)','x/(x^2+1)','2/(x^2+1)','2x/(x^2-1)'],
['2x^3-2x^2+x+C','2x^3+2x^2+x+C','6x^3-4x^2+x+C','2x^3-4x^2+x+C'],
['2','3','4','6'],
['x=±i','x=±1','x=±2i','x=0'],
['x=-1,1,2','x=-2,1,2','x=-1,1,3','x=-2,2,3'],
['[[7,-2],[-3,1]]','[[7,2],[3,1]]','[[1,-2],[-3,7]]','[[7,-3],[-2,1]]'],
['495','220','660','990'],
['336','56','168','512'],
['7/32','5/32','9/32','7/64'],
['3x^2*y^2','2x^2*y','x^2*y^2','3x*y^2'],
['x=11/7,y=9/7','x=9/7,y=11/7','x=2,y=1','x=1,y=2'],
['13','12','14','17'],
['64π','16π','32π','128π'],
['8','6','10','12']]
correct_indices=[0,0,0,1,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0]
for i,(level,q,e) in enumerate(mcq,1):
    opts=mcq_options[i-1]
    add('Difficult MCQs (20)',level,q,e,f'MCQ-{i}',opts,'ABCD'[correct_indices[i-1]])

assert len(cases)==100,len(cases)

def norm(s):
    return re.sub(r'\s+',' ',str(s)).strip().lower().replace('**','^').replace(' ','')

def answer_ok(result, expected):
    got=str(result.get('answer_text',''))
    # Compare expression outputs through SymPy parser where possible; matrices/dicts handled by string normalization.
    if expected.startswith('Matrix(') or expected.startswith('{') or expected.startswith('[') or expected.startswith('('):
        return norm(got)==norm(expected) or norm(expected) in norm(got)
    try:
        from backend.engine import P
        import sympy as sp
        a=P(got); b=P(expected)
        return sp.simplify(a-b)==0
    except Exception:
        return norm(got)==norm(expected) or norm(expected) in norm(got)

results=[]
for i,c in enumerate(cases,1):
    r=solve(c['q'])
    ok=answer_ok(r,c['expected'])
    steps=len(r.get('steps') or [])
    formula=bool(r.get('formula'))
    verified=bool(r.get('verified'))
    results.append({**c,'number':i,'ok':ok,'answer':r.get('answer_text'),'steps':steps,'formula':formula,'verified':verified,'level':r.get('verification_level'),'warnings':r.get('warnings',[])})

for section in ['Probability (25)','Advanced algebra (25)','Grade 8–10 maths (30)','Difficult MCQs (20)']:
    subset=[x for x in results if x['section']==section]
    print(f'{section}: {sum(x["ok"] for x in subset)}/{len(subset)} correct; {sum(x["verified"] for x in subset)}/{len(subset)} verified; {sum(x["steps"]>0 for x in subset)}/{len(subset)} with steps; {sum(x["formula"] for x in subset)}/{len(subset)} with formula')
print('TOTAL:',sum(x['ok'] for x in results),'/100 correct')
print('VERIFIED:',sum(x['verified'] for x in results),'/100')
print('STEPS:',sum(x['steps']>0 for x in results),'/100')
print('FORMULAS:',sum(x['formula'] for x in results),'/100')
print('\nFAILURES:')
for x in results:
    if not x['ok']:
        print(x['number'],x['section'],x['q'],'EXPECTED=',x['expected'],'GOT=',x['answer'],'WARN=',x['warnings'])
(Path(__file__).resolve().parent / 'TEST_100_RESULTS.json').write_text(json.dumps(results,indent=2,default=str),encoding='utf-8')
