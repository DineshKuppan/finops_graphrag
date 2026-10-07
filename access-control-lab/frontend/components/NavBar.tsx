"use client";

import Link from "next/link";
import { useAuth } from "../lib/auth";

export function NavBar() {
  const { user, logout } = useAuth();

  return (
    <header className="navbar">
      <Link href="/" className="brand">
        FinOps Access Control Lab
      </Link>
      <nav>
        {user && (
          <>
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/rbac">RBAC</Link>
            <Link href="/abac">ABAC</Link>
            <Link href="/pbac">PBAC</Link>
            <span className="pill">{user.username}</span>
            <button onClick={logout}>Log out</button>
          </>
        )}
      </nav>
    </header>
  );
}
