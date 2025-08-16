# Content Cleaner
REST API to remove AI/Word/HTML artifacts and invisible Unicode.

## Run
1) Copy env: `.env.example` → `.env` (keep API_TOKENS=dev-token).
2) Install: `pip install -r requirements.txt`
3) Start: `uvicorn app.main:app --reload`
4) Try GUI at `/` or API docs at `/docs`.

## API
POST /clean
Auth: Authorization: Bearer <token>
Body: { "text": "<raw-content>" }
Response: { "clean": "<cleaned-content>" }
