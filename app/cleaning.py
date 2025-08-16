import re
from bs4 import BeautifulSoup

# ---------- HTML handling (strip junk, extract text) ----------

WORD_JUNK_TAGS = {"o:p"}              # MS Word-specific
REMOVE_TAGS = {"script", "style", "meta", "link", "iframe"}
UNWRAP_TAGS = {"div", "span"}         # remove tag but keep content

def _looks_like_html(s: str) -> bool:
    return "<" in s and ">" in s and re.search(r"</?\w+", s) is not None

def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove junk tags entirely
    for name in list(REMOVE_TAGS | WORD_JUNK_TAGS):
        for t in soup.find_all(name):
            t.decompose()

    # Remove inline styles/classes and unwrap div/span
    for t in soup.find_all(True):
        if t.name in UNWRAP_TAGS:
            t.attrs = {}
            t.unwrap()
        else:
            t.attrs = {k: v for k, v in t.attrs.items() if k not in {"style", "class"}}

    # Drop empty paragraphs
    for p in soup.find_all("p"):
        if not p.get_text(strip=True):
            p.decompose()

    # Convert <br> to newline
    for br in soup.find_all("br"):
        br.replace_with("\n")

    text = soup.get_text(separator="\n")
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


# ---------- Unicode helpers ----------

# Keep tabs/newlines/carriage returns; drop other ASCII control chars + DEL
CTRL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

# Items to remove (explicit list – no dash-like code points here)
INVISIBLES = [
    "\u2003", "\u2018", "\u2019", "\u201C", "\u201D",
    "\u200B", "\u2002", "\u00A0", "\u202F", "\u2060",
    "\u200C", "\u200D", "\u200E", "\u200F", "\uFEFF",
    "\u2061", "\u2062", "\u2063", "\u2064", "\u180E",
    "\u2001", "\u2008", "\u2009", "\u200A", "\u3164",
    "\u00AD", "\u202E", "\u2800", "\u02BC"
]
INVISIBLE_RE = re.compile("|".join(map(re.escape, INVISIBLES)))

# Convert literal sequences like "\u200b" to the actual character
_U_ESC_RE = re.compile(r"\\u([0-9a-fA-F]{4})")
def _unescape_unicode_sequences(s: str) -> str:
    return _U_ESC_RE.sub(lambda m: chr(int(m.group(1), 16)), s)

# Drop backslashes that are NOT starting a valid JSON escape (", \, /, b, f, n, r, t, u)
_BAD_BACKSLASH = re.compile(r"\\(?![\"\\/bfnrtu])")
def _drop_spurious_backslashes(s: str) -> str:
    return _BAD_BACKSLASH.sub("", s)


# ---------- Dash normalization ----------

def _normalize_dashes(text: str) -> str:
    # Map dash-like chars to ASCII hyphen
    text = re.sub(r"[—–−‒―⸻‐]", "-", text)
    # Force spacing around hyphen used as a dash: "word-word" -> "word - word"
    text = re.sub(r"(?<=\S)-(?=\S)", " - ", text)
    return text


# ---------- Whitespace normalization ----------

def _collapse_spaces(s: str) -> str:
    # Convert NBSP and narrow NBSP to normal spaces
    s = s.replace("\u00A0", " ").replace("\u202F", " ")
    # Collapse multiple spaces/tabs
    s = re.sub(r"[ \t]{2,}", " ", s)
    # Trim spaces around newlines
    s = re.sub(r"[ \t]*\n[ \t]*", "\n", s)
    # Collapse 3+ blank lines to at most 2
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# ---------- Main cleaning entry point ----------

def clean_content(raw: str) -> str:
    """Return cleaned text for either HTML or plain input."""
    if raw is None:
        raise ValueError("No text provided")

    # 1) HTML -> text (preserve <br> as newlines)
    text = _html_to_text(raw) if _looks_like_html(raw) else raw

    # 2) Turn literal unicode escapes (e.g., "\\u200b") into real codepoints
    text = _unescape_unicode_sequences(text)

    # 3) Remove stray backslashes like "\width" (keep valid JSON escapes intact)
    text = _drop_spurious_backslashes(text)

    # 4) Remove ASCII control chars (keep \n, \r, \t) and explicit invisibles
    text = CTRL_CHARS.sub("", text)
    text = INVISIBLE_RE.sub("", text)

    # 5) Normalize dashes and tidy whitespace
    text = _normalize_dashes(text)
    text = _collapse_spaces(text)

    return text
