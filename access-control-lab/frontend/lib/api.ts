import type {
  AccessModel,
  DemoUser,
  InvoiceDecision,
  Policy,
  UserProfile,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || "Request failed");
  }
  return res.json() as Promise<T>;
}

function authHeader(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

export const api = {
  listDemoUsers: () => request<DemoUser[]>("/auth/users"),

  login: (username: string, password: string) =>
    request<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  me: (token: string) =>
    request<UserProfile>("/auth/me", { headers: authHeader(token) }),

  listInvoices: (
    model: AccessModel,
    token: string,
    opts?: { simulateAfterHours?: boolean }
  ) => {
    const qs =
      model === "pbac" && opts?.simulateAfterHours
        ? "?simulate_after_hours=true"
        : "";
    return request<InvoiceDecision[]>(`/${model}/invoices${qs}`, {
      headers: authHeader(token),
    });
  },

  approveInvoice: (
    model: AccessModel,
    invoiceId: string,
    token: string,
    opts?: { simulateAfterHours?: boolean }
  ) => {
    const qs =
      model === "pbac" && opts?.simulateAfterHours
        ? "?simulate_after_hours=true"
        : "";
    return request<InvoiceDecision>(
      `/${model}/invoices/${invoiceId}/approve${qs}`,
      { method: "POST", headers: authHeader(token) }
    );
  },

  listPolicies: () => request<Policy[]>("/pbac/policies"),
};

export { ApiError, API_URL };
