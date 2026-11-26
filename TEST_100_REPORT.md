# Zentrix AI v1.5.0 — 100-question benchmark report

**Overall result: 100/100 correct.** All 100 returned a passing solver check, included solution steps, and supplied a formula or method label.

| Section | Correct | Passing checks | Steps | Formula/method |
|---|---:|---:|---:|---:|
| Probability (25) | 25/25 | 25/25 | 25/25 | 25/25 |
| Advanced algebra (25) | 25/25 | 25/25 | 25/25 | 25/25 |
| Grade 8–10 maths (30) | 30/30 | 30/30 | 30/30 | 30/30 |
| Difficult MCQs (20) | 20/20 | 20/20 | 20/20 | 20/20 |

## Verification transparency
A passing-check result means Zentrix returned a check and that check passed. It does **not** mean every answer was independently proved. The suite used 83 rule-based checks, 9 symbolic checks, and 8 numerical checks.

## Complete test questions and results

### Probability (25)
| # | Level | Question sent to Zentrix | Expected answer | Result |
|---:|---|---|---|---|
| 1 | rule-based | `probability 1/2` | `1/2` | PASS — `1/2` |
| 2 | rule-based | `probability 3/4` | `3/4` | PASS — `3/4` |
| 3 | rule-based | `probability 2 out of 5` | `2/5` | PASS — `2/5` |
| 4 | rule-based | `probability 7/10` | `7/10` | PASS — `7/10` |
| 5 | rule-based | `probability 0/8` | `0` | PASS — `0` |
| 6 | rule-based | `probability 8/8` | `1` | PASS — `1` |
| 7 | rule-based | `probability 5 out of 20` | `1/4` | PASS — `1/4` |
| 8 | rule-based | `probability 9/12` | `3/4` | PASS — `3/4` |
| 9 | rule-based | `probability exactly 2 heads in 5 fair coin tosses` | `5/16` | PASS — `5/16` |
| 10 | rule-based | `probability exactly 3 heads in 6 fair coin tosses` | `5/16` | PASS — `5/16` |
| 11 | rule-based | `probability exactly 0 heads in 4 fair coin tosses` | `1/16` | PASS — `1/16` |
| 12 | rule-based | `probability exactly 4 heads in 6 fair coin tosses` | `15/64` | PASS — `15/64` |
| 13 | rule-based | `combination 10,3` | `120` | PASS — `120` |
| 14 | rule-based | `permutation 7,3` | `210` | PASS — `210` |
| 15 | rule-based | `probability 6/36` | `1/6` | PASS — `1/6` |
| 16 | rule-based | `probability 15/52` | `15/52` | PASS — `15/52` |
| 17 | rule-based | `probability 11 out of 40` | `11/40` | PASS — `11/40` |
| 18 | rule-based | `probability exactly 5 heads in 10 fair coin tosses` | `63/256` | PASS — `63/256` |
| 19 | rule-based | `probability exactly 1 heads in 8 fair coin tosses` | `1/32` | PASS — `1/32` |
| 20 | rule-based | `probability exactly 7 heads in 12 fair coin tosses` | `99/512` | PASS — `99/512` |
| 21 | rule-based | `probability 1/1000` | `1/1000` | PASS — `1/1000` |
| 22 | rule-based | `probability 0.125` | `0.125` | PASS — `0.125000000000000` |
| 23 | rule-based | `probability 21/28` | `3/4` | PASS — `3/4` |
| 24 | rule-based | `combination 20,10` | `184756` | PASS — `184756` |
| 25 | rule-based | `permutation 9,4` | `3024` | PASS — `3024` |

