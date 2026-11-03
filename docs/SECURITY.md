# Security Architecture & Anti-Leak Specifications — ModelArena

## 1. Anti-Leak Guarantee

The core integrity of **ModelArena** depends on strict blind evaluation. If a user or client can inspect model identities before voting, evaluation validity is compromised.

### 1.1. Technical Enforcements
1. **Battle Creation Payload:** `POST /api/battles` returns solely `{ battle_id, category }`. Model IDs, slugs, providers, and internal metadata are completely excluded from the JSON schema.
2. **SSE Stream Sanitization:** SSE event streams `/api/battles/{id}/stream/{slot}` emit only:
   - `event: token` with `{ "token": "..." }`
   - `event: done` with `{ "status": "completed" }`
   - `event: error` with sanitized generic messages.
   No server headers, event IDs, or chunk metadata reveal provider information.
3. **Automated Pytest Assertion:** [backend/tests/test_anti_leak.py](file:///c:/Users/vinee/project%201/modelarena/backend/tests/test_anti_leak.py) programmatically intercepts responses, headers, and SSE buffers to verify zero substring matches against model slugs prior to voting.

---

## 2. Authentication & Credential Security

### 2.1. Password Hashing (Argon2id)
- Passwords are encrypted using **Argon2id** (`argon2-cffi`), the winner of the Password Hashing Competition.
- Default parameters: Memory cost `65,536 KiB`, Time cost `3 iterations`, Parallelism `4 lanes`.

### 2.2. Token Lifecycle & Cookie Security
- **Access Tokens:** Short-lived JWT (15-minute expiration) containing user ID, role, and CSRF fingerprint.
- **Refresh Tokens:** Long-lived (7 days) cryptographically random tokens stored as SHA-256 hashes in `refresh_tokens`. Single-use rotation on each refresh; previous tokens are revoked immediately.
- **Cookie Flags:**
  - `HttpOnly`: Inaccessible to client JavaScript (XSS mitigation).
  - `SameSite=Lax`: Prevents CSRF on third-party site requests.
  - `Path=/`: Scoped to application root.
  - `Secure`: Enforced in production HTTPS environments.

### 2.3. Brute Force Protection
- Redis sliding counters monitor failed login attempts per IP and per email account.
- 5 failed attempts within 15 minutes triggers a temporary 15-minute lock on authentication endpoints.

---

## 3. Network & Transport Security

### 3.1. Cross-Origin Resource Sharing (CORS)
Configured in `backend/app/main.py`:
- `allow_credentials=True`
- Regular expression origin filtering: `allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"`
- Explicit origins specified in `.env` (`CORS_ORIGINS`).

### 3.2. Rate Limiting (Redis Sliding Window)
- **Anonymous battles:** Capped at 15 battles per hour per IP / anonymous session.
- **Authenticated battles:** Capped at 40 battles per hour per user account.
- Sliding window counters in Redis prevent burst abuse and denial-of-service on LLM provider backends.

---

## 4. Input Sanitization & Content Security

1. **Prompt Length Constraints:** Capped at 4,000 characters to prevent buffer and memory exhaustion.
2. **Markdown Rendering:** Frontend relies on `react-markdown` with strict HTML parsing disabled. Script tags and raw HTML injections are stripped automatically.
3. **Database Parameterization:** 100% of queries use SQLAlchemy 2.0 ORM expressions or parameterized binds, preventing SQL injection vulnerabilities.

