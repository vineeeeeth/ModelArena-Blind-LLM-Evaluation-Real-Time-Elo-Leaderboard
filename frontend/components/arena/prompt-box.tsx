"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import { Send, Sparkles, Code2, Calculator, Languages, FileText } from "lucide-react";
import { Button } from "../ui/button";

interface PromptBoxProps {
  onSubmit: (prompt: string, category?: string) => void;
  isLoading: boolean;
}

const CATEGORIES = [
  { id: "auto", label: "Auto Detect", icon: Sparkles },
  { id: "coding", label: "Coding", icon: Code2 },
  { id: "math", label: "Math", icon: Calculator },
  { id: "hindi", label: "Hindi", icon: Languages },
  { id: "summarization", label: "Summarization", icon: FileText },
];

const SUGGESTIONS = [
  {
    category: "coding",
    text: "Write a high-performance LRU Cache in TypeScript with O(1) get and put.",
  },
  {
    category: "math",
    text: "Evaluate the limit as x approaches 0 of (sin(x) - x) / x^3 using Taylor series.",
  },
  {
    category: "hindi",
    text: "भारतीय संस्कृति में 'वसुधैव कुटुम्बकम्' के विचार का ऐतिहासिक और वर्तमान महत्व समझाइए।",
  },
  {
    category: "general",
    text: "What would happen to Earth's climate and tides if the Moon suddenly broke apart?",
  },
];

export function PromptBox({ onSubmit, isLoading }: PromptBoxProps) {
  const [prompt, setPrompt] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("auto");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onSubmit(
      prompt.trim(),
      selectedCategory === "auto" ? undefined : selectedCategory
    );
  };

  const maxChars = 4000;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="w-full max-w-4xl mx-auto space-y-4"
    >
      <form onSubmit={handleSubmit} className="relative rounded-2xl border border-border/60 bg-card/60 p-4 backdrop-blur-lg shadow-xl shadow-black/5 dark:shadow-purple-950/10">
        {/* Category Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pb-3 border-b border-border/40">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setSelectedCategory(cat.id)}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all ${
                  isSelected
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {cat.label}
              </button>
            );
          })}
        </div>

        {/* Text Area */}
        <div className="py-2">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value.slice(0, maxChars))}
            placeholder="Type your prompt here... (e.g. ask a difficult coding problem, a complex math question, or in Hindi)"
            rows={4}
            className="w-full resize-none bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none text-base sm:text-lg leading-relaxed"
            disabled={isLoading}
          />
        </div>

        {/* Bottom Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-border/40">
          <span className="text-xs font-mono text-muted-foreground">
            {prompt.length} / {maxChars}
          </span>

          <Button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="gap-2 px-6 shadow-md shadow-primary/20"
          >
            {isLoading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span>Generate Battle</span>
          </Button>
        </div>
      </form>

      {/* Suggestion Chips */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <span className="text-xs text-muted-foreground flex items-center gap-1">
          <Sparkles className="h-3 w-3" /> Try an example:
        </span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              setPrompt(s.text);
              if (s.category !== "general") setSelectedCategory(s.category);
            }}
            className="rounded-lg border border-border/60 bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors truncate max-w-[280px]"
          >
            {s.text}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