### Advanced algebra (25)
| # | Level | Question sent to Zentrix | Expected answer | Result |
|---:|---|---|---|---|
| 26 | rule-based | `solve 7*x-19=30` | `7` | PASS — `[7]` |
| 27 | rule-based | `solve 3*x+11=2*x+17` | `6` | PASS — `[6]` |
| 28 | rule-based | `solve x^2-9*x+20=0` | `[4, 5]` | PASS — `[4, 5]` |
| 29 | symbolic | `factor x^2-16` | `(x - 4)*(x + 4)` | PASS — `(x - 4)*(x + 4)` |
| 30 | symbolic | `expand (2*x-3)^3` | `8*x**3 - 36*x**2 + 54*x - 27` | PASS — `8*x**3 - 36*x**2 + 54*x - 27` |
| 31 | symbolic | `simplify (x^2-9)/(x-3)` | `x + 3` | PASS — `x + 3` |
| 32 | rule-based | `solve 2*x^2-7*x+3=0` | `[1/2, 3]` | PASS — `[1/2, 3]` |
| 33 | rule-based | `solve x^3-6*x^2+11*x-6=0` | `[1, 2, 3]` | PASS — `[1, 2, 3]` |
| 34 | rule-based | `solve x^4-5*x^2+4=0` | `[-2, -1, 1, 2]` | PASS — `[-2, -1, 1, 2]` |
| 35 | rule-based | `solve x^2+4=0` | `[-2*I, 2*I]` | PASS — `[-2*I, 2*I]` |
| 36 | rule-based | `solve 2*x+3*y=12, x-y=1` | `{x: 3, y: 2}` | PASS — `{x: 3, y: 2}` |
| 37 | rule-based | `solve x+y+z=6, 2*x-y+z=3, x+2*y-z=2` | `{x: 1, y: 2, z: 3}` | PASS — `{x: 1, y: 2, z: 3}` |
| 38 | rule-based | `solve x^2-5*x+6>0` | `Union(Interval.open(-oo, 2), Interval.open(3, oo))` | PASS — `Union(Interval.open(-oo, 2), Interval.open(3, oo))` |
| 39 | rule-based | `solve x^2+2*x-8<=0` | `Interval(-4, 2)` | PASS — `Interval(-4, 2)` |
| 40 | rule-based | `inverse of [[2,1],[5,3]]` | `Matrix([[3, -1], [-5, 2]])` | PASS — `Matrix([[3, -1], [-5, 2]])` |
| 41 | rule-based | `eigenvalues of [[4,1],[2,3]]` | `{5: 1, 2: 1}` | PASS — `{5: 1, 2: 1}` |
| 42 | rule-based | `determinant of [[3,2,1],[0,4,5],[0,0,2]]` | `24` | PASS — `24` |
| 43 | rule-based | `matrix multiply [[1,2],[3,4]] and [[2,0],[1,2]]` | `Matrix([[4, 4], [10, 8]])` | PASS — `Matrix([[4, 4], [10, 8]])` |
| 44 | symbolic | `partial derivative of x^2*y+sin(x*y) with respect to x` | `2*x*y + y*cos(x*y)` | PASS — `2*x*y + y*cos(x*y)` |
| 45 | numerical | `derivative of exp(x)*sin(x^2)` | `exp(x)*(2*x*cos(x**2)+sin(x**2))` | PASS — `(2*x*cos(x**2) + sin(x**2))*exp(x)` |
| 46 | numerical | `integrate x^3-2*x from 0 to 2` | `0` | PASS — `0` |
| 47 | numerical | `limit (x^2-1)/(x-1) as x->1` | `2` | PASS — `2` |
| 48 | rule-based | `series sin(x) around x=0 to 6` | `x - x**3/6 + x**5/120` | PASS — `x**5/120 - x**3/6 + x` |
| 49 | rule-based | `word problem: A number increased by 7 is three times the difference between the number and 5. Find the number.` | `11` | PASS — `11` |
| 50 | rule-based | `solve (x^2-1)/(x-1)=3 for x` | `2` | PASS — `[2]` |

