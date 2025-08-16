from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body

from app.auth import require_token
from app.cleaning import clean_content
from app.rate_limit import rate_limit

app = FastAPI(title="Content Cleaner API")

# serve static (for the logo)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS (handy if you ever call from a separate frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------- API -------------

@app.post("/clean")
async def clean(payload: dict = Body(...), token: str = Depends(require_token)):
    if not rate_limit(token):
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

    text = payload.get("text")
    if not isinstance(text, str):
        return JSONResponse({"detail": "Missing text"}, status_code=400)

    cleaned = clean_content(text)
    return {"clean": cleaned}


# ------------- Frontend (Homepage) -------------
@app.get("/", response_class=HTMLResponse)
async def home():
    # NOTE: put your logo file at: app/static/content-cleaner-welcoming-page.png
    return """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Content Cleaner Demo</title>
<style>
  :root{
    --brand:#f5a300;        /* your yellow/orange */
    --brand-dark:#d48e00;
    --ink:#2f2f2f;          /* dark gray text */
    --muted:#6e6e6e;
    --panel:#f5f5f5;        /* light gray result bg */
    --card:#ffffff;
    --ring:rgba(245,163,0,.35);
    --radius:14px;
    --shadow:0 10px 30px rgba(0,0,0,.08);
  }
  *{box-sizing:border-box}
  html,body{margin:0}
  body{
    font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    color:var(--ink);
    background:#fff;
  }
  .wrap{
    max-width:900px;
    margin:40px auto 64px;
    padding:0 20px;
  }

  /* hero */
  .hero{
    text-align:center;
    margin-bottom:28px;
  }
  .logo{
    width:240px;
    max-width:60vw;
    display:block;
    margin:0 auto 8px;
  }
  .title{
    font-weight:800;
    font-size:clamp(24px, 3.4vw, 36px);
    letter-spacing:.2px;
  }
  .title .accent{ color:var(--brand); }

  /* card */
  .card{
    background:var(--card);
    border-radius:var(--radius);
    box-shadow:var(--shadow);
    padding:24px;
  }
  .card h2{
    margin:0 0 12px 0;
    font-size:clamp(18px, 2.4vw, 22px);
  }
  .hint{ color:var(--muted); margin:0 0 18px 0; }

  /* form */
  .grid{
    display:grid;
    gap:18px;
    grid-template-columns:1fr;
  }
  @media (min-width: 860px){
    .grid{ grid-template-columns:1fr 1fr; }
  }
  label{
    display:block;
    font-weight:700;
    margin:0 0 8px;
  }
  textarea{
    width:100%;
    min-height:200px;
    resize:vertical;
    padding:12px 14px;
    border:1.5px solid #e6e6e6;
    border-radius:12px;
    outline:none;
    font:inherit;
    line-height:1.4;
  }
  textarea:focus{
    border-color:var(--brand);
    box-shadow:0 0 0 4px var(--ring);
  }
  .controls{
    display:flex; gap:10px; align-items:center; margin:10px 0 2px;
    flex-wrap:wrap;
  }
  .token{
    flex:1 1 260px;
    padding:10px 12px;
    border:1.5px solid #e6e6e6;
    border-radius:12px;
    outline:none;
  }
  .token:focus{ border-color:var(--brand); box-shadow:0 0 0 4px var(--ring); }

  .btn{
    appearance:none;
    border:0;
    background:var(--brand);
    color:#1b1b1b;
    font-weight:800;
    padding:12px 20px;
    border-radius:999px;
    cursor:pointer;
    transition:transform .05s ease, background .15s ease;
    box-shadow:0 6px 14px rgba(245,163,0,.35);
    white-space:nowrap;
  }
  .btn:hover{ background:var(--brand-dark); }
  .btn:active{ transform:translateY(1px); }

  /* result panel styled like your mock (gray block) */
  .result{
    background:var(--panel);
    border:1.5px solid #e6e6e6;
    border-radius:12px;
    padding:14px;
    min-height:200px;
    white-space:pre-wrap;
    overflow:auto;
  }

  .footer-note{
    text-align:center;
    color:var(--muted);
    margin:20px 0 0;
    font-size:14px;
  }
</style>
</head>
<body>
  <div class="wrap">
    <!-- Hero -->
    <div class="hero">
      <img class="logo" src="/static/content-cleaner-welcoming-page.png" alt="Content Cleaner Logo" />
      <div class="title">Content <span class="accent">Cleaner</span> Demo</div>
    </div>

    <!-- Clean section card -->
    <div class="card">
      <h2>Enter raw HTML or text below</h2>
      <p class="hint">Paste messy content on the left and click <b>Clean</b>. Result appears on the right.</p>

      <div class="controls">
        <input id="token" class="token" placeholder="Bearer token (default: dev-token)" />
        <button id="run" class="btn">Clean</button>
      </div>

      <div class="grid">
        <div>
          <label for="input">Input</label>
          <textarea id="input" placeholder="<p>Hello&nbsp;&nbsp;— world<br><br>zero\u200bwidth</p>"></textarea>
        </div>
        <div>
          <label for="output">Result :</label>
          <div id="output" class="result" aria-live="polite"></div>
        </div>
      </div>
    </div>

    <p class="footer-note">Tip: use <b>dev-token</b> if you didn't change tokens.</p>
  </div>

<script>
  const $ = (id) => document.getElementById(id);

  // Try to remember the last token locally
  const savedToken = localStorage.getItem("cc_token");
  if (savedToken) $("token").value = savedToken;

  $("run").addEventListener("click", async () => {
    const text = $("input").value;
    const token = ($("token").value || "dev-token").trim();
    localStorage.setItem("cc_token", token);

    $("run").disabled = true;
    $("run").innerText = "Cleaning…";

    try {
      const res = await fetch("/clean", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ text })
      });

      const data = await res.json();
      if (!res.ok) {
        $("output").textContent = `${res.status} ${res.statusText}\n${data.detail || JSON.stringify(data)}`;
      } else {
        $("output").textContent = data.clean || "";
      }
    } catch (e) {
      $("output").textContent = "Network error: " + e;
    } finally {
      $("run").disabled = false;
      $("run").innerText = "Clean";
    }
  });
</script>
</body>
</html>
    """
