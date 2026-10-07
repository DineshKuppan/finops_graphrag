"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { DemoUser } from "../../lib/types";

const DEMO_PASSWORD = "password123";

export default function LoginPage() {
  const { login, user } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      router.replace("/dashboard");
      return;
    }
    api.listDemoUsers().then(setUsers).catch((e) => setError(String(e)));
  }, [user, router]);

  async function handleLogin(username: string) {
    setPending(username);
    setError(null);
    try {
      await login(username, DEMO_PASSWORD);
      router.replace("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login failed");
    } finally {
      setPending(null);
    }
  }

  return (
    <div>
      <div className="card">
        <h2>Pick a demo user</h2>
        <p>
          Every demo account uses the password <code>{DEMO_PASSWORD}</code>.
          Pick any user below to see how each access-control model treats
          them differently.
        </p>
        {error && <p style={{ color: "var(--deny)" }}>{error}</p>}
        <div className="grid">
          {users.map((u) => (
            <div
              key={u.username}
              className="user-card"
              onClick={() => handleLogin(u.username)}
            >
              <div className="name">{u.full_name}</div>
              <div className="meta">@{u.username}</div>
              <div className="meta">
                roles: {u.roles.join(", ") || "none"}
              </div>
              <div className="meta">department: {u.department}</div>
              {pending === u.username && <div className="meta">signing in...</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