### Grade 8–10 maths (30)
| # | Level | Question sent to Zentrix | Expected answer | Result |
|---:|---|---|---|---|
| 51 | numerical | `25% of 240` | `60` | PASS — `60` |
| 52 | numerical | `144/12` | `12` | PASS — `12` |
| 53 | symbolic | `simplify 18/24` | `3/4` | PASS — `3/4` |
| 54 | rule-based | `gcd 84,126` | `42` | PASS — `42` |
| 55 | rule-based | `lcm 12,18` | `36` | PASS — `36` |
| 56 | rule-based | `pythagoras 3,4` | `5` | PASS — `5` |
| 57 | rule-based | `rectangle area 12,5` | `60` | PASS — `60 units²` |
| 58 | rule-based | `rectangle perimeter 12,5` | `34` | PASS — `34 units` |
| 59 | rule-based | `triangle area 10,8` | `40` | PASS — `40 units²` |
| 60 | rule-based | `cube volume 4` | `64` | PASS — `64` |
| 61 | rule-based | `mean of 2,4,6,8,10` | `6` | PASS — `6` |
| 62 | rule-based | `median of 3,7,9,11,20` | `9` | PASS — `9` |
| 63 | rule-based | `standard deviation of 2,4,4,4,5,5,7,9` | `2` | PASS — `2` |
| 64 | rule-based | `slope 1,2,5,10` | `2` | PASS — `2` |
| 65 | rule-based | `midpoint 2,4,8,10` | `(5, 7)` | PASS — `(5, 7)` |
| 66 | rule-based | `distance 0,0,3,4` | `5` | PASS — `5` |
| 67 | rule-based | `circle area 7` | `49*pi` | PASS — `49*pi` |
| 68 | rule-based | `circumference 7` | `14*pi` | PASS — `14*pi` |
| 69 | rule-based | `function f(x)=x^2+2*x at 3` | `15` | PASS — `15` |
| 70 | symbolic | `trig simplify sin(x)^2+cos(x)^2` | `1` | PASS — `1` |
| 71 | rule-based | `heron area 13,14,15` | `84` | PASS — `84` |
| 72 | rule-based | `sphere volume 3` | `36*pi` | PASS — `36*pi` |
| 73 | rule-based | `cylinder volume 2,5` | `20*pi` | PASS — `20*pi` |
| 74 | rule-based | `convert 2.5 km to m` | `2500` | PASS — `2500 m` |
| 75 | rule-based | `dot product [1,2,3] and [4,5,6]` | `32` | PASS — `32` |
| 76 | rule-based | `physics force mass=5 acceleration=2` | `10` | PASS — `10 N` |
| 77 | rule-based | `physics kinetic energy mass=1200 velocity=20` | `240000` | PASS — `240000 J` |
| 78 | rule-based | `solve 5*(x-2)=3*x+8` | `9` | PASS — `[9]` |
| 79 | symbolic | `factor 4*x^2-25` | `(2*x - 5)*(2*x + 5)` | PASS — `(2*x - 5)*(2*x + 5)` |
| 80 | rule-based | `solve 2*x/3+4=10` | `9` | PASS — `[9]` |

