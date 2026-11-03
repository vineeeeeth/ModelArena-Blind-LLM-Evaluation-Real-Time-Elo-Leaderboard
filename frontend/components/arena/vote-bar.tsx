"use client";

import React, { useEffect } from "react";
import { motion } from "motion/react";
import { ThumbsUp, Scale, ThumbsDown, Sparkles } from "lucide-react";
import { Button } from "../ui/button";

interface VoteBarProps {
  canVote: boolean;
  isVoting: boolean;
  onVote: (choice: "A" | "B" | "tie" | "both_bad") => void;
}

export function VoteBar({ canVote, isVoting, onVote }: VoteBarProps) {
  // Keyboard shortcuts 1, 2, 3, 4
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!canVote || isVoting) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === "1") onVote("A");
      else if (e.key === "2") onVote("tie");
      else if (e.key === "3") onVote("both_bad");
      else if (e.key === "4") onVote("B");
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [canVote, isVoting, onVote]);

  const buttons = [
    {
      choice: "A" as const,
      label: "👈 Model A is better",
      key: "1",
      variant: "outline" as const,
      color: "hover:border-indigo-500 hover:text-indigo-400",
    },
    {
      choice: "tie" as const,
      label: "🤝 Tie",
      key: "2",
      variant: "outline" as const,
      color: "hover:border-amber-500 hover:text-amber-400",
    },
    {
      choice: "both_bad" as const,
      label: "👎 Both bad",
      key: "3",
      variant: "outline" as const,
      color: "hover:border-rose-500 hover:text-rose-400",
    },
    {
      choice: "B" as const,
      label: "Model B is better 👉",
      key: "4",
      variant: "outline" as const,
      color: "hover:border-purple-500 hover:text-purple-400",
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto my-4 text-center space-y-3">
      <div className="text-xs text-muted-foreground font-medium">
        {!canVote ? (
          <span className="flex items-center justify-center gap-1.5 animate-pulse text-muted-foreground/80">
            Waiting for both models to finish generating...
          </span>
        ) : (
          <span className="text-foreground/90 font-medium flex items-center justify-center gap-1">
            <Sparkles className="h-3.5 w-3.5 text-primary" /> Select the better answer or use keyboard shortcuts (1-4)
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {buttons.map((btn) => (
          <motion.div
            key={btn.choice}
            whileHover={canVote ? { scale: 1.02 } : {}}
            whileTap={canVote ? { scale: 0.98 } : {}}
          >
            <Button
              type="button"
              variant={btn.variant}
              disabled={!canVote || isVoting}
              onClick={() => onVote(btn.choice)}
              className={`w-full py-5 text-xs sm:text-sm font-semibold rounded-xl border-border/80 bg-card/80 transition-all ${btn.color} relative overflow-hidden`}
            >
              <span>{btn.label}</span>
              <kbd className="hidden sm:inline-block absolute right-2.5 top-2.5 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground/80 bg-muted/70 rounded border border-border/60">
                {btn.key}
              </kbd>
            </Button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

