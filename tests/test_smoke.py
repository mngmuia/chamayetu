def test_allocation():
 b=[500000,300000,200000];r=90000;a=[round(r*x/sum(b),2) for x in b];assert sum(a)==r
