from app.access_control.rbac import evaluate_rbac


def test_admin_can_view_and_approve_anything(alice_admin, inv_marketing):
    assert evaluate_rbac(alice_admin, inv_marketing, "view_invoice")["allowed"] is True
    assert evaluate_rbac(alice_admin, inv_marketing, "approve_invoice")["allowed"] is True


def test_finance_manager_can_approve_invoice_outside_their_department(bob_finance, inv_marketing):
    # RBAC is role-only: finance_manager can approve ANY invoice, even one
    # that belongs to another department. This is the over-permissioning
    # problem RBAC is prone to.
    decision = evaluate_rbac(bob_finance, inv_marketing, "approve_invoice")
    assert decision["allowed"] is True


def test_employee_role_has_no_invoice_permissions_at_all(dave_marketing, inv_marketing):
    # Even though the invoice belongs to dave's own department, RBAC has
    # no notion of "own department" -- the employee role simply has no
    # view_invoice permission.
    decision = evaluate_rbac(dave_marketing, inv_marketing, "view_invoice")
    assert decision["allowed"] is False


def test_auditor_can_view_but_not_approve(carol_auditor, inv_marketing):
    assert evaluate_rbac(carol_auditor, inv_marketing, "view_invoice")["allowed"] is True
    assert evaluate_rbac(carol_auditor, inv_marketing, "approve_invoice")["allowed"] is False
