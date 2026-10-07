export type AccessModel = "rbac" | "abac" | "pbac";

export interface UserAttributes {
  department: string;
  clearance_level: number;
  region: string;
}

export interface UserProfile {
  id: string;
  username: string;
  full_name: string;
  roles: string[];
  attributes: UserAttributes;
}

export interface DemoUser {
  username: string;
  full_name: string;
  roles: string[];
  department: string;
}

export interface InvoiceOut {
  id: string;
  title: string;
  department: string;
  amount: number;
  classification: string;
  classification_level: number;
  region: string;
  owner_username: string;
}

export interface Decision {
  allowed: boolean;
  model: string;
  action: string;
  reason: string;
  trace: string[];
}

export interface InvoiceDecision {
  invoice: InvoiceOut;
  decision: Decision;
}

export interface Policy {
  id: string;
  description: string;
  effect: "permit" | "deny";
  actions: string[];
  conditions: Array<{
    attr: string;
    op: string;
    value?: unknown;
    value_ref?: string;
  }>;
}
