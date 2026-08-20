def test_money_formula():
    gross, expenses, tax = 1000, 100, 50
    assert gross-expenses-tax == 850

def test_allocation_reconciles():
    balances=[500000,300000,200000]; result=90000
    alloc=[round(result*b/sum(balances),2) for b in balances]
    assert sum(alloc)==result
