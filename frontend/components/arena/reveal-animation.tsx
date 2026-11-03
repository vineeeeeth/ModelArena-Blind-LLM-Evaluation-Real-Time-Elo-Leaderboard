"use client";

import React from "react";
import { motion } from "motion/react";
import { Trophy, Zap, Clock, Coins, RotateCcw, ArrowRight } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ResponseReveal } from "@/lib/hooks/use-battle";

interface RevealAnimationProps {
  voteChoice: "A" | "B" | "tie" | "both_bad";
  responses: ResponseReveal[];
  onNewBattle: () => void;
}

export function RevealAnimation({
  voteChoice,
  responses,
  onNewBattle,
}: RevealAnimationProps) {
  const respA = responses.find((r) => r.slot === "A");
  const respB = responses.find((r) => r.slot === "B");

  const isWinnerA = voteChoice === "A";
  const isWinnerB = voteChoice === "B";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, type: "spring", bounce: 0.25 }}
      className="w-full max-w-4xl mx-auto my-6 p-6 rounded-2xl border border-primary/30 bg-card/90 backdrop-blur-xl shadow-2xl space-y-6"
    >
      <div className="text-center space-y-1">
        <Badge variant="outline" className="px-3 py-1 text-xs uppercase tracking-wider bg-primary/10 text-primary border-primary/20">
          Identities Revealed
        </Badge>
        <h2 className="text-2xl font-bold tracking-tight">Battle Results</h2>
        <p className="text-sm text-muted-foreground">
          {voteChoice === "A" && "You voted for Model A"}
          {voteChoice === "B" && "You voted for Model B"}
          {voteChoice === "tie" && "You voted for a Tie"}
          {voteChoice === "both_bad" && "You voted Both Bad"}
        </p>
      </div>

      {/* Model Cards Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Model A Reveal */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className={`relative p-5 rounded-xl border ${
            isWinnerA
              ? "border-emerald-500/50 bg-emerald-500/5 shadow-md shadow-emerald-500/10"
              : "border-border/60 bg-muted/20"
          }`}
        >
          {isWinnerA && (
            <div className="absolute top-3 right-3 flex items-center gap-1 text-emerald-500 text-xs font-semibold">
              <Trophy className="h-4 w-4" /> Winner
            </div>
          )}
          <span className="text-xs font-mono font-medium text-muted-foreground uppercase">
            Slot A
          </span>
          <h3 className="text-xl font-bold mt-1 text-foreground">
            {respA?.model_name || "Unknown Model"}
          </h3>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            {respA?.model_slug}
          </p>

          <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-border/40 text-center">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase flex items-center justify-center gap-1">
                <Clock className="h-3 w-3" /> Latency
              </span>
              <p className="font-semibold text-sm mt-0.5">
                {respA?.total_latency_ms ? `${(respA.total_latency_ms / 1000).toFixed(2)}s` : "N/A"}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground uppercase flex items-center justify-center gap-1">
                <Zap className="h-3 w-3" /> Tokens
              </span>
              <p className="font-semibold text-sm mt-0.5">
                {respA?.output_tokens || 0}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground uppercase flex items-center justify-center gap-1">
                <Coins className="h-3 w-3" /> Cost
              </span>
              <p className="font-semibold text-sm mt-0.5">
                {respA?.cost_usd === 0 ? "Free ($0)" : `$${respA?.cost_usd?.toFixed(5)}`}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Model B Reveal */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className={`relative p-5 rounded-xl border ${
            isWinnerB
              ? "border-emerald-500/50 bg-emerald-500/5 shadow-md shadow-emerald-500/10"
              : "border-border/60 bg-muted/20"
          }`}
        >
          {isWinnerB && (
            <div className="absolute top-3 right-3 flex items-center gap-1 text-emerald-500 text-xs font-semibold">
              <Trophy className="h-4 w-4" /> Winner
            </div>
          )}
          <span className="text-xs font-mono font-medium text-muted-foreground uppercase">
            Slot B
          </span>
          <h3 className="text-xl font-bold mt-1 text-foreground">
            {respB?.model_name || "Unknown Model"}
          </h3>
          <p className="text-xs text-muted-foreground font-mono mt-0.5">
            {respB?.model_slug}
          </p>

          <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-border/40 text-center">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase flex items-center justify-center gap-1">
                <Clock className="h-3 w-3" /> Latency
              </span>
              <p className="font-semibold text-sm mt-0.5">
                {respB?.total_latency_ms ? `${(respB.total_latency_ms / 1000).toFixed(2)}s` : "N/A"}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground uppercase flex items-center justify-center gap-1">
                <Zap className="h-3 w-3" /> Tokens
              </span>
              <p className="font-semibold text-sm mt-0.5">
                {respB?.output_tokens || 0}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground uppercase flex items-center justify-center gap-1">
                <Coins className="h-3 w-3" /> Cost
              </span>
              <p className="font-semibold text-sm mt-0.5">
                {respB?.cost_usd === 0 ? "Free ($0)" : `$${respB?.cost_usd?.toFixed(5)}`}
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Action to Start New Battle */}
      <div className="flex justify-center pt-2">
        <Button onClick={onNewBattle} size="lg" className="gap-2 px-8 shadow-lg shadow-primary/20">
          <RotateCcw className="h-4 w-4" /> Start New Battle
        </Button>
      </div>
    </motion.div>
  );
}

