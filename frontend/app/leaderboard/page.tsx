"use client";

import React, { useState } from "react";
import { Trophy, Sparkles } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LeaderboardTable } from "@/components/leaderboard/leaderboard-table";
import { SimulatedBadge } from "@/components/leaderboard/simulated-badge";
import { useLeaderboard } from "@/lib/hooks/use-leaderboard";

const CATEGORIES = [
  { id: "overall", label: "Overall" },
  { id: "coding", label: "Coding" },
  { id: "math", label: "Math" },
  { id: "hindi", label: "Hindi" },
  { id: "summarization", label: "Summarization" },
];

function LeaderboardPageContent() {
  const [selectedCategory, setSelectedCategory] = useState("overall");
  const [includeSimulated, setIncludeSimulated] = useState(true);

  const { data, isLoading } = useLeaderboard(selectedCategory, includeSimulated);

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8 sm:py-12 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2.5">
            <Trophy className="h-7 w-7 text-amber-500" />
            <span>LLM Elo & Bradley-Terry Leaderboard</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Statistical rankings computed with Bradley-Terry MLE and 95% Bootstrap Confidence Intervals.
          </p>
        </div>

        <SimulatedBadge
          includeSimulated={includeSimulated}
          onToggle={setIncludeSimulated}
        />
      </div>

      {/* Tabs */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
        <TabsList className="grid grid-cols-2 sm:grid-cols-5 w-full max-w-2xl h-10 p-1">
          {CATEGORIES.map((cat) => (
            <TabsTrigger key={cat.id} value={cat.id} className="text-xs sm:text-sm">
              {cat.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Leaderboard Table */}
      <LeaderboardTable
        entries={data?.entries || []}
        isLoading={isLoading}
      />
    </div>
  );
}

export default function LeaderboardPage() {
  return <LeaderboardPageContent />;
}

