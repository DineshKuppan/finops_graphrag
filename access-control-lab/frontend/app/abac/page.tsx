"use client";

import { useCallback, useEffect, useState } from "react";
import { RequireAuth } from "../../components/RequireAuth";
import { ModelTabs } from "../../components/ModelTabs";
import { InvoiceTable } from "../../components/InvoiceTable";
import { api, ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { InvoiceDecision } from "../../lib/types";

export default function AbacPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<InvoiceDecision[]>([]);
  const [approving, setApproving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api
      .listInvoices("abac", token)
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [token]);

  useEffect(load, [load]);

  async function handleApprove(invoiceId: string) {
    if (!token) return;
    setApproving(invoiceId);
    setError(null);
    try {
      const updated = await api.approveInvoice("abac", invoiceId, token);
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
        <h2>ABAC: Attribute-Based Access Control</h2>
        <p className="reason">
          Decisions compare <em>attributes</em>: your department, clearance
          level, and region against the invoice&rsquo;s department,
          classification level, and region, plus an amount-based approval
          budget derived from your clearance. The same role can get
          different answers on different invoices.
        </p>
      </div>
      {error && <p style={{ color: "var(--deny)" }}>{error}</p>}
      <div className="card">
        <InvoiceTable
          model="abac"
          rows={rows}
          onApprove={handleApprove}
          approving={approving}
        />
      </div>
    </RequireAuth>
  );
}
