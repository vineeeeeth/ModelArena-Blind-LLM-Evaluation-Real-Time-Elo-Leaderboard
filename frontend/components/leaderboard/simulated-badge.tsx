"use client";

import React from "react";
import { Info } from "lucide-react";

interface SimulatedBadgeProps {
  includeSimulated: boolean;
  onToggle: (checked: boolean) => void;
}

export function SimulatedBadge({ includeSimulated, onToggle }: SimulatedBadgeProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border/60 bg-muted/30 px-3.5 py-1.5 text-xs text-muted-foreground">
      <div className="flex items-center gap-1.5">
        <Info className="h-3.5 w-3.5 text-amber-500" />
        <span>Includes simulated demo data</span>
      </div>
      <label className="flex items-center gap-1.5 cursor-pointer select-none font-medium text-foreground">
        <input
          type="checkbox"
          checked={includeSimulated}
          onChange={(e) => onToggle(e.target.checked)}
          className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
        />
        <span>Show Demo Votes</span>
      </label>
    </div>
  );
}

