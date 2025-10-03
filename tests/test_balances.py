import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from helpers import calculate_balances

def test_balances_simple_case():
    members = [{"id": 1}, {"id": 2}, {"id": 3}]
    loans = [
        {"payer_id": 1, "payee_id": 2, "amount": 30},
        {"payer_id": 1, "payee_id": 3, "amount": 30},
    ]
    balances = calculate_balances(loans, 1, members)
    assert balances == {1: 0, 2: 30, 3: 30}

def test_balances_user_as_payee():
    members = [{"id": 1}, {"id": 2}]
    loans = [{"payer_id": 1, "payee_id": 2, "amount": 50}]
    balances = calculate_balances(loans, 2, members)
    assert balances == {1: -50, 2: 0}

def test_balances_circular_debts():
    members = [{"id": 1}, {"id": 2}]
    loans = [
        {"payer_id": 1, "payee_id": 2, "amount": 40},
        {"payer_id": 2, "payee_id": 1, "amount": 40},
    ]
    balances = calculate_balances(loans, 1, members)
    assert balances == {1: 0, 2: 0}

def test_balances_invalid_user():
    members = [{"id": 1}, {"id": 2}]
    loans = []
    with pytest.raises(ValueError, match="User must be a member"):
        calculate_balances(loans, 3, members)

def test_balances_invalid_fields():
    members = [{"id": 1}, {"id": 2}]
    loans = [{"payer_id": 1, "payee_id": 2}]  # missing amount
    with pytest.raises(ValueError, match="Loans must have"):
        calculate_balances(loans, 1, members)

def test_balances_negative_amount():
    members = [{"id": 1}, {"id": 2}]
    loans = [{"payer_id": 1, "payee_id": 2, "amount": -10}]
    with pytest.raises(ValueError, match="Loan amounts must be positive"):
        calculate_balances(loans, 1, members)

def test_balances_non_numeric_amount():
    members = [{"id": 1}, {"id": 2}]
    loans = [{"payer_id": 1, "payee_id": 2, "amount": "ten"}]
    with pytest.raises(ValueError, match="Loan amounts must be numeric"):
        calculate_balances(loans, 1, members)

def test_balances_payer_not_in_group():
    members = [{"id": 1}, {"id": 2}]
    loans = [{"payer_id": 3, "payee_id": 2, "amount": 10}]
    with pytest.raises(ValueError, match="Payer must be a member"):
        calculate_balances(loans, 1, members)

def test_balances_payee_not_in_group():
    members = [{"id": 1}, {"id": 2}]
    loans = [{"payer_id": 1, "payee_id": 3, "amount": 10}]
    with pytest.raises(ValueError, match="Payee must be a member"):
        calculate_balances(loans, 1, members)
