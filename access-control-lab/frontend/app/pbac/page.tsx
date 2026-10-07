"use client";

import { useCallback, useEffect, useState } from "react";
import { RequireAuth } from "../../components/RequireAuth";
import { ModelTabs } from "../../components/ModelTabs";
import { InvoiceTable } from "../../components/InvoiceTable";
import { api, ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { InvoiceDecision, Policy } from "../../lib/types";

export default function PbacPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<InvoiceDecision[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [showPolicies, setShowPolicies] = useState(false);
  const [simulateAfterHours, setSimulateAfterHours] = useState(false);
  const [approving, setApproving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api
      .listInvoices("pbac", token, { simulateAfterHours })
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [token, simulateAfterHours]);

  useEffect(load, [load]);

  useEffect(() => {
    api.listPolicies().then(setPolicies).catch(() => {});
  }, []);

  async function handleApprove(invoiceId: string) {
    if (!token) return;
    setApproving(invoiceId);
    setError(null);
    try {
      const updated = await api.approveInvoice("pbac", invoiceId, token, {
        simulateAfterHours,
      });
      setRows((prev) =>
        prev.map((r) => (r.invoice.id === invoiceId ? updated : r))
      );
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setApproving(null);
    }
  }

  return (
    <RequireAuth>
      <ModelTabs />
      <div className="card">
        <h2>PBAC: Policy-Based Access Control</h2>
        <p className="reason">
          Decisions are computed by evaluating a list of declarative policy
          documents (roles, attributes, and environment/context all
          allowed as conditions) with a <strong>deny-overrides</strong>{" "}
          combining algorithm: any matching deny wins, otherwise any
          matching permit wins, otherwise the default is deny.
        </p>
        <button className="link" onClick={() => setShowPolicies((v) => !v)}>
          {showPolicies ? "hide raw policies" : "show raw policies"}
        </button>
        {showPolicies && (
          <pre
            style={{
              background: "#0b0f18",
              padding: 12,
              borderRadius: 8,
              overflowX: "auto",
              fontSize: 12,
              marginTop: 10,
            }}
          >
            {JSON.stringify(policies, null, 2)}
          </pre>
        )}
      </div>

      <div className="toggle-row">
        <label>
          <input
            type="checkbox"
            checked={simulateAfterHours}
            onChange={(e) => setSimulateAfterHours(e.target.checked)}
          />{" "}
          Simulate after-hours (approvals get denied by the{" "}
          <code>deny-after-hours-approval</code> policy regardless of
          role/attributes)
        </label>
      </div>

      {error && <p style={{ color: "var(--deny)" }}>{error}</p>}
      <div className="card">
        <InvoiceTable
          model="pbac"
          rows={rows}
          onApprove={handleApprove}
          approving={approving}
        />
      </div>
    </RequireAuth>
  );
}
