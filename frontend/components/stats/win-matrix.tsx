"use client";

import React from "react";
import { WinMatrixResponse } from "@/lib/hooks/use-leaderboard";

interface WinMatrixProps {
  data?: WinMatrixResponse;
  isLoading: boolean;
}

export function WinMatrix({ data, isLoading }: WinMatrixProps) {
  if (isLoading || !data) {
    return <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Loading matrix...</div>;
  }

  const { model_slugs, matrix } = data;

  const getColor = (val: number | null) => {
    if (val === null) return "bg-muted/20 text-muted-foreground";
    // val is between 0 and 1
    if (val > 0.6) return "bg-emerald-500/20 text-emerald-400 font-semibold";
    if (val > 0.5) return "bg-emerald-500/10 text-emerald-300";
    if (val === 0.5) return "bg-muted/40 text-foreground";
    if (val > 0.4) return "bg-rose-500/10 text-rose-300";
    return "bg-rose-500/20 text-rose-400 font-semibold";
  };

  return (
    <div className="w-full overflow-x-auto py-2">
      <table className="w-full text-center text-xs border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-left font-medium text-muted-foreground">Model A \ Model B</th>
            {model_slugs.map((slug) => (
              <th key={slug} className="p-2 font-mono text-[11px] text-muted-foreground max-w-[100px] truncate" title={slug}>
                {slug}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/40">
          {model_slugs.map((slugA, i) => (
            <tr key={slugA}>
              <td className="p-2 text-left font-mono font-medium text-foreground max-w-[120px] truncate" title={slugA}>
                {slugA}
              </td>
              {model_slugs.map((slugB, j) => {
                if (i === j) {
                  return (
                    <td key={slugB} className="p-2 bg-muted/30 text-muted-foreground/40 font-mono">
                      -
                    </td>
                  );
                }
                const val = matrix[i]?.[j];
                return (
                  <td key={slugB} className={`p-2 font-mono transition-colors ${getColor(val)}`}>
                    {val !== null && val !== undefined ? `${(val * 100).toFixed(0)}%` : "N/A"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

