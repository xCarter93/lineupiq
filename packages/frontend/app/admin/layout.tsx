"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Database, PlayCircle, Settings } from "lucide-react";

const adminTabs = [
  { href: "/admin", label: "Roster", icon: Database },
  { href: "/admin/simulation", label: "Simulation", icon: PlayCircle },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      <div className="flex items-center gap-2 mb-2">
        <Settings className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
      </div>
      <p className="text-muted-foreground mb-6">
        Manage data, simulations, and system settings
      </p>

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b mb-6">
        {adminTabs.map((tab) => {
          const isActive =
            tab.href === "/admin"
              ? pathname === "/admin"
              : pathname.startsWith(tab.href);
          const Icon = tab.icon;

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                isActive
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30"
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </Link>
          );
        })}
      </div>

      {children}
    </div>
  );
}
