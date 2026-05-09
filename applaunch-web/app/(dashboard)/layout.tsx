// applaunch-web/app/(dashboard)/layout.tsx
// Dashboard shell — sidebar navigation + top header

import Link from "next/link";
import { LayoutDashboard, Rocket, Settings } from "lucide-react";

const navItems = [
  { href: "/apps",     label: "Apps",     icon: LayoutDashboard },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-56 border-r border-border flex flex-col py-6 px-4 gap-2 shrink-0">
        <div className="flex items-center gap-2 px-2 mb-6">
          <Rocket className="w-5 h-5 text-green-500" />
          <span className="font-bold text-lg">AppLaunch</span>
        </div>

        <nav className="flex flex-col gap-1">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-8">
        {children}
      </main>
    </div>
  );
}
