# Add these imports at top of your Flask file (if not already present)
import os
import re
import time
import json
import pandas as pd
import yfinance as yf
from functools import lru_cache
from dotenv import load_dotenv

# If you're using google.generativeai (Gemini), import it
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.0")  # change if needed

if GENAI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ---------- Helpers ----------
def is_gibberish(query: str) -> bool:
    """Reject very short or non-alphabet queries as gibberish."""
    if not query: 
        return True
    q = query.strip()
    if len(q) < 3:
        return True
    # at least one alphabetic character
    if not re.search(r"[A-Za-z]", q):
        return True
    # guard: if too many random characters (no whitespace, too many symbols)
    if len(re.findall(r"[A-Za-z0-9]", q)) / max(1, len(q)) < 0.4:
        return True
    return False

def local_parse_query(query: str) -> dict:
    """
    Simple but robust parser: extracts sector, country, market_cap, profit_margin, keywords.
    Returns a dict of filters and keywords.
    """
    q = query.lower()
    filters = {}
    keywords = []

    # sector keywords map (extend as needed)
    sector_map = {
        "technology": ["tech", "technology", "software", "semiconductor"],
        "financials": ["finance", "bank", "financial", "payments", "visa", "mastercard"],
        "energy": ["energy", "oil", "gas", "renewable", "solar", "wind"],
        "healthcare": ["health", "healthcare", "pharma", "biotech", "medicine"],
        "automotive": ["automotive", "auto", "car", "ev", "electric vehicle", "vehicle"],
        "retail": ["retail", "consumer", "consumer goods"],
        "telecom": ["telecom", "telecommunications", "telecoms"]
    }
    for sector, kws in sector_map.items():
        for kw in kws:
            if kw in q:
                filters["sector"] = sector.capitalize()
                break
        if "sector" in filters:
            break

    # country detection
    if "india" in q or "indian" in q or ".ns" in q:
        filters["country"] = "India"
    elif "china" in q:
        filters["country"] = "China"
    elif "usa" in q or "us " in q or "united states" in q or "american" in q:
        filters["country"] = "USA"

    # market cap phrases: e.g. "large cap", "small cap", "market cap > 50b"
    if "large cap" in q or "large-cap" in q or "market cap > 100" in q:
        filters["market_cap_billions"] = {">": 100}
    elif "mid cap" in q or "mid-cap" in q:
        filters["market_cap_billions"] = {"between": [2, 100]}
    elif "small cap" in q or "small-cap" in q:
        filters["market_cap_billions"] = {"<": 2}
    else:
        # detect numeric market cap filter
        m = re.search(r"market cap\s*(>|<|>=|<=|=)\s*([\d\.]+)\s*(b|bn|billion)?", q)
        if m:
            op = m.group(1)
            val = float(m.group(2))
            if m.group(3):
                # assume billions
                pass
            filters["market_cap_billions"] = {op: val}

    # profitability / profit_margin
    if "profitable" in q or "profit" in q or "profit margin" in q:
        # default: profit margin > 0
        filters["profit_margin"] = {">": 0}

    # price filters
    m = re.search(r"price\s*(>|<|>=|<=|=)\s*\$?([\d\.]+)", q)
    if m:
        op, val = m.group(1), float(m.group(2))
        filters["price"] = {op: val}

    # top/limit preference
    m = re.search(r"top\s+(\d+)", q)
    limit = int(m.group(1)) if m else None

    # keywords fallback: individual words that might match company or industry
    tokens = re.findall(r"[A-Za-z]{2,}", q)
    common_stop = {"show","me","companies","company","in","the","of","and","top","best","that","with","are","which"}
    keywords = [t for t in tokens if t not in common_stop]

    return {
        "filters": filters,
        "keywords": keywords,
        "limit": limit
    }

