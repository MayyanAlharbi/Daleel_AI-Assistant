import type { ReactNode } from "react";
import TopBar from "@/components/TopBar";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <TopBar />
      <main>{children}</main>
    </div>
  );
}
