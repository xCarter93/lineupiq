"use client";

import Link from "next/link";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-border/50 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo - links to homepage */}
        <Link
          href="/"
          className="text-xl font-bold tracking-tight text-foreground hover:text-primary transition-colors"
        >
          LineupIQ
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-6">
          <Link
            href="/matchup"
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Matchup Simulator
          </Link>
        </nav>
      </div>
    </header>
  );
}
