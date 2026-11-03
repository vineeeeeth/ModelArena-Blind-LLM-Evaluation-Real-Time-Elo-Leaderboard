# Code Style & Engineering Standards — ModelArena

## 1. Engineering Philosophy

**ModelArena** enforces strict typing, modular separation of concerns, and clean architectural boundaries. There are no mocks, no untyped objects, and no uncontrolled side effects.

---

## 2. Backend Guidelines (Python 3.12 / FastAPI)

### 2.1. Typing & Imports
- **Always enable future annotations:**
  ```python
  from __future__ import annotations
  ```
- **Type Annotations:** All functions, methods, parameters, and return types must be fully annotated with Python 3.12 syntax (`str | None` rather than `Optional[str]`, `list[str]` instead of `List[str]`).
- **Pydantic v2 Models:** Use Pydantic v2 schemas for all API payloads. Inherit from `BaseModel` and utilize `model_config = ConfigDict(...)` where applicable.

### 2.2. Database & Asynchronous I/O
- **SQLAlchemy 2.0 Syntax:**
  ```python
  # Correct (2.0 style):
  result = await db.execute(select(Model).where(Model.is_enabled.is_(True)))
  models = result.scalars().all()

  # Avoid (1.4 legacy query style):
  # db.query(Model).filter(...)
  ```
- **Session Management:** All database operations use `AsyncSession` yielded by `get_db` dependency. Never execute blocking synchronous database queries in request handlers.

### 2.3. Logging Standards (`structlog`)
Never use bare `print()` statements in production code. Use structured contextual logs:
```python
from app.core.logging import logger

logger.info(
    "battle_created",
    battle_id=str(battle.id),
    category=battle.category.value,
    model_a=model_a.slug,
    model_b=model_b.slug,
)
```

---

## 3. Frontend Guidelines (Next.js 15 / TypeScript)

### 3.1. Strict TypeScript
- `tsconfig.json` runs in strict mode (`"strict": true`).
- No `any` types unless interfacing with un-typed third-party payloads, in which case explicit type assertions or `unknown` with runtime guards must be used.
- Explicit interfaces for all API response objects (e.g., `VoteResult`, `ResponseReveal`, `LeaderboardEntry`).

### 3.2. React 19 & Component Architecture
- Use `"use client";` explicitly at the top of client-side interactive components.
- Components must be functional and stateless where possible; server state belongs in TanStack Query.
- Use `shadcn/ui` conventions (`components/ui/`) with `clsx` and `tailwind-merge` (`cn(...)` utility).

### 3.3. Motion Guidelines (`motion/react`)
- Import animations strictly from `motion/react`:
  ```typescript
  import { motion, AnimatePresence } from "motion/react";
  ```
- Avoid importing from legacy `framer-motion` to maintain compatibility with modern bundlers.

---

## 4. Testing Standards (pytest & Playwright)

1. **Pytest (Backend):**
   - Rating mathematics must be verified analytically with known Elo and Bradley-Terry test fixtures.
   - Anti-leak verification tests must assert that model slugs do not appear in battle generation or SSE payloads before voting.
   - Run via: `pytest`
2. **Playwright (Frontend E2E):**
   - Test one full happy-path: prompt submission $\to$ SSE streaming $\to$ vote $\to$ reveal animation $\to$ leaderboard update.

