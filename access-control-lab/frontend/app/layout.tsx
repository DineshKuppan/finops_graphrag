import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AuthProvider } from "../lib/auth";
import { NavBar } from "../components/NavBar";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinOps Access Control Lab",
  description: "Exploring RBAC, ABAC, and PBAC over the same FinOps resources.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <NavBar />
          <main className="page">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
