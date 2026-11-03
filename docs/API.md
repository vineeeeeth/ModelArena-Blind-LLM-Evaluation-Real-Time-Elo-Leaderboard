# REST & SSE API Specification — ModelArena

## 1. Overview & Base URLs

- **API Base URL:** `http://localhost:8000/api`
- **Frontend URL:** `http://localhost:3000`
- **Data Formats:** JSON for request/response payloads; `text/event-stream` for SSE token delivery.
- **Authentication:** HTTP-only cookies (`arena_session`, `access_token`, `refresh_token`).

---

## 2. Battles API (`/api/battles`)

### 2.1. Create Battle
Initializes a new blind comparison between two randomized models.

- **Endpoint:** `POST /api/battles`
- **Rate Limit:** Anonymous: 15/hr; Authenticated: 40/hr.
- **Request Body:**
  ```json
  {
    "prompt": "Write an LRU Cache in Python with O(1) operations.",
    "category": "coding" // optional, defaults to auto-classification
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "battle_id": "74208c99-1db7-4d6d-a71b-4fe3fdcbe8f1",
    "category": "coding"
  }
  ```
  *(Anti-Leak: Model identities are never returned here.)*

---

### 2.2. Stream Model Output (SSE)
Streams tokens for a single slot.

- **Endpoint:** `GET /api/battles/{battle_id}/stream/{slot}`
- **Parameters:**
  - `battle_id` (UUID): ID returned by battle creation.
  - `slot` (string): `'A'` or `'B'`.
- **Response Format:** `text/event-stream`
- **SSE Events:**
  - `event: token`
    ```json
    data: {"token": "class "}
    ```
  - `event: done`
    ```json
    data: {"status": "completed"}
    ```
  - `event: error`
    ```json
    data: {"error": "Generation failed. Try again."}
    ```

---

### 2.3. Submit Vote & Reveal
Records the user's vote and returns the true identities and performance metrics.

- **Endpoint:** `POST /api/battles/{battle_id}/vote`
- **Constraints:**
  - Status must be `ready` (both models finished).
  - Enforced single vote per battle (`409 Conflict` on duplicates).
  - Minimum vote time: 1,500 ms (`400 Bad Request` if suspiciously fast).
- **Request Body:**
  ```json
  {
    "choice": "A", // "A" | "B" | "tie" | "both_bad"
    "time_to_vote_ms": 2840
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "choice": "A",
    "responses": [
      {
        "slot": "A",
        "model_name": "Google Gemini Flash",
        "model_slug": "gemini-flash",
        "input_tokens": 18,
        "output_tokens": 420,
        "ttft_ms": 340,
        "total_latency_ms": 1820,
        "cost_usd": 0.000127
      },
      {
        "slot": "B",
        "model_name": "Qwen 2.5 3B",
        "model_slug": "qwen-2.5-3b",
        "input_tokens": 18,
        "output_tokens": 390,
        "ttft_ms": 480,
        "total_latency_ms": 2450,
        "cost_usd": 0.0
      }
    ]
  }
  ```

---

## 3. Leaderboard & Statistics API (`/api/leaderboard`, `/api/stats`)

### 3.1. Fetch Leaderboard
- **Endpoint:** `GET /api/leaderboard`
- **Query Parameters:**
  - `category` (string, optional): `general`, `coding`, `math`, `hindi`, `summarization`. Omit for overall.
  - `include_simulated` (boolean, optional, default `true`).
- **Response (`200 OK`):**
  ```json
  {
    "category": null,
    "entries": [
      {
        "model_id": 6,
        "model_slug": "gpt-4o",
        "model_name": "GPT-4o",
        "provider": "openai",
        "is_open_source": false,
        "elo": 1270.56,
        "bt_score": 1270.56,
        "ci_low": 1170.25,
        "ci_high": 1353.58,
        "rank": 1,
        "num_battles": 219,
        "win_rate": 0.8607,
        "avg_latency_ms": 1384.29,
        "avg_cost_usd": 0.00404,
        "is_provisional": false
      }
    ]
  }
  ```

---

### 3.2. Pairwise Win Matrix
- **Endpoint:** `GET /api/stats/win-matrix`
- **Query Parameters:** `category` (optional)
- **Response (`200 OK`):** Returns matrix of model pairs with $A$ win percentage, $B$ win percentage, and tie counts.

---

### 3.3. Cost vs Latency Distribution
- **Endpoint:** `GET /api/stats/cost-latency`
- **Response (`200 OK`):** Returns average cost per million tokens, TTFT, and total latency for all active models.

---

## 4. Authentication Endpoints (`/api/auth`)

- `POST /api/auth/signup`: Create email/password user account.
- `POST /api/auth/login`: Authenticate and set rotating HTTP-only refresh and access cookies.
- `POST /api/auth/logout`: Invalidate refresh token in database and clear cookies.
- `GET /api/auth/me`: Fetch currently authenticated user profile and battle statistics.
- `POST /api/auth/forgot-password`: Send password reset link via SMTP.
- `POST /api/auth/reset-password`: Set new password with verified reset token.

---

## 5. System Health (`/api/health`)

- **Endpoint:** `GET /api/health`
- **Response (`200 OK`):**
  ```json
  {
    "status": "ok",
    "db": "ok",
    "redis": "ok",
    "ollama": "ok"
  }
  ```

