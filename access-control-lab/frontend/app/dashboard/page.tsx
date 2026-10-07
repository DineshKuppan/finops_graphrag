"use client";

import Link from "next/link";
import { RequireAuth } from "../../components/RequireAuth";
import { useAuth } from "../../lib/auth";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <RequireAuth>
      {user && (
        <div>
          <div className="card">
            <h2>Welcome, {user.full_name}</h2>
            <ul className="attr-list">
              <li>
                <strong>Roles:</strong> {user.roles.join(", ") || "none"}
              </li>
              <li>
                <strong>Department:</strong> {user.attributes.department}
              </li>
              <li>
                <strong>Clearance level:</strong>{" "}
                {user.attributes.clearance_level}
              </li>
              <li>
                <strong>Region:</strong> {user.attributes.region}
              </li>
            </ul>
          </div>

          <div className="grid">
            <Link href="/rbac" className="card" style={{ display: "block" }}>
              <h3>RBAC</h3>
              <p className="reason">
                See which invoices your <em>roles</em> let you view or
                approve, regardless of department or clearance.
              </p>
            </Link>
            <Link href="/abac" className="card" style={{ display: "block" }}>
              <h3>ABAC</h3>
              <p className="reason">
                See how department, clearance, and region attributes
                change the outcome per invoice.
              </p>
            </Link>
            <Link href="/pbac" className="card" style={{ display: "block" }}>
              <h3>PBAC</h3>
              <p className="reason">
                See the declarative policies in effect, deny-overrides in
                action, and try the after-hours context toggle.
              </p>
            </Link>
          </div>
        </div>
      )}
    </RequireAuth>
  );
}
