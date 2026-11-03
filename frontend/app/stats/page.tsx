"use client";

import React, { useState } from "react";
import { BarChart3, TrendingUp, Grid, ScatterChart as ScatterIcon, Layers } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ConfidenceChart } from "@/components/stats/confidence-chart";
import { WinMatrix } from "@/components/stats/win-matrix";
import { RatingTrends } from "@/components/stats/rating-trends";
import { CostQualityScatter } from "@/components/stats/cost-quality-scatter";
import { BattleCountChart } from "@/components/stats/battle-count-chart";
import {
  useLeaderboard,
  useWinMatrix,
  useTrends,
  useCostLatency,
  useBattleCounts,
} from "@/lib/hooks/use-leaderboard";

const CATEGORIES = [
  { id: "overall", label: "Overall" },
  { id: "coding", label: "Coding" },
  { id: "math", label: "Math" },
  { id: "hindi", label: "Hindi" },
  { id: "summarization", label: "Summarization" },
];

export default function StatsPage() {
  const [selectedCategory, setSelectedCategory] = useState("overall");

  const { data: leaderboard, isLoading: isLeadLoading } = useLeaderboard(selectedCategory);
  const { data: winMatrix, isLoading: isMatrixLoading } = useWinMatrix(selectedCategory);
  const { data: trends, isLoading: isTrendsLoading } = useTrends(selectedCategory);
  const { data: costLatency, isLoading: isCostLoading } = useCostLatency();
  const { data: battleCounts, isLoading: isCountsLoading } = useBattleCounts();

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8 sm:py-12 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2.5">
          <BarChart3 className="h-7 w-7 text-indigo-500" />
          <span>Analytics & Statistical Analysis</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Detailed metrics, pairwise head-to-head records, bootstrap intervals, and cost-latency trade-offs.
        </p>
      </div>

      {/* Category selector */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
        <TabsList className="grid grid-cols-2 sm:grid-cols-5 w-full max-w-2xl h-10 p-1">
          {CATEGORIES.map((cat) => (
            <TabsTrigger key={cat.id} value={cat.id} className="text-xs sm:text-sm">
              {cat.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Grid of Statistical Visualizations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Confidence Interval Dot & Whisker */}
        <Card className="col-span-1 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Layers className="h-5 w-5 text-purple-500" />
              <span>Bootstrap Confidence Intervals (95% CI)</span>
            </CardTitle>
            <CardDescription>
              Bradley-Terry ability scores with 95% non-parametric bootstrap intervals (resampled with replacement).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ConfidenceChart entries={leaderboard?.entries || []} />
          </CardContent>
        </Card>

        {/* 2. Pairwise Win Matrix Heatmap */}
        <Card className="col-span-1 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Grid className="h-5 w-5 text-emerald-500" />
              <span>Pairwise Win-Fraction Heatmap (Row vs. Column)</span>
            </CardTitle>
            <CardDescription>
              Fraction of times the row model was voted better than the column model in head-to-head matchups.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <WinMatrix data={winMatrix} isLoading={isMatrixLoading} />
          </CardContent>
        </Card>

        {/* 3. Rating Trends Over Time */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-amber-500" />
              <span>Rating Progression Over Time</span>
            </CardTitle>
            <CardDescription>
              Snapshot of Bradley-Terry scores over successive evaluation epochs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RatingTrends trends={trends} isLoading={isTrendsLoading} />
          </CardContent>
        </Card>

        {/* 4. Cost vs. Quality Scatter */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ScatterIcon className="h-5 w-5 text-cyan-500" />
              <span>Cost vs. Quality Trade-Off</span>
            </CardTitle>
            <CardDescription>
              Average query cost (per 1,000 queries) plotted against model rating.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CostQualityScatter points={costLatency} isLoading={isCostLoading} />
          </CardContent>
        </Card>

        {/* 5. Battle Counts by Category */}
        <Card className="col-span-1 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-500" />
              <span>Evaluations by Category</span>
            </CardTitle>
            <CardDescription>
              Distribution of community evaluations recorded across prompt categories.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <BattleCountChart counts={battleCounts} isLoading={isCountsLoading} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