def gemini_parse_query(query: str) -> dict:
    """Call Gemini to extract structured filters. Returns same shape as local_parse_query.
       This function is defensive: it tries to parse JSON from the model output and falls back to local parser.
    """
    if not GENAI_AVAILABLE or not GEMINI_API_KEY:
        return local_parse_query(query)

    # Prompt: ask for JSON with a strict schema
    prompt = f"""
You are an assistant that extracts structured filters from a user stock search query.

Input query: \"\"\"{query}\"\"\"

Return a JSON object exactly (no extra text) with keys:
- filters: object mapping column names to condition (e.g., {{"sector": "Technology", "market_cap_billions": {{">": 100}}}})
- keywords: array of relevant keywords
- limit: integer or null

If nothing relevant, return empty filters and empty keywords.

Example:
{{"filters": {{}}, "keywords": ["electric","vehicle"], "limit": 10}}
"""
    try:
        # Use the configured model; defensive code because model names vary across accounts
        resp = genai.generate(model=GEMINI_MODEL, prompt=prompt, max_output_tokens=300)
        text = ""
        # resp may have a structure with 'candidates' or 'output' depending on library version
        if hasattr(resp, "text"):
            text = resp.text
        else:
            # Try common fields
            text = str(resp)
        # extract JSON blob from text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            # basic normalization
            filters = parsed.get("filters", {})
            keywords = parsed.get("keywords", []) or []
            limit = parsed.get("limit")
            return {"filters": filters, "keywords": keywords, "limit": limit}
    except Exception as e:
        # logging safe fallback
        print("[Gemini parse error]", e)

    # fallback
    return local_parse_query(query)

# LRU cache to limit yfinance calls per process
@lru_cache(maxsize=1024)
def fetch_yf_info(symbol: str) -> dict:
    """Return price, volume, change_percent for a symbol (safe with try/except)."""
    try:
        t = yf.Ticker(symbol)
        info = t.info if hasattr(t, "info") else {}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        volume = info.get("volume")
        change = info.get("regularMarketChangePercent") or info.get("regularMarketChange")
        # normalize change percent if necessary
        if change is not None and abs(change) > 1000:
            # sometimes different format; leave as-is
            pass
        return {
            "price": float(price) if price is not None else None,
            "volume": int(volume) if volume is not None else None,
            "change_percent": float(change) if change is not None else None
        }
    except Exception as e:
        print(f"[yf] fetch error {symbol}: {e}")
        return {"price": None, "volume": None, "change_percent": None}

def generate_summary_with_gemini(company: dict, query: str) -> str:
    """Try Gemini for a one-sentence summary that ties the company to the user query; fallback to template."""
    if GENAI_AVAILABLE and GEMINI_API_KEY:
        prompt = f"""Write a short 1-sentence summary (max 30 words) about {company.get('company_name') or company.get('name')}, including why it matches the query: \"{query}\". Return only the sentence."""
        try:
            resp = genai.generate(model=GEMINI_MODEL, prompt=prompt, max_output_tokens=60)
            text = getattr(resp, "text", None) or str(resp)
            # strip extra whitespace
            return re.sub(r"\s+", " ", text).strip()
        except Exception as e:
            print("[Gemini summary error]", e)
    # fallback template
    desc = company.get("description") or company.get("industry") or ""
    return f"{company.get('company_name') or company.get('name')} — {desc[:120]}..."

