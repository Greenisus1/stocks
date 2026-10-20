"""Quote + history fetch via Yahoo Finance's public chart endpoint.
No API key, no account. Responses cached on disk so repeated views stay offline-fast."""
import json, os, time, urllib.parse, urllib.request

CACHE_DIR = os.environ.get("STOCKS_CACHE") or os.path.expanduser("~/.cache/stocks")
CACHE_TTL = 900  # 15 minutes
UA = {"User-Agent": "Mozilla/5.0 (stocks terminal app)"}

def _fetch(symbol, range_="3mo", interval="1d", timeout=10):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(symbol.upper()) + "?range=" + range_ + "&interval=" + interval)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _cache_path(symbol, range_, interval):
    return os.path.join(CACHE_DIR, "%s_%s_%s.json" % (symbol.upper(), range_, interval))

def get_history(symbol, range_="3mo", interval="1d", max_age=CACHE_TTL):
    """Return {"symbol", "currency", "price", "change_pct", "closes"} or None on failure."""
    path = _cache_path(symbol, range_, interval)
    data = None
    try:
        if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age:
            with open(path) as fh: data = json.load(fh)
    except (OSError, ValueError):
        data = None
    if data is None:
        try:
            data = _fetch(symbol, range_, interval)
            os.makedirs(CACHE_DIR, exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w") as fh: json.dump(data, fh)
            os.replace(tmp, path)
        except Exception:
            try:
                with open(path) as fh: data = json.load(fh)  # stale cache beats nothing
            except (OSError, ValueError):
                return None
    try:
        result = data["chart"]["result"][0]
        meta = result["meta"]
        closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
        return {"symbol": meta.get("symbol", symbol.upper()),
                "currency": meta.get("currency", "?"),
                "price": meta.get("regularMarketPrice", closes[-1] if closes else None),
                "change_pct": meta.get("regularMarketChangePercent"),
                "closes": closes}
    except (KeyError, IndexError, TypeError):
        return None
