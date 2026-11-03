# Design System Specification — ModelArena

## 1. Overview & Aesthetic Philosophy

**ModelArena** employs a sleek, modern, developer-centric **dark-mode first** interface. The aesthetic emphasizes clean visual hierarchies, smooth micro-interactions via `motion/react`, high-contrast typography, and accessible visual indicators for state transitions.

---

## 2. Color Palette & Theming (Tailwind CSS & HSL Tokens)

The design system maps semantic tokens to HSL variables configured in `tailwind.config.ts` and `globals.css`:

### 2.1. Base Colors
| Semantic Token | Light Mode (HSL) | Dark Mode (HSL) | Purpose |
| :--- | :--- | :--- | :--- |
| `background` | `0 0% 100%` (`#ffffff`) | `224 71% 4%` (`#030712`) | Root canvas background |
| `foreground` | `224 71% 4%` | `210 40% 98%` | Primary readable text |
| `card` | `0 0% 100%` | `222 47% 7%` (`#090d16`) | Surface cards, battle panels |
| `card-foreground`| `224 71% 4%` | `210 40% 98%` | Card textual content |
| `border` | `220 13% 91%` | `217 33% 17%` | Subtle container borders |
| `muted` | `220 14% 96%` | `217 33% 12%` | Inactive pills, skeletons |
| `muted-foreground` | `220 9% 46%` | `215 20% 65%` | Secondary labels, timestamps |

### 2.2. Brand & Intent Accents
- **Primary (`indigo` / `violet`):** `hsl(263 70% 50%)` — Main action buttons, active tabs, glowing indicators.
- **Slot A Accent (`indigo`):** `text-indigo-400`, `border-indigo-500/30`, `bg-indigo-500/10`
- **Slot B Accent (`purple`):** `text-purple-400`, `border-purple-500/30`, `bg-purple-500/10`
- **Success / Done (`emerald`):** `text-emerald-400`, `bg-emerald-500/10`, `border-emerald-500/20`
- **Destructive / Error (`rose`):** `text-rose-400`, `bg-rose-500/10`, `border-rose-500/20`
- **Warning / Tie (`amber`):** `text-amber-400`, `bg-amber-500/10`, `border-amber-500/20`

---

## 3. Typography Hierarchy

- **Font Family:** Inter / system-ui (`sans-serif`), with JetBrains Mono / Fira Code for monospace code displays.
- **Headings:**
  - `H1 (Hero)`: `text-4xl sm:text-5xl font-extrabold tracking-tight`
  - `H2 (Section)`: `text-2xl sm:text-3xl font-bold tracking-tight`
  - `H3 (Card title)`: `text-lg sm:text-xl font-semibold`
- **Body:** `text-sm sm:text-base leading-relaxed text-foreground/90`
- **Captions & Metadata:** `text-xs font-mono text-muted-foreground`

---

## 4. UI Components

### 4.1. Battle Panels (`BattleView`)
- **Structure:** Dual-column grid (`grid grid-cols-1 md:grid-cols-2 gap-4`).
- **Container:** Rounded `rounded-2xl`, translucent backdrop `bg-card/70 backdrop-blur-md`, subtle border `border border-border/70`, elevation shadow.
- **Streaming State:**
  - *Initial / Thinking:* Shimmer skeleton placeholders (`Skeleton className="h-4 w-full"`).
  - *Streaming:* Progressive Markdown renderer with an active pulsing caret (`w-2 h-4 bg-primary animate-pulse`).
  - *Status Badge:* 
    - Streaming: `<Loader2 className="animate-spin text-primary" /> Thinking...`
    - Finished: `<CheckCircle2 className="text-emerald-500" /> Done`

### 4.2. Category Selector Chips (`PromptBox`)
- **Pills:** Horizontal scrollable cluster of category buttons (Auto, Coding, Math, Hindi, Summarization).
- **Active State:** Solid primary fill `bg-primary text-primary-foreground shadow-sm`.
- **Inactive State:** `bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground`.

### 4.3. Voting Action Bar (`VoteBar`)
- **Grid Layout:** 4 action tiles (`Model A is better`, `Tie`, `Both bad`, `Model B is better`).
- **Interaction Feedback:** Motion hover `scale: 1.02` and tap `scale: 0.98`.
- **Keyboard Badges:** Inline `<kbd>` chips displaying shortcuts `1`, `2`, `3`, `4`.

### 4.4. Reveal Animation (`RevealAnimation`)
- **Transition:** AnimatePresence with spring physics (`stiffness: 300, damping: 25`).
- **Card Breakdown:** Reveals Model name, Provider tag, TTFT, Total Latency, Token counts, and computed Cost ($ USD).

---

## 5. Animation Guidelines (`motion/react`)

1. **Page Transitions:** Fade and subtle Y-offset slide (`initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}`).
2. **Micro-interactions:** Button hover scale capped at 1.02; active tap scale 0.98.
3. **SSE Scroll Auto-Following:** Smooth auto-scroll behavior tracking `scrollRef.scrollTop = scrollRef.scrollHeight` during token streaming.

