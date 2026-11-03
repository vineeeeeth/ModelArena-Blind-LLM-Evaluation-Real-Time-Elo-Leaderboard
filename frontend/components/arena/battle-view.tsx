"use client";

import React, { useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Bot, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { MarkdownRenderer } from "../markdown-renderer";
import { Skeleton } from "../ui/skeleton";
import { Badge } from "../ui/badge";

interface BattleViewProps {
  slotA: {
    tokens: string;
    isDone: boolean;
    isStarted: boolean;
    error: string | null;
  };
  slotB: {
    tokens: string;
    isDone: boolean;
    isStarted: boolean;
    error: string | null;
  };
}

export function BattleView({ slotA, slotB }: BattleViewProps) {
  const scrollRefA = useRef<HTMLDivElement>(null);
  const scrollRefB = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom smoothly during stream
  useEffect(() => {
    if (scrollRefA.current && !slotA.isDone) {
      scrollRefA.current.scrollTop = scrollRefA.current.scrollHeight;
    }
  }, [slotA.tokens, slotA.isDone]);

  useEffect(() => {
    if (scrollRefB.current && !slotB.isDone) {
      scrollRefB.current.scrollTop = scrollRefB.current.scrollHeight;
    }
  }, [slotB.tokens, slotB.isDone]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-6xl mx-auto my-6">
      {/* Slot A */}
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col h-[520px] rounded-2xl border border-border/70 bg-card/70 backdrop-blur-md overflow-hidden shadow-lg"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border/50 bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500 font-semibold text-xs border border-indigo-500/20">
              A
            </div>
            <span className="font-semibold text-sm">Model A</span>
          </div>

          <div>
            {slotA.isDone ? (
              <Badge variant="secondary" className="gap-1 bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-xs">
                <CheckCircle2 className="h-3 w-3" /> Done
              </Badge>
            ) : slotA.isStarted ? (
              <Badge variant="outline" className="gap-1.5 animate-pulse text-xs">
                <Loader2 className="h-3 w-3 animate-spin text-primary" /> Thinking...
              </Badge>
            ) : null}
          </div>
        </div>

        {/* Content Body */}
        <div ref={scrollRefA} className="flex-1 overflow-y-auto p-5 scroll-smooth">
          {slotA.error ? (
            <div className="flex items-center gap-2 text-destructive text-sm p-4 rounded-lg bg-destructive/10">
              <AlertCircle className="h-4 w-4" />
              <span>{slotA.error}</span>
            </div>
          ) : !slotA.tokens && !slotA.isDone ? (
            <div className="space-y-3 pt-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ) : (
            <div className="relative">
              <MarkdownRenderer content={slotA.tokens} />
              {!slotA.isDone && (
                <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse align-middle" />
              )}
            </div>
          )}
        </div>
      </motion.div>

      {/* Slot B */}
      <motion.div
        initial={{ opacity: 0, x: 10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col h-[520px] rounded-2xl border border-border/70 bg-card/70 backdrop-blur-md overflow-hidden shadow-lg"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border/50 bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500 font-semibold text-xs border border-purple-500/20">
              B
            </div>
            <span className="font-semibold text-sm">Model B</span>
          </div>

          <div>
            {slotB.isDone ? (
              <Badge variant="secondary" className="gap-1 bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-xs">
                <CheckCircle2 className="h-3 w-3" /> Done
              </Badge>
            ) : slotB.isStarted ? (
              <Badge variant="outline" className="gap-1.5 animate-pulse text-xs">
                <Loader2 className="h-3 w-3 animate-spin text-primary" /> Thinking...
              </Badge>
            ) : null}
          </div>
        </div>

        {/* Content Body */}
        <div ref={scrollRefB} className="flex-1 overflow-y-auto p-5 scroll-smooth">
          {slotB.error ? (
            <div className="flex items-center gap-2 text-destructive text-sm p-4 rounded-lg bg-destructive/10">
              <AlertCircle className="h-4 w-4" />
              <span>{slotB.error}</span>
            </div>
          ) : !slotB.tokens && !slotB.isDone ? (
            <div className="space-y-3 pt-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ) : (
            <div className="relative">
              <MarkdownRenderer content={slotB.tokens} />
              {!slotB.isDone && (
                <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse align-middle" />
              )}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

