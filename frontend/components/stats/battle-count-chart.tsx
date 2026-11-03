"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

interface BattleCountChartProps {
  counts?: Record<string, number>;
  isLoading: boolean;
}

export function BattleCountChart({ counts, isLoading }: BattleCountChartProps) {
  if (isLoading || !counts) {
    return <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Loading counts...</div>;
  }

  const data = Object.entries(counts)
    .filter(([k]) => k !== "total")
    .map(([cat, count]) => ({
      category: cat.charAt(0).toUpperCase() + cat.slice(1),
      battles: count,
    }));

  return (
    <div className="w-full h-80 pt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 30, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.4} />
          <XAxis dataKey="category" tick={{ fontSize: 11, fill: "#888" }} />
          <YAxis tick={{ fontSize: 11, fill: "#888" }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: "8px", fontSize: "12px" }}
          />
          <Bar dataKey="battles" fill="#6366f1" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

