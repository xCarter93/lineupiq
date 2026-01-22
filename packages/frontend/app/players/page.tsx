import { SectionLabel } from "@/components/ui/section-label";
import { PlayerRepository } from "@/components/players/PlayerRepository";

export default function PlayersPage() {
  return (
    <div className="min-h-screen">
      <div className="max-w-[1800px] mx-auto px-6 lg:px-10 py-12">
        {/* Hero Section */}
        <div className="mb-8">
          <SectionLabel className="mb-4 block">PLAYER LOOKUP</SectionLabel>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-3">
            2025 Player Performance
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Explore predicted vs actual stats for all NFL players. Select a player to see
            week-by-week validation of our ML models against 2025 season data.
          </p>
        </div>

        {/* Player Repository Component */}
        <PlayerRepository />
      </div>
    </div>
  );
}
