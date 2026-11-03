"use client";

import React from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ErrorBar,
  CartesianGrid,
} from "recharts";
import { LeaderboardEntry } from "@/lib/hooks/use-leaderboard";

interface ConfidenceChartProps {
  entries: LeaderboardEntry[];
}

export function ConfidenceChart({ entries }: ConfidenceChartProps) {
  const data = entries.map((e, index) => {
    const errorLow = Math.max(0, e.bt_score - e.ci_low);
    const errorHigh = Math.max(0, e.ci_high - e.bt_score);
    return {
      index,
      name: e.model_name,
      score: Math.round(e.bt_score),
      ci_low: Math.round(e.ci_low),
      ci_high: Math.round(e.ci_high),
      errorY: [errorLow, errorHigh],
    };
  });

  return (
    <div className="w-full h-80 pt-4">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.4} />
          <XAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 11, fill: "#888" }}
            interval={0}
            angle={-20}
            textAnchor="end"
          />
          <YAxis
            type="number"
            dataKey="score"
            name="Score"
            domain={["dataMin - 50", "dataMax + 50"]}
            tick={{ fontSize: 11, fill: "#888" }}
          />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="rounded-lg border border-border bg-card p-2.5 text-xs shadow-md">
                    <p className="font-semibold text-foreground">{item.name}</p>
                    <p className="text-primary font-mono mt-1">Score: {item.score}</p>
                    <p className="text-muted-foreground font-mono">
                      95% CI: [{item.ci_low}, {item.ci_high}]
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter data={data} fill="#8b5cf6">
            <ErrorBar dataKey="errorY" width={4} strokeWidth={2} stroke="#a78bfa" direction="y" />
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