# ---------- The route ----------
@app.route("/api/ai_search", methods=["POST"])
def ai_search():
    """Hybrid AI-assisted search (US + India)."""
    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            return jsonify({"error": "No JSON payload"}), 400
        query = payload.get("query", "").strip()
        if is_gibberish(query):
            # Clear signal for UI: empty results, no random fallback
            return jsonify({"query": query, "filters": {}, "results": []})

        # 1) Ask Gemini (if available) or local parser for structured filters
        parsed = gemini_parse_query(query)
        filters = parsed.get("filters", {})
        keywords = parsed.get("keywords", []) or []
        limit = parsed.get("limit") or payload.get("limit") or 20
        try:
            limit = int(limit)
        except Exception:
            limit = 20
        limit = max(1, min(limit, 50))  # keep between 1 and 50

        # 2) Filter dataset (df must already be loaded at app startup)
        working_df = df.copy()

        # apply sector filter
        sector = filters.get("sector")
        if sector:
            # case-insensitive match
            working_df = working_df[working_df['sector'].str.contains(str(sector), case=False, na=False)]

        # country filter
        country = filters.get("country")
        if country:
            working_df = working_df[working_df['country'].str.contains(str(country), case=False, na=False)]

        # market cap filters
        mc = filters.get("market_cap_billions")
        if isinstance(mc, dict):
            if ">" in mc:
                working_df = working_df[pd.to_numeric(working_df['market_cap_billions'], errors='coerce') > float(mc[">"])]
            elif "<" in mc:
                working_df = working_df[pd.to_numeric(working_df['market_cap_billions'], errors='coerce') < float(mc["<"])]
            elif "between" in mc:
                lo, hi = mc["between"]
                working_df = working_df[(pd.to_numeric(working_df['market_cap_billions'], errors='coerce') >= lo) & (pd.to_numeric(working_df['market_cap_billions'], errors='coerce') <= hi)]

        # profit_margin if present in df (many datasets don't have it) - safe check
        pm = filters.get("profit_margin")
        if isinstance(pm, dict) and 'profit_margin' in working_df.columns:
            if ">" in pm:
                working_df = working_df[pd.to_numeric(working_df['profit_margin'], errors='coerce') > float(pm[">"])]
            elif "<" in pm:
                working_df = working_df[pd.to_numeric(working_df['profit_margin'], errors='coerce') < float(pm["<"])]

        # keywords: simple contains matching across several columns
        if keywords:
            kw_regex = "|".join(re.escape(k) for k in keywords[:10])
            mask = (
                working_df['company_name'].str.contains(kw_regex, case=False, na=False)
            ) | (
                working_df.get('description', pd.Series([""] * len(working_df))).str.contains(kw_regex, case=False, na=False)
            ) | (
                working_df.get('industry', pd.Series([""] * len(working_df))).str.contains(kw_regex, case=False, na=False)
            ) | (
                working_df.get('symbol', pd.Series([""] * len(working_df))).str.contains(kw_regex, case=False, na=False)
            )
            working_df = working_df[mask]

        # final safety: remove duplicates and limit
        working_df = working_df.drop_duplicates(subset=["symbol"], keep="first")
        if working_df.empty:
            return jsonify({"query": query, "filters": filters, "results": []})

        # Choose top rows (we might have a scoring function later)
        candidates = working_df.head(limit)

        results = []
        for _, row in candidates.iterrows():
            symbol = str(row.get("symbol") or row.get("Symbol") or "").strip()
            company_name = row.get("company_name") or row.get("name") or row.get("Company") or ""
            # Fetch live yfinance info (cached)
            live = fetch_yf_info(symbol) if symbol else {"price": None, "volume": None, "change_percent": None}
            # Build result object
            res_item = {
                "company_name": company_name,
                "symbol": symbol,
                "sector": row.get("sector"),
                "industry": row.get("industry") or row.get("Industry"),
                "country": row.get("country"),
                "market_cap_billions": row.get("market_cap_billions"),
                "description": row.get("description") or row.get("summary") or "",
                "price": live.get("price"),
                "volume": live.get("volume"),
                "change_percent": live.get("change_percent"),
            }
            # Generate a tiny summary (non-blocking fallback)
            res_item["summary"] = generate_summary_with_gemini(res_item, query)
            results.append(res_item)

        return jsonify({
            "query": query,
            "filters": filters,
            "keywords": keywords,
            "results": results,
        })

    except Exception as e:
        print("[/api/ai_search] error:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected error occurred"}), 500
