"use client";

import Link from "next/link";
import { useAuth } from "../lib/auth";

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div>
      <div className="card">
        <h2>RBAC vs ABAC vs PBAC, side by side</h2>
        <p>
          This lab runs the same five demo users and the same six mock
          FinOps invoices through three different authorization models.
          Each model answers the same question &mdash;{" "}
          <em>&ldquo;can this user view or approve this invoice?&rdquo;</em>{" "}
          &mdash; using different inputs:
        </p>
        <ul>
          <li>
            <strong>RBAC</strong> (Role-Based) looks only at which{" "}
            <em>roles</em> a user holds, against a static role-permission
            matrix.
          </li>
          <li>
            <strong>ABAC</strong> (Attribute-Based) compares{" "}
            <em>attributes</em> of the user (department, clearance,
            region) against attributes of the resource (department,
            classification, amount).
          </li>
          <li>
            <strong>PBAC</strong> (Policy-Based) evaluates declarative{" "}
            <em>policy documents</em> that can combine roles, attributes,
            and environment/context (e.g. time of day), with an explicit
            deny-overrides conflict resolution rule.
          </li>
        </ul>
        <p>
          Every decision screen shows the verdict, the reason, and the
          full evaluation trace, so you can see exactly why access was
          granted or denied under each model.
        </p>
        {user ? (
          <Link href="/dashboard">
            <button className="primary">Go to dashboard</button>
          </Link>
        ) : (
          <Link href="/login">
            <button className="primary">Log in to start exploring</button>
          </Link>
        )}
      </div>
    </div>
  );
}
