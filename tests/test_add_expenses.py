import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from helpers import split_expense

def test_valid_split_three_members():
    members = [{"id": 1}, {"id": 2}, {"id": 3}]
    loans = split_expense(90, members, 1)
    assert loans == [(1, 2, 30), (1, 3, 30)]

def test_group_too_small():
    members = [{"id": 1}]
    with pytest.raises(ValueError, match="At least two members"):
        split_expense(50, members, 1)

def test_amount_not_positive():
    members = [{"id": 1}, {"id": 2}]
    with pytest.raises(ValueError, match="Amount must be positive"):
        split_expense(0, members, 1)

def test_payer_not_in_group():
    members = [{"id": 1}, {"id": 2}]
    with pytest.raises(ValueError, match="Payer must be a member"):
        split_expense(50, members, 99)

def test_fractional_split():
    members = [{"id": 1}, {"id": 2}, {"id": 3}]
    loans = split_expense(100, members, 1)
    assert loans == [(1, 2, pytest.approx(33.3333, rel=1e-4)),
                     (1, 3, pytest.approx(33.3333, rel=1e-4))]


