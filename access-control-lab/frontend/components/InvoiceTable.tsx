"use client";

import { Fragment, useState } from "react";
import type { AccessModel, InvoiceDecision } from "../lib/types";

interface Props {
  model: AccessModel;
  rows: InvoiceDecision[];
  onApprove: (invoiceId: string) => Promise<void>;
  approving: string | null;
}

export function InvoiceTable({ model, rows, onApprove, approving }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (rows.length === 0) {
    return <p className="empty-state">No invoices.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Invoice</th>
          <th>Department</th>
          <th>Amount</th>
          <th>Classification</th>
          <th>Region</th>
          <th>View</th>
          <th>Approve</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(({ invoice, decision }) => {
          const isExpanded = expanded === invoice.id;
          return (
            <Fragment key={invoice.id}>
              <tr>
                <td>
                  <div>{invoice.title}</div>
                  <div className="meta" style={{ color: "var(--muted)" }}>
                    {invoice.id}
                  </div>
                </td>
                <td>{invoice.department}</td>
                <td>${invoice.amount.toLocaleString()}</td>
                <td>{invoice.classification}</td>
                <td>{invoice.region}</td>
                <td>
                  <span className={`badge ${decision.allowed ? "allow" : "deny"}`}>
                    {decision.allowed ? "ALLOWED" : "DENIED"}
                  </span>
                  <div>
                    <button
                      className="link"
                      onClick={() =>
                        setExpanded(isExpanded ? null : invoice.id)
                      }
                    >
                      {isExpanded ? "hide" : "why?"}
                    </button>
                  </div>
                </td>
                <td>
                  <button
                    disabled={approving === invoice.id}
                    onClick={() => onApprove(invoice.id)}
                  >
                    {approving === invoice.id ? "checking..." : "Try approve"}
                  </button>
                </td>
              </tr>
              {isExpanded && (
                <tr>
                  <td colSpan={7}>
                    <div className="reason">
                      <strong>{model.toUpperCase()} reason:</strong>{" "}
                      {decision.reason}
                    </div>
                    <ul className="trace">
                      {decision.trace.map((line, i) => (
                        <li key={i}>{line}</li>
                      ))}
                    </ul>
                  </td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
