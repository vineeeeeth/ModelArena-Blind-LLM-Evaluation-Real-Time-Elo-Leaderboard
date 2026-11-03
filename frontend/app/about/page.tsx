import React from "react";
import { BookOpen, Scale, Award, ShieldAlert, Cpu, BarChart2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-8 sm:py-12 space-y-8">
      <div className="space-y-3">
        <h1 className="text-4xl font-extrabold tracking-tight">Methodology & Design</h1>
        <p className="text-lg text-muted-foreground">
          How ModelArena provides statistically robust, unbiased evaluations of Large Language Models.
        </p>
      </div>

      <div className="space-y-6">
        {/* 1. Blind Evaluation */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Scale className="h-5 w-5 text-indigo-500" />
              <span>1. Blind Head-to-Head Testing</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
            <p>
              When a user submits a prompt, ModelArena randomly selects two distinct enabled models.
              To eliminate position bias, the models are randomly assigned to either Slot A or Slot B.
            </p>
            <p>
              Crucially, neither the model names, providers, latency headers, nor token metrics are
              transmitted to the browser prior to the vote. This strict anti-leak guarantee ensures
              that human judgment is based solely on the quality of the generated answers.
            </p>
          </CardContent>
        </Card>

        {/* 2. Rating Algorithms */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Award className="h-5 w-5 text-amber-500" />
              <span>2. Online Elo & Bradley-Terry MLE</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
            <p>
              ModelArena uses a dual-engine rating approach:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>
                <strong className="text-foreground">Online Elo (K=32):</strong> Provides immediate score updates
                upon every submitted vote, with initial rating set to 1000.
              </li>
              <li>
                <strong className="text-foreground">Bradley-Terry Maximum Likelihood Estimation:</strong> Fits
                a logistic regression model over all historical decisive and tie votes (ties count as 0.5 win
                for each model). The latent ability parameters are scaled to an Elo-like distribution:
                <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono text-primary ml-1">
                  Score = 1000 + (400 / ln(10)) * (γ - mean(γ))
                </code>
              </li>
            </ul>
          </CardContent>
        </Card>

        {/* 3. Bootstrap Confidence Intervals */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <BarChart2 className="h-5 w-5 text-purple-500" />
              <span>3. Bootstrap Confidence Intervals & CI-Aware Rank</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
            <p>
              Pairwise rankings without uncertainty estimates can be misleading. ModelArena runs non-parametric
              bootstrap resampling (200 to 1,000 iterations with replacement) over the entire vote corpus.
            </p>
            <p>
              The 2.5th and 97.5th percentiles of the bootstrap distribution establish the 95% Confidence Interval.
              A model's ranking is considered provisional until it has participated in at least 20 battles.
            </p>
          </CardContent>
        </Card>

        {/* 4. Anti-Abuse & Vote Integrity */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-500" />
              <span>4. Vote Integrity & Anti-Spam</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
            <p>
              To maintain leaderboard integrity:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Rate limiting is enforced per IP and per user session via Redis sliding windows.</li>
              <li>Votes cast in under 1.5 seconds after generation are rejected to prevent automated click farms.</li>
              <li>Database unique constraints guarantee that each battle can only receive exactly one vote.</li>
              <li>Simulated demo data is tagged with <code className="text-xs bg-muted px-1 rounded font-mono">is_simulated = true</code> and can be toggled on or off at any time.</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