### Difficult MCQs (20)
| # | MCQ question | Options | Correct option | Zentrix result |
|---:|---|---|---|---|
| 81 | `solve 3*x^2-12*x+9=0` | A. x=1 or x=3; B. x=-1 or x=3; C. x=1 or x=4; D. x=0 or x=3 | **A** | PASS — `[1, 3]` |
| 82 | `factor x^3-8` | A. (x-2)(x^2+2x+4); B. (x+2)(x^2-2x+4); C. (x-2)(x^2-2x+4); D. (x+2)(x^2+2x+4) | **A** | PASS — `(x - 2)*(x**2 + 2*x + 4)` |
| 83 | `solve 2*x^2+5*x-3=0` | A. x=-3 or x=1/2; B. x=3 or x=-1/2; C. x=-1 or x=3/2; D. x=1 or x=-3/2 | **A** | PASS — `[-3, 1/2]` |
| 84 | `determinant of [[2,1,0],[1,3,2],[0,2,4]]` | A. 10; B. 12; C. 14; D. 18 | **B** | PASS — `12` |
| 85 | `eigenvalues of [[2,0],[0,7]]` | A. λ=2,7; B. λ=3,6; C. λ=-2,7; D. λ=2,5 | **A** | PASS — `{2: 1, 7: 1}` |
| 86 | `solve x^2-2*x-15=0` | A. x=-3 or x=5; B. x=-5 or x=3; C. x=-3 or x=4; D. x=3 or x=5 | **A** | PASS — `[-3, 5]` |
| 87 | `derivative of ln(x^2+1)` | A. 2x/(x^2+1); B. x/(x^2+1); C. 2/(x^2+1); D. 2x/(x^2-1) | **A** | PASS — `2*x/(x**2 + 1)` |
| 88 | `integrate 6*x^2-4*x+1` | A. 2x^3-2x^2+x+C; B. 2x^3+2x^2+x+C; C. 6x^3-4x^2+x+C; D. 2x^3-4x^2+x+C | **A** | PASS — `2*x**3 - 2*x**2 + x + C` |
| 89 | `limit (x^2-4)/(x-2) as x->2` | A. 2; B. 3; C. 4; D. 6 | **C** | PASS — `4` |
| 90 | `solve x^2+1=0` | A. x=±i; B. x=±1; C. x=±2i; D. x=0 | **A** | PASS — `[-I, I]` |
| 91 | `solve x^3-2*x^2-x+2=0` | A. x=-1,1,2; B. x=-2,1,2; C. x=-1,1,3; D. x=-2,2,3 | **A** | PASS — `[-1, 1, 2]` |
| 92 | `inverse of [[1,2],[3,7]]` | A. [[7,-2],[-3,1]]; B. [[7,2],[3,1]]; C. [[1,-2],[-3,7]]; D. [[7,-3],[-2,1]] | **A** | PASS — `Matrix([[7, -2], [-3, 1]])` |
| 93 | `combination 12,4` | A. 495; B. 220; C. 660; D. 990 | **A** | PASS — `495` |
| 94 | `permutation 8,3` | A. 336; B. 56; C. 168; D. 512 | **A** | PASS — `336` |
| 95 | `probability exactly 3 heads in 8 fair coin tosses` | A. 7/32; B. 5/32; C. 9/32; D. 7/64 | **A** | PASS — `7/32` |
| 96 | `partial derivative of x^2*y^3 with respect to y` | A. 3x^2*y^2; B. 2x^2*y; C. x^2*y^2; D. 3x*y^2 | **A** | PASS — `3*x**2*y**2` |
| 97 | `solve 2*x+3*y=7, 4*x-y=5` | A. x=11/7,y=9/7; B. x=9/7,y=11/7; C. x=2,y=1; D. x=1,y=2 | **A** | PASS — `{x: 11/7, y: 9/7}` |
| 98 | `pythagoras 5,12` | A. 13; B. 12; C. 14; D. 17 | **A** | PASS — `13` |
| 99 | `sphere surface area 4` | A. 64π; B. 16π; C. 32π; D. 128π | **A** | PASS — `64*pi` |
| 100 | `word problem: A number increased by 4 is twice the difference between the number and 2. Find the number.` | A. 8; B. 6; C. 10; D. 12 | **A** | PASS — `8` |

## Methodology and limits
- Each prompt was submitted directly to Zentrix’s local `engine.solve()` function.
- Answers were compared against predefined expected results; the harness also recorded checks, working steps, and formula/method labels.
- For the 20 MCQs, the calculated answer was matched against the keyed option. The report includes all choices, but arbitrary MCQ option extraction from free-form text or photographs was not tested.
- This is a finite benchmark. A 100/100 score on these selected questions is not a guarantee that every unseen problem will be solved correctly.