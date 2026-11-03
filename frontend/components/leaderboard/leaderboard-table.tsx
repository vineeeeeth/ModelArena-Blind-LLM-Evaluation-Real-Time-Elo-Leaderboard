"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Trophy, ArrowUpDown, ExternalLink, ShieldCheck, HelpCircle } from "lucide-react";
import { LeaderboardEntry } from "@/lib/hooks/use-leaderboard";
import { Skeleton } from "../ui/skeleton";
import { Badge } from "../ui/badge";

interface LeaderboardTableProps {
  entries: LeaderboardEntry[];
  isLoading: boolean;
}

export function LeaderboardTable({ entries, isLoading }: LeaderboardTableProps) {
  const [sortField, setSortField] = useState<keyof LeaderboardEntry>("rank");
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  const handleSort = (field: keyof LeaderboardEntry) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === "rank");
    }
  };

  const sortedEntries = [...entries].sort((a, b) => {
    const valA = a[sortField];
    const valB = b[sortField];
    if (typeof valA === "number" && typeof valB === "number") {
      return sortAsc ? valA - valB : valB - valA;
    }
    return String(valA).localeCompare(String(valB));
  });

  if (isLoading) {
    return (
      <div className="w-full space-y-2 py-4">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No battles recorded yet in this category.
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-border/60 bg-card/40 backdrop-blur-md shadow-sm">
      <table className="w-full text-left text-sm border-collapse">
        <thead className="bg-muted/40 text-xs uppercase text-muted-foreground border-b border-border/60 select-none">
          <tr>
            <th onClick={() => handleSort("rank")} className="py-3.5 px-4 cursor-pointer hover:text-foreground">
              <div className="flex items-center gap-1">Rank <ArrowUpDown className="h-3 w-3" /></div>
            </th>
            <th className="py-3.5 px-4">Model</th>
            <th onClick={() => handleSort("bt_score")} className="py-3.5 px-4 cursor-pointer hover:text-foreground">
              <div className="flex items-center gap-1">Score (95% CI) <ArrowUpDown className="h-3 w-3" /></div>
            </th>
            <th onClick={() => handleSort("win_rate")} className="py-3.5 px-4 cursor-pointer hover:text-foreground">
              <div className="flex items-center gap-1">Win Rate <ArrowUpDown className="h-3 w-3" /></div>
            </th>
            <th onClick={() => handleSort("num_battles")} className="py-3.5 px-4 cursor-pointer hover:text-foreground">
              <div className="flex items-center gap-1">Battles <ArrowUpDown className="h-3 w-3" /></div>
            </th>
            <th onClick={() => handleSort("avg_latency_ms")} className="py-3.5 px-4 cursor-pointer hover:text-foreground">
              <div className="flex items-center gap-1">Avg Latency <ArrowUpDown className="h-3 w-3" /></div>
            </th>
            <th className="py-3.5 px-4">Cost / 1M Out</th>
            <th className="py-3.5 px-4">License</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/40 font-mono text-xs">
          <AnimatePresence mode="popLayout">
            {sortedEntries.map((row) => {
              const ciDiff = Math.round((row.ci_high - row.ci_low) / 2);
              const isTop3 = row.rank <= 3;

              return (
                <motion.tr
                  key={row.model_slug}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ type: "spring", stiffness: 350, damping: 25 }}
                  className="hover:bg-muted/30 transition-colors"
                >
                  {/* Rank */}
                  <td className="py-3.5 px-4 font-semibold text-sm">
                    <div className="flex items-center gap-1.5">
                      {row.rank === 1 && <Trophy className="h-4 w-4 text-amber-400" />}
                      {row.rank === 2 && <Trophy className="h-4 w-4 text-slate-400" />}
                      {row.rank === 3 && <Trophy className="h-4 w-4 text-amber-600" />}
                      <span>#{row.rank}</span>
                    </div>
                  </td>

                  {/* Model */}
                  <td className="py-3.5 px-4 font-sans">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-foreground">{row.model_name}</span>
                      {row.is_provisional && (
                        <Badge variant="outline" className="text-[10px] text-amber-500 border-amber-500/30">
                          Provisional
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">{row.provider}</span>
                  </td>

                  {/* Bradley-Terry & CI */}
                  <td className="py-3.5 px-4 font-semibold text-sm text-foreground">
                    <div className="flex items-center gap-1.5">
                      <span>{Math.round(row.bt_score)}</span>
                      <span className="text-xs font-normal text-muted-foreground">
                        ±{ciDiff}
                      </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground font-normal">
                      [{Math.round(row.ci_low)}, {Math.round(row.ci_high)}]
                    </div>
                  </td>

                  {/* Win rate */}
                  <td className="py-3.5 px-4 text-sm font-sans">
                    {(row.win_rate * 100).toFixed(1)}%
                  </td>

                  {/* Battles */}
                  <td className="py-3.5 px-4 text-sm font-sans">
                    {row.num_battles.toLocaleString()}
                  </td>

                  {/* Latency */}
                  <td className="py-3.5 px-4 font-sans text-xs">
                    {(row.avg_latency_ms / 1000).toFixed(2)}s
                  </td>

                  {/* Cost */}
                  <td className="py-3.5 px-4 font-sans text-xs">
                    {row.avg_cost_usd === 0 ? "Free" : `$${(row.avg_cost_usd * 1000).toFixed(3)}`}
                  </td>

                  {/* License */}
                  <td className="py-3.5 px-4 font-sans">
                    <Badge variant={row.is_open_source ? "secondary" : "outline"} className="text-[10px]">
                      {row.is_open_source ? "Open Weights" : "Proprietary"}
                    </Badge>
                  </td>
                </motion.tr>
              );
            })}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
}

