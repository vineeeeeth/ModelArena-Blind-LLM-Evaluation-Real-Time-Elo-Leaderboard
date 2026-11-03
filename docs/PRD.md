# Product Requirements Document (PRD) — ModelArena

## 1. Executive Summary

**ModelArena** is a blind, head-to-head LLM (Large Language Model) evaluation platform with an online Elo and Bradley-Terry MLE leaderboard. 

Users submit prompts across specialized domains and receive real-time, side-by-side answers from two anonymous LLMs without knowing which model produced which response. Users vote on the superior response (**Model A is better**, **Model B is better**, **Tie**, or **Both bad**). Upon voting, the platform triggers an interactive reveal sequence displaying model identities, tokens generated, time-to-first-token (TTFT), total latency, and estimated cost.

All interactions feed directly into a real-time rating engine running an **online Elo rating system** backed by asynchronous **Bradley-Terry Maximum Likelihood Estimation (MLE)** with **bootstrap confidence intervals** and pairwise win matrices.

---

## 2. Target Audience & Core Personas

1. **AI Researchers & Evaluators:** Seeking empirical, unbiased, crowd-sourced evaluations of LLM performance without prompt gaming or marketing bias.
2. **Software Engineers & Developers:** Deciding which model offers the best accuracy-to-latency/cost ratio for coding, math, or reasoning workloads.
3. **General Public & Multilingual Users:** Exploring model nuances in English and non-Latin scripts (e.g., Hindi in Devanagari).
4. **Platform Administrators:** Managing active model rosters, monitoring abuse metrics, and adjusting pricing tiers.

---

## 3. Product Principles (Non-Negotiables)

1. **Zero Fake Data / No In-Memory Placeholders:** Every metric, ranking, token count, and latency on screen originates from live PostgreSQL queries, Redis counters, and actual LLM inference.
2. **Anti-Leak Guarantee:** Model identities are never returned in battle creation responses, SSE streams, response payloads, client-accessible headers, or unvoted database states.
3. **Anonymous-First Voting with Frictionless Accounts:** Visitors can immediately test models anonymously via HTTP-only session cookies. Optional accounts (email/password with Argon2id and Google OAuth) unlock voting history and abuse protection perks.
4. **Frontier-Calibrated Sampling:** Models are paired with anti-hallucination system instructions and low-temperature sampling (0.1–0.3) to maximize factual precision and code correctness.

---

## 4. Key Functional Features

### 4.1. Blind Battle Generation
- **Prompt Submission:** Accepts prompts up to 4,000 characters.
- **Category Classification:** Automatic prompt classification via `classifier.py` into five distinct categories:
  - `General`: Universal factual and conversational inquiries.
  - `Coding`: Programmatic queries, script tasks, software engineering problems.
  - `Math`: Numerical calculations, algebraic derivations, proofs.
  - `Hindi`: Devanagari script detection and cultural/linguistic queries.
  - `Summarization`: Extraction, distillation, and synthesis tasks.
  - *User Override:* Users can manually toggle the category pill before submission.
- **Pair Selection Algorithm:** Selects two distinct enabled models, weighted towards under-sampled pairs to ensure uniform pairwise comparison matrices.
- **Slot Randomization:** Eliminates position bias by randomly assigning selected models to Slot A or Slot B.

### 4.2. Dual Concurrent Streaming
- **Server-Sent Events (SSE):** Dual concurrent streams emit tokens via `/api/battles/{id}/stream/A` and `/api/battles/{id}/stream/B`.
- **Live Metrics Tracking:**
  - Time to First Token (TTFT in milliseconds).
  - Total latency (milliseconds).
  - Input tokens and output tokens.
  - Estimated inference cost ($ USD).

### 4.3. Voting & Identity Reveal
- **Vote Actions:** `A is better (1)`, `Tie (2)`, `Both bad (3)`, `Model B is better (4)`.
- **Keyboard Shortcuts:** Keyboard numbers `1`, `2`, `3`, `4` trigger respective vote actions.
- **Vote Validity Rules:**
  - Votes are locked until both models finish generating (`status == ready`).
  - Single vote per battle (enforced by DB unique constraint `uq_votes_battle_id`).
  - Speed limit: Suspiciously fast votes (< 1,500 ms) are rejected.
- **Reveal Sequence:** Motion animation reveals model names, provider badges, latency, token count, and cost breakdown.

### 4.4. Leaderboard & Statistical Dashboard
- **Rankings Table:** Displays Rank, Model, Provider, Elo Rating, Bradley-Terry Score with 95% Bootstrap Confidence Intervals (`[ci_low, ci_high]`), Win Rate, Number of Battles, Average Latency, and Cost.
- **Category Filtering:** Filter rankings across All, Coding, Math, Hindi, Summarization, and General.
- **Pairwise Win Matrix:** Interactive heatmap displaying model head-to-head win percentages.
- **Cost vs. Latency Scatter Chart:** Interactive chart plotting cost ($/Mtok) vs. median latency.
- **Historical Elo Trends:** Line charts showing rating trajectories over time.

---

## 5. Non-Functional Requirements

- **Performance:** SSE token latency < 100ms first token overhead from proxy.
- **Availability:** Dockerized services running with health checks on Postgres, Redis, and Ollama.
- **Security:** CSRF protection, Argon2id password hashing, HTTP-only secure cookie sessions, SQL injection prevention via SQLAlchemy 2.0 ORM, strict sanitized Markdown rendering.
- **Compatibility:** Modern web browsers (Chrome, Firefox, Safari, Edge) with full dark-mode responsive design.

