import Link from "next/link";
import { SectionLabel } from "@/components/ui/section-label";

export default function Page() {
  return (
    <div className="min-h-screen">
      <div className="max-w-4xl mx-auto px-6 py-16 md:py-24">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <SectionLabel className="mb-6 block">
            ML-POWERED PREDICTIONS
          </SectionLabel>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-foreground mb-6">
            Smarter Fantasy Football
            <br />
            <span className="text-primary">Decisions</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Get ML-powered stat projections for any player matchup. Built on historical NFL data
            to help you set winning lineups.
          </p>
          <Link
            href="/matchup"
            className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg shadow-primary/25"
          >
            Build a Matchup
          </Link>
        </div>

        {/* Value Proposition */}
        <div className="bg-white rounded-2xl shadow-sm p-8 md:p-12">
          <SectionLabel className="mb-6 block text-center">
            WHY LINEUPIQ
          </SectionLabel>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-3xl mb-3">📊</div>
              <h3 className="font-semibold text-foreground mb-2">Stat-Level Predictions</h3>
              <p className="text-sm text-muted-foreground">
                Individual stat projections for passing, rushing, and receiving yards plus touchdowns.
              </p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-3">🎯</div>
              <h3 className="font-semibold text-foreground mb-2">Custom Scoring</h3>
              <p className="text-sm text-muted-foreground">
                Configure your league&apos;s scoring rules for accurate fantasy point calculations.
              </p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-3">🏈</div>
              <h3 className="font-semibold text-foreground mb-2">Matchup Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Factor in opponent defense strength and home/away advantage for better projections.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
