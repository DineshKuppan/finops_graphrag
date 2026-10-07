from app.access_control.pbac import build_environment, evaluate_pbac


def business_hours_env():
    return build_environment(simulate_after_hours=False)


def after_hours_env():
    return build_environment(simulate_after_hours=True)


def test_admin_permit_policy_grants_everything(alice_admin, inv_finance_restricted):
    decision = evaluate_pbac(alice_admin, inv_finance_restricted, "approve_invoice", business_hours_env())
    assert decision["allowed"] is True
    assert "admin-full-access" in decision["reason"]


def test_deny_overrides_permit_for_restricted_invoice(bob_finance, inv_finance_restricted):
    # bob's clearance (3) < 5 required for restricted resources, so the
    # explicit deny policy wins even though nothing else is in conflict.
    decision = evaluate_pbac(bob_finance, inv_finance_restricted, "view_invoice", business_hours_env())
    assert decision["allowed"] is False
    assert "deny-restricted-without-top-clearance" in decision["reason"]


def test_auditor_read_only_policy(carol_auditor, inv_finance_internal):
    view = evaluate_pbac(carol_auditor, inv_finance_internal, "view_invoice", business_hours_env())
    approve = evaluate_pbac(carol_auditor, inv_finance_internal, "approve_invoice", business_hours_env())
    assert view["allowed"] is True
    assert approve["allowed"] is False  # no policy permits auditors to approve


def test_finance_manager_can_approve_within_department_and_budget(bob_finance, inv_finance_internal):
    decision = evaluate_pbac(bob_finance, inv_finance_internal, "approve_invoice", business_hours_env())
    assert decision["allowed"] is True


def test_after_hours_blocks_approval_even_with_valid_permit(bob_finance, inv_finance_internal):
    # Same subject, resource, and action as the test above -- the only
    # thing that changed is the environment. This context-sensitivity is
    # unique to PBAC among the three models in this lab.
    decision = evaluate_pbac(bob_finance, inv_finance_internal, "approve_invoice", after_hours_env())
    assert decision["allowed"] is False
    assert "deny-after-hours-approval" in decision["reason"]


def test_default_deny_when_no_policy_matches(dave_marketing, inv_finance_restricted):
    decision = evaluate_pbac(dave_marketing, inv_finance_restricted, "approve_invoice", business_hours_env())
    assert decision["allowed"] is False
