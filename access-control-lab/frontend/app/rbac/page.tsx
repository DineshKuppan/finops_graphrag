"use client";

import { useCallback, useEffect, useState } from "react";
import { RequireAuth } from "../../components/RequireAuth";
import { ModelTabs } from "../../components/ModelTabs";
import { InvoiceTable } from "../../components/InvoiceTable";
import { api, ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { InvoiceDecision } from "../../lib/types";

export default function RbacPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<InvoiceDecision[]>([]);
  const [approving, setApproving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api
      .listInvoices("rbac", token)
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [token]);

  useEffect(load, [load]);

  async function handleApprove(invoiceId: string) {
    if (!token) return;
    setApproving(invoiceId);
    setError(null);
    try {
      const updated = await api.approveInvoice("rbac", invoiceId, token);
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
        <h2>RBAC: Role-Based Access Control</h2>
        <p className="reason">
          Decisions come only from a static role &rarr; permission matrix
          (<code>admin</code> and <code>finance_manager</code> can view and
          approve everything; <code>auditor</code> can view only;{" "}
          <code>employee</code> has no invoice permissions at all).
          Department, clearance, and ownership are never consulted &mdash;
          notice how that can both over-grant and under-grant access.
        </p>
      </div>
      {error && <p style={{ color: "var(--deny)" }}>{error}</p>}
      <div className="card">
        <InvoiceTable
          model="rbac"
          rows={rows}
          onApprove={handleApprove}
          approving={approving}
        />
      </div>
    </RequireAuth>
  );
}
