"use client";

import React from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Label,
} from "recharts";
import { CostLatencyPoint } from "@/lib/hooks/use-leaderboard";

interface CostQualityScatterProps {
  points?: CostLatencyPoint[];
  isLoading: boolean;
}

export function CostQualityScatter({ points, isLoading }: CostQualityScatterProps) {
  if (isLoading || !points || points.length === 0) {
    return <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Loading scatter plot...</div>;
  }

  const data = points.map((p) => ({
    name: p.model_name,
    cost: p.avg_cost_usd * 1000, // Cost per 1K responses
    elo: Math.round(p.elo),
    latency: (p.avg_latency_ms / 1000).toFixed(2),
  }));

  return (
    <div className="w-full h-80 pt-4">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.4} />
          <XAxis
            type="number"
            dataKey="cost"
            name="Cost"
            unit="$ / 1k"
            tick={{ fontSize: 11, fill: "#888" }}
          >
            <Label value="Avg Cost per 1,000 queries ($)" offset={-20} position="insideBottom" style={{ fill: "#888", fontSize: 11 }} />
          </XAxis>
          <YAxis
            type="number"
            dataKey="elo"
            name="Elo"
            domain={["dataMin - 30", "dataMax + 30"]}
            tick={{ fontSize: 11, fill: "#888" }}
          >
            <Label value="Overall Elo Score" angle={-90} position="insideLeft" style={{ fill: "#888", fontSize: 11 }} />
          </YAxis>
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="rounded-lg border border-border bg-card p-2.5 text-xs shadow-md">
                    <p className="font-semibold text-foreground">{item.name}</p>
                    <p className="text-primary font-mono mt-1">Elo: {item.elo}</p>
                    <p className="text-muted-foreground font-mono">Cost: ${item.cost.toFixed(4)} / 1k queries</p>
                    <p className="text-muted-foreground font-mono">Latency: {item.latency}s</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter data={data} fill="#10b981" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

