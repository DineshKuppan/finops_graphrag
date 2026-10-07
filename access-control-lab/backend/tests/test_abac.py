from app.access_control.abac import evaluate_abac


def test_same_department_grants_view(dave_marketing, inv_marketing):
    decision = evaluate_abac(dave_marketing, inv_marketing, "view_invoice")
    assert decision["allowed"] is True


def test_different_department_without_clearance_denies_view(erin_legal, inv_marketing):
    # erin is LEGAL/EU with clearance 2; inv_marketing is MARKETING/US,
    # internal (level 1). Department differs and region differs too.
    decision = evaluate_abac(erin_legal, inv_marketing, "view_invoice")
    assert decision["allowed"] is False


def test_sufficient_clearance_and_matching_region_grants_view(carol_auditor, inv_finance_restricted):
    # carol: FINANCE/EU, clearance 4. inv_finance_restricted: FINANCE/US,
    # restricted (level 5). Same department -> allowed regardless of region.
    decision = evaluate_abac(carol_auditor, inv_finance_restricted, "view_invoice")
    assert decision["allowed"] is True


def test_finance_manager_cannot_approve_outside_their_department(bob_finance, inv_marketing):
    # Unlike RBAC, ABAC blocks bob from approving a MARKETING invoice.
    decision = evaluate_abac(bob_finance, inv_marketing, "approve_invoice")
    assert decision["allowed"] is False


def test_finance_manager_can_approve_small_invoice_in_own_department(bob_finance, inv_finance_internal):
    decision = evaluate_abac(bob_finance, inv_finance_internal, "approve_invoice")
    assert decision["allowed"] is True


def test_clearance_insufficient_for_restricted_approval(bob_finance, inv_finance_restricted):
    # bob's clearance (3) is below the restricted invoice's level (5).
    decision = evaluate_abac(bob_finance, inv_finance_restricted, "approve_invoice")
    assert decision["allowed"] is False
