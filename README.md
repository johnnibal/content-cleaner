# 🧹 Content Cleaner API

FastAPI microservice that **cleans and normalizes text/HTML**.  
Includes **Bearer token auth**, a **per-token rate limit**, and a **tiny web UI** at `/`.

---

## ✨ What it does

- **HTML → text**: strips Word junk (`<o:p>`, `<style>`, `<script>`), unwraps `div/span`, converts `<br>` → newlines, drops empty `<p>`.
- **Removes invisible & control chars**: ZWSP (`U+200B`), ZWJ/ZWNJ, NBSP, FEFF, soft hyphen, etc.  
  Preserves `\n / \r / \t` so line breaks remain readable.
- **Normalizes dashes**: em/en/minus/figure/three-em → `-`, adds spacing (e.g. `Hello—world` → `Hello - world`).
- **Whitespace tidy**: collapses extra spaces/tabs, trims around newlines, limits blank lines.
- **Robust to literal escapes**: turns `\\u200b` into the real char and removes it; drops stray backslashes like `\width`.

---

## 🚀 Run it

### Local
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
Docker
bash
Copy
Edit
docker-compose up --build
Open:

UI: http://127.0.0.1:8000/

API docs: http://127.0.0.1:8000/docs

🔑 Authentication
All API calls require a Bearer token header:

makefile
Copy
Edit
Authorization: Bearer dev-token
Configure via .env:

ini
Copy
Edit
API_TOKENS=dev-token,another-token
BLOCKED_TOKENS=
RATE_LIMIT_RPM=60
Errors: 401 (missing/invalid), 403 (blocked), 429 (rate limit).

🧪 API
Endpoint: POST /clean
Headers: Authorization: Bearer <token>
Body:

json
Copy
Edit
{ "text": "<raw content or HTML>" }
Response:

json
Copy
Edit
{ "clean": "<normalized plain text>" }
Example
bash
Copy
Edit
curl -X POST "http://127.0.0.1:8000/clean" \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{ "text": "<p>Hello&nbsp;&nbsp;— world<br><br>zero\\u200bwidth</p>" }'
Response:

json
Copy
Edit
{ "clean": "Hello - world\n\nzerowidth" }
🖥️ Web UI (optional)
Open http://127.0.0.1:8000/

Paste messy content on the left

Enter token (defaults to dev-token)

Click Clean → see normalized text on the right
The page is responsive and includes your logo.

📂 Structure
bash
Copy
Edit
app/
 ├─ main.py         # API + web UI (homepage)
 ├─ auth.py         # Bearer token enforcement
 ├─ rate_limit.py   # Sliding-window limiter (per token)
 └─ cleaning.py     # HTML/text cleaning pipeline
requirements.txt
.env.example
Dockerfile
docker-compose.yml