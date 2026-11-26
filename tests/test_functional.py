from src.models import Bill, Parameters, TenantSettlement, ApartmentSettlement, Transfer, Tenant
from src.manager import Manager


def test_settlement_due_between_tanants_and_apartment():
    manager = Manager(Parameters())

    settlement: ApartmentSettlement = manager.get_settlement('apart-polanka', 2025, 1)
    
    tenants_settlements: list[TenantSettlement] = manager.create_tenants_settlements(settlement)
    assert len(tenants_settlements) == 3

    total_due = sum([tenant_settlement.total_due_pln for tenant_settlement in tenants_settlements])
    assert total_due == settlement.total_due_pln

def test_debtors_calculation():
    manager = Manager(Parameters())

    debtors = manager.get_debtors('apart-polanka', 2025, 1)
    assert len(debtors) == 0

    debtors = manager.get_debtors('apart-polanka', 2025, 2)
    assert len(debtors) == 3


def test_tax_calculation():
    manager = Manager(Parameters())
    
    tax = manager.calculate_tax(2025, 1, 0.085)
    assert tax == 638 # 0.085 * 7500.0

    tax = manager.calculate_tax(2025, 2, 0.085)
    assert tax == 0

def test_deposits_calculation():
    manager = Manager(Parameters())
    
    deposit_balance = manager.check_deposits()
    assert deposit_balance == -8700.0 # no deposit in transfers

    manager.transfers.append(Transfer(
        tenant='tenant-1',
        date='2025-01-01',
        settlement_year=None,
        settlement_month=None,
        amount_pln=1000.0,
        type='deposit'
    ))

    deposit_balance = manager.check_deposits()
    assert deposit_balance == -7700.0 # 1000.0 deposit in transfers

def test_annual_balance_calculation():
    manager = Manager(Parameters())
    
    annual_balance = manager.get_annual_balance(2025)
    assert annual_balance == 6490.0 # 7500.0 in transfers minus 910.0 in bills

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-02-15',
        settlement_year=2025,
        settlement_month=5,
        amount_pln=500.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-02-15',
        settlement_year=2025,
        settlement_month=5,
        amount_pln=4500.0,
        type='renovation'
    ))

    annual_balance = manager.get_annual_balance(2025)
    assert annual_balance == 1490.0 # 7500.0 in transfers minus 910.0 in bills minus new bills 500.0 and 4500.0

def test_apartment_has_any_bills():
    manager = Manager(Parameters())
    
    has_bills = manager.has_any_bills('apart-polanka', 2025, 1)
    assert has_bills == True

    has_bills = manager.has_any_bills('apart-polanka', 2025, 3)
    assert has_bills == False

def test_validate_transfer():
    manager = Manager(Parameters())
    manager.tenants["tenant-4"] = Tenant(
        name = "Kamil Zieliński",
        apartment = "apart-polanka",
        room = "room-bigger",
        rent_pln = 2000.0,
        deposit_pln = 4000.0,
        date_agreement_from = "2025-01-01",
        date_agreement_to = "2025-12-31"
    )

    #transfer with no mistakes
    good_transfer = Transfer(
        amount_pln = 2000.0,
        date = "2025-01-10",
        settlement_year = 2025,
        settlement_month = 1,
        tenant = "tenant-4",
        type = "rent"
        )
    manager.transfers.append(good_transfer)

    assert manager.validate_transfer(good_transfer) == (True, "No errors")

    #Transfer with wrong settlement month
    wrong_month_transfer = Transfer(
        amount_pln = 2000.0,
        date = "2025-01-01",
        settlement_year = 2025,
        settlement_month = 13,
        tenant = "tenant-4",
        type = "rent"
        )
    manager.transfers.append(wrong_month_transfer)

    assert manager.validate_transfer(wrong_month_transfer) == (False, "Wrong settlement month")

    #Transfer with negative amount
    negative_amount_transfer = Transfer(
            amount_pln = -2000.0,
            date = "2025-01-01",
            settlement_year = 2025,
            settlement_month = 13,
            tenant = "tenant-4",
            type = "anti-rent"
            )
    manager.transfers.append(negative_amount_transfer)

    assert manager.validate_transfer(negative_amount_transfer) == (False, "Negative amount")

    #transfer with no tenant
    no_tenant_transfer = Transfer(
        amount_pln = 1000.0,
        date = "2025-01-01",
        settlement_year = 2025,
        settlement_month = 1,
        tenant = "tenant-999",
        type = "rent"
        )
    manager.transfers.append(no_tenant_transfer)
    
    assert manager.validate_transfer(no_tenant_transfer) == (False, "Tenant doesn't exist")

    #transfer out of tenant agreement
    out_of_agreement_transfer = Transfer(
        amount_pln = 1000.0,
        date = "2026-01-01",
        settlement_year = 2026,
        settlement_month = 1,
        tenant = "tenant-4",
        type = "rent"
        )
    manager.transfers.append(out_of_agreement_transfer)
    
    assert manager.validate_transfer(out_of_agreement_transfer) == (False,"Transfer out of tenant agreement")