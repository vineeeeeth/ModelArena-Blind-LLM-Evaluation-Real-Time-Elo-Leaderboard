"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Swords, Sparkles } from "lucide-react";
import { PromptBox } from "@/components/arena/prompt-box";
import { BattleView } from "@/components/arena/battle-view";
import { VoteBar } from "@/components/arena/vote-bar";
import { RevealAnimation } from "@/components/arena/reveal-animation";
import {
  useCreateBattle,
  useStreamSlot,
  useVote,
  VoteResult,
} from "@/lib/hooks/use-battle";
import { toast } from "sonner";

export default function ArenaPage() {
  const [battleId, setBattleId] = useState<string | null>(null);
  const [battleCategory, setBattleCategory] = useState<string>("general");
  const [voteResult, setVoteResult] = useState<VoteResult | null>(null);
  const [voteStartTime, setVoteStartTime] = useState<number | null>(null);

  const createBattleMutation = useCreateBattle();
  const voteMutation = useVote(battleId || "");

  // Slot streaming hooks: automatically initiate streaming when battleId is present
  const slotA = useStreamSlot(battleId, "A");
  const slotB = useStreamSlot(battleId, "B");

  const handleStartBattle = async (prompt: string, category?: string) => {
    try {
      setVoteResult(null);
      setVoteStartTime(null);

      const res = await createBattleMutation.mutateAsync({
        prompt,
        category,
      });

      setBattleId(res.battle_id);
      setBattleCategory(res.category);
    } catch (err: any) {
      toast.error(err.message || "Failed to start battle. Please try again.");
    }
  };

  // Record time when both models finish generating
  useEffect(() => {
    if (slotA.isDone && slotB.isDone && !voteStartTime && battleId) {
      setVoteStartTime(Date.now());
    }
  }, [slotA.isDone, slotB.isDone, voteStartTime, battleId]);

  const handleVote = async (choice: "A" | "B" | "tie" | "both_bad") => {
    if (!battleId) return;

    const timeToVote = voteStartTime ? Date.now() - voteStartTime : undefined;
    try {
      const result = await voteMutation.mutateAsync({
        choice,
        time_to_vote_ms: timeToVote,
      });
      setVoteResult(result);
      toast.success("Vote recorded! Ratings updated.");
    } catch (err: any) {
      toast.error(err.message || "Failed to submit vote.");
    }
  };

  const handleNewBattle = () => {
    setBattleId(null);
    setVoteResult(null);
    setVoteStartTime(null);
  };

  const bothDone = slotA.isDone && slotB.isDone;

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8 sm:py-12">
      {/* Hero Header */}
      {!battleId && (
        <div className="text-center space-y-4 mb-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-muted/40 px-3.5 py-1 text-xs font-medium text-muted-foreground"
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Blind Head-to-Head LLM Evaluations</span>
          </motion.div>

          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            Compare Models Side by Side
          </h1>
          <p className="max-w-2xl mx-auto text-base sm:text-lg text-muted-foreground">
            Submit any prompt to receive answers from two anonymous LLMs. Evaluate the responses,
            cast your vote, and reveal their true identities to rank the leaderboard.
          </p>
        </div>
      )}

      {/* Main Content Area */}
      <AnimatePresence mode="wait">
        {!battleId ? (
          <PromptBox
            key="prompt-box"
            onSubmit={handleStartBattle}
            isLoading={createBattleMutation.isPending}
          />
        ) : (
          <div key="battle-in-progress" className="space-y-6">
            {/* Battle View */}
            <BattleView slotA={slotA} slotB={slotB} />

            {/* Voting Bar or Result Reveal */}
            {!voteResult ? (
              <VoteBar
                canVote={bothDone}
                isVoting={voteMutation.isPending}
                onVote={handleVote}
              />
            ) : (
              <RevealAnimation
                voteChoice={voteResult.choice}
                responses={voteResult.responses}
                onNewBattle={handleNewBattle}
              />
            )}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
