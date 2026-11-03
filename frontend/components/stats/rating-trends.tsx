"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import { TrendResponse } from "@/lib/hooks/use-leaderboard";

interface RatingTrendsProps {
  trends?: TrendResponse[];
  isLoading: boolean;
}

const COLORS = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#06b6d4", "#f43f5e", "#84cc16"];

export function RatingTrends({ trends, isLoading }: RatingTrendsProps) {
  if (isLoading || !trends || trends.length === 0) {
    return <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Loading trends...</div>;
  }

  // Format data for Recharts: group by timestamp
  const timestamps = Array.from(
    new Set(trends.flatMap((t) => t.points.map((p) => new Date(p.computed_at).toLocaleDateString())))
  );

  const chartData = timestamps.map((ts) => {
    const entry: Record<string, any> = { date: ts };
    for (const t of trends) {
      const match = t.points.find((p) => new Date(p.computed_at).toLocaleDateString() === ts);
      if (match) {
        entry[t.model_slug] = Math.round(match.bt_score);
      }
    }
    return entry;
  });

  return (
    <div className="w-full h-80 pt-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.4} />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#888" }} />
          <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#888" }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: "8px", fontSize: "12px" }}
          />
          <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
          {trends.slice(0, 8).map((t, idx) => (
            <Line
              key={t.model_slug}
              type="monotone"
              dataKey={t.model_slug}
              stroke={COLORS[idx % COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

