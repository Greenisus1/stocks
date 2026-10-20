"""On-device price estimation: moving averages + least-squares trend.
These are simple statistical estimates from past closes - not financial advice."""
import math

def moving_average(values, window):
    if window <= 0 or len(values) < window: return None
    return sum(values[-window:]) / window

def linear_trend(values):
    """Least-squares fit y = a + b*x over the series; returns (a, b, sigma)."""
    n = len(values)
    if n < 2: return None
    sx = n * (n - 1) / 2.0
    sx2 = (n - 1) * n * (2 * n - 1) / 6.0
    sy = sum(values)
    sxy = sum(i * v for i, v in enumerate(values))
    denom = n * sx2 - sx * sx
    if denom == 0: return None
    b = (n * sxy - sx * sy) / denom
    a = (sy - b * sx) / n
    resid = [v - (a + b * i) for i, v in enumerate(values)]
    sigma = math.sqrt(sum(r * r for r in resid) / n)
    return a, b, sigma

def forecast(closes, days_ahead=1, short=7, long=30):
    """Estimate a price days_ahead in the future with an uncertainty band.

    Projects the least-squares trend from the last close, with a small pull
    toward the short moving average. Returns dict with estimate, low, high, trend_pct,
    or None when there is not enough history. Estimate only - markets are noisy.
    """
    if not closes or len(closes) < max(short, 10): return None
    ma_s = moving_average(closes, short)
    ma_l = moving_average(closes, min(long, len(closes)))
    fit = linear_trend(closes[-max(long, 10):])
    if ma_s is None or fit is None: return None
    a, b, sigma = fit
    last = closes[-1]
    est = last + b * days_ahead + 0.25 * (ma_s - last)
    band = sigma * math.sqrt(days_ahead) * 1.5 + est * 0.005
    trend_pct = (b * days_ahead / last * 100.0) if last else 0.0
    return {"estimate": round(est, 2), "low": round(max(0.0, est - band), 2),
            "high": round(est + band, 2), "trend_pct": round(trend_pct, 2),
            "ma_short": round(ma_s, 2), "ma_long": round(ma_l, 2) if ma_l else None}
