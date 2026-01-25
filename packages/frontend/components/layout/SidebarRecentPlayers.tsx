"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, User } from "lucide-react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useSidebar } from "./sidebar-context";
import { Avatar } from "@/components/ui/avatar";

interface RecentPlayerItemProps {
  player: {
    _id: string;
    playerId: string;
    name: string;
    position: string;
    team: string;
    headshotUrl?: string;
  };
  onClick?: () => void;
}

function RecentPlayerItem({ player, onClick }: RecentPlayerItemProps) {
  const initials = player.name
    .split(" ")
    .map((n) => n[0])
    .join("");

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-sidebar-accent/50 transition-colors text-left"
    >
      <Avatar
        src={player.headshotUrl}
        alt={player.name}
        fallback={initials}
        size="sm"
        className="h-6 w-6"
      />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium truncate">{player.name}</p>
        <p className="text-[10px] text-muted-foreground">
          {player.position} - {player.team}
        </p>
      </div>
    </button>
  );
}

export function SidebarRecentPlayers() {
  const [isOpen, setIsOpen] = useState(true);
  const { isCollapsed } = useSidebar();

  const recentPlayers = useQuery(api.recentPlayers.getWithDetails);

  if (isCollapsed) {
    return null;
  }

  const hasPlayers = recentPlayers && recentPlayers.length > 0;

  return (
    <div className="px-2">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-sidebar-accent/50 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Recent Players
          </span>
        </div>
        {hasPlayers && (
          <span className="text-xs text-muted-foreground">
            {recentPlayers.length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="py-1 animate-in fade-in slide-in-from-top-1 duration-200">
          {hasPlayers ? (
            <div className="space-y-0.5">
              {recentPlayers.map((player) => (
                <RecentPlayerItem
                  key={player._id}
                  player={player}
                  onClick={() => {
                    // TODO: Open player detail drawer
                    console.log("Open player:", player.playerId);
                  }}
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-4 text-muted-foreground">
              <User className="h-8 w-8 opacity-50" />
              <p className="text-xs">No recent players</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
