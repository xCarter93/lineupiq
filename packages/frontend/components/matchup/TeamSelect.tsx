"use client";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

interface Team {
  abbr: string;
  name: string;
  division: string;
}

export const NFL_TEAMS: Team[] = [
  // AFC East
  { abbr: "BUF", name: "Bills", division: "AFC East" },
  { abbr: "MIA", name: "Dolphins", division: "AFC East" },
  { abbr: "NE", name: "Patriots", division: "AFC East" },
  { abbr: "NYJ", name: "Jets", division: "AFC East" },
  // AFC North
  { abbr: "BAL", name: "Ravens", division: "AFC North" },
  { abbr: "CIN", name: "Bengals", division: "AFC North" },
  { abbr: "CLE", name: "Browns", division: "AFC North" },
  { abbr: "PIT", name: "Steelers", division: "AFC North" },
  // AFC South
  { abbr: "HOU", name: "Texans", division: "AFC South" },
  { abbr: "IND", name: "Colts", division: "AFC South" },
  { abbr: "JAX", name: "Jaguars", division: "AFC South" },
  { abbr: "TEN", name: "Titans", division: "AFC South" },
  // AFC West
  { abbr: "DEN", name: "Broncos", division: "AFC West" },
  { abbr: "KC", name: "Chiefs", division: "AFC West" },
  { abbr: "LV", name: "Raiders", division: "AFC West" },
  { abbr: "LAC", name: "Chargers", division: "AFC West" },
  // NFC East
  { abbr: "DAL", name: "Cowboys", division: "NFC East" },
  { abbr: "NYG", name: "Giants", division: "NFC East" },
  { abbr: "PHI", name: "Eagles", division: "NFC East" },
  { abbr: "WAS", name: "Commanders", division: "NFC East" },
  // NFC North
  { abbr: "CHI", name: "Bears", division: "NFC North" },
  { abbr: "DET", name: "Lions", division: "NFC North" },
  { abbr: "GB", name: "Packers", division: "NFC North" },
  { abbr: "MIN", name: "Vikings", division: "NFC North" },
  // NFC South
  { abbr: "ATL", name: "Falcons", division: "NFC South" },
  { abbr: "CAR", name: "Panthers", division: "NFC South" },
  { abbr: "NO", name: "Saints", division: "NFC South" },
  { abbr: "TB", name: "Buccaneers", division: "NFC South" },
  // NFC West
  { abbr: "ARI", name: "Cardinals", division: "NFC West" },
  { abbr: "LAR", name: "Rams", division: "NFC West" },
  { abbr: "SEA", name: "Seahawks", division: "NFC West" },
  { abbr: "SF", name: "49ers", division: "NFC West" },
];

// Group teams by division
const DIVISIONS = [
  "AFC East",
  "AFC North",
  "AFC South",
  "AFC West",
  "NFC East",
  "NFC North",
  "NFC South",
  "NFC West",
] as const;

interface TeamSelectProps {
  value: string | null;
  onSelect: (team: string) => void;
  placeholder?: string;
}

export function TeamSelect({
  value,
  onSelect,
  placeholder = "Select opponent...",
}: TeamSelectProps) {
  const selectedTeam = value ? NFL_TEAMS.find((t) => t.abbr === value) : null;

  return (
    <Select value={value ?? undefined} onValueChange={onSelect}>
      <SelectTrigger
        className={cn(
          "bg-white rounded-lg border-border/50 shadow-sm h-11 w-full",
          "focus:ring-2 focus:ring-primary/20"
        )}
      >
        <SelectValue placeholder={placeholder}>
          {selectedTeam ? `${selectedTeam.name} (${selectedTeam.abbr})` : null}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="bg-white rounded-xl shadow-lg">
        {DIVISIONS.map((division) => (
          <SelectGroup key={division}>
            <SelectLabel className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 py-2">
              {division}
            </SelectLabel>
            {NFL_TEAMS.filter((team) => team.division === division).map(
              (team) => (
                <SelectItem
                  key={team.abbr}
                  value={team.abbr}
                  className="hover:bg-muted/50 rounded-md mx-1"
                >
                  {team.name}
                </SelectItem>
              )
            )}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  );
}
