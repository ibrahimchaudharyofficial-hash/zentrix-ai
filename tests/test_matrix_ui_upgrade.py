import os


def test_matrix_lab_exposes_advanced_operations():
    path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'static', 'index.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()
    for operation in ('rref', 'nullspace', 'column space', 'row space', 'lu of', 'qr of', 'svd of', 'condition number'):
        assert operation in html
    assert 'askMatrixSingle' in html
