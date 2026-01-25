"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";

interface PlayerTableFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedTeam: string | null;
  onTeamChange: (team: string | null) => void;
  teams: string[];
}

export function PlayerTableFilters({
  searchQuery,
  onSearchChange,
  selectedTeam,
  onTeamChange,
  teams,
}: PlayerTableFiltersProps) {
  const hasFilters = searchQuery || selectedTeam;

  const clearFilters = () => {
    onSearchChange("");
    onTeamChange(null);
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search players..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Team Filter */}
      <Select
        value={selectedTeam ?? "all"}
        onValueChange={(v) => onTeamChange(v === "all" ? null : v)}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="All Teams" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Teams</SelectItem>
          {teams.map((team) => (
            <SelectItem key={team} value={team}>
              {team}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Clear Filters */}
      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={clearFilters}>
          <X className="h-3.5 w-3.5 mr-1.5" />
          Clear
        </Button>
      )}
    </div>
  );
}
