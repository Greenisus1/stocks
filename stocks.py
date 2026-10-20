#!/usr/bin/env python3
"""Stocks: watchlist quotes with on-device estimates. Original terminal app. Not financial advice."""
import curses, json, os, sys, time

try:
    import pi18n
except ImportError:
    pi18n = None

# English UI strings; the Translations app owns every language via ~/pi-translations.
DEFAULT_STRINGS = {
 'TITLE': 'STOCKS (beta)',
 'HEAD': '{symbol:<8} {price:>10} {change:>7}  {trend:<12} {estimate:>10}',
 'ADD': 'A add symbol | D remove | Enter details | R refresh | Esc/q quit',
 'PROMPT_ADD': 'Symbol to watch (e.g. AAPL): ',
 'PROMPT_DEL': 'Symbol to remove: ',
 'LOADING': 'Loading {symbol}...',
 'FAILED': '{symbol}: no data (offline and nothing cached, or unknown symbol)',
 'DETAIL_EST': 'Estimate for tomorrow: {estimate} {currency} (range {low} - {high})',
 'DETAIL_TREND': 'Trend vs now: {trend:+.2f}%   MA7 {ma_s}   MA30 {ma_l}',
 'DISCLAIMER': 'Estimate from past prices only. Not financial advice.',
 'DETAIL_KEYS': 'Esc/q back',
 'EMPTY': 'No symbols yet. Press A to add one.',
 'CLOSES': 'Last {n} closes, oldest to newest:',
}
VERSION = '1.0.0'
WATCH_DIR = os.environ.get('STOCKS_HOME') or os.path.expanduser('~/.local/share/stocks')
WATCH_FILE = os.path.join(WATCH_DIR, 'watchlist.json')

def load_watchlist():
    try:
        with open(WATCH_FILE) as fh:
            data = json.load(fh)
        return [s for s in data.get('symbols', []) if isinstance(s, str) and s][:20]
    except (OSError, ValueError):
        return []

def save_watchlist(symbols):
    os.makedirs(WATCH_DIR, exist_ok=True)
    tmp = WATCH_FILE + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump({'symbols': symbols}, fh)
    os.replace(tmp, WATCH_FILE)

def trend_label(trend_pct):
    if trend_pct is None: return ''
    if trend_pct > 0.5: return 'up'
    if trend_pct < -0.5: return 'down'
    return 'flat'

def prompt(s, y, text):
    h, w = s.getmaxyx()
    curses.echo(); curses.curs_set(1)
    s.addnstr(y, 1, text, w - 2)
    s.refresh()
    try:
        val = s.getstr(y, min(1 + len(text), w - 12), 10).decode().strip().upper()
    finally:
        curses.noecho(); curses.curs_set(0)
    return val

def detail(s, symbol, S):
    import quotes, forecast
    s.erase(); h, w = s.getmaxyx()
    s.addnstr(1, 1, S['LOADING'].format(symbol=symbol), w - 2); s.refresh()
    hst = quotes.get_history(symbol)
    s.erase()
    if not hst or not hst.get('closes'):
        s.addnstr(1, 1, S['FAILED'].format(symbol=symbol), w - 2)
    else:
        closes = hst['closes']; price = hst.get('price') or closes[-1]
        cur = hst.get('currency', '')
        est = forecast.forecast(closes)
        s.addnstr(0, 1, '%s  %s %s' % (symbol, price, cur), w - 2, curses.A_BOLD)
        s.addnstr(2, 1, S['CLOSES'].format(n=min(10, len(closes))), w - 2)
        recent = closes[-10:]
        lo, hi = min(recent), max(recent)
        for i, c in enumerate(recent):
            bar = 1 + int((c - lo) / (hi - lo) * 38) if hi > lo else 20
            s.addnstr(3 + i, 1, ('%10.2f ' % c) + '#' * bar, w - 2)
        row = 14
        if est:
            s.addnstr(row, 1, S['DETAIL_EST'].format(estimate=est['estimate'], currency=cur, low=est['low'], high=est['high']), w - 2)
            s.addnstr(row + 1, 1, S['DETAIL_TREND'].format(trend=est['trend_pct'], ma_s=est['ma_short'], ma_l=est['ma_long']), w - 2)
        s.addnstr(row + 3, 1, S['DISCLAIMER'], w - 2, curses.A_BOLD)
    s.addnstr(h - 1, 1, S['DETAIL_KEYS'], w - 2)
    s.refresh()
    while s.getch() not in (27, ord('q')): pass

def loop(s):
    S = pi18n.load('stocks', DEFAULT_STRINGS) if pi18n else DEFAULT_STRINGS
    symbols = load_watchlist()
    selected = 0
    while True:
        s.erase(); h, w = s.getmaxyx()
        s.addnstr(0, 1, S['TITLE'], w - 2, curses.A_BOLD)
        s.addnstr(1, 1, S['HEAD'].format(symbol='SYMBOL', price='PRICE', change='CHG%', trend='TREND', estimate='EST'), w - 2)
        if not symbols:
            s.addnstr(3, 1, S['EMPTY'], w - 2)
        import quotes, forecast
        for i, sym in enumerate(symbols):
            hst = quotes.get_history(sym)
            if hst and hst.get('closes'):
                est = forecast.forecast(hst['closes'])
                price = hst.get('price') or hst['closes'][-1]
                chg = hst.get('change_pct')
                line = S['HEAD'].format(symbol=sym, price='%.2f' % price,
                                        change=('%.2f' % chg if chg is not None else '?'),
                                        trend=trend_label(est['trend_pct']) if est else '?',
                                        estimate=('%.2f' % est['estimate']) if est else '?')
            else:
                line = S['FAILED'].format(symbol=sym)
            attr = curses.A_REVERSE if i == selected else 0
            s.addnstr(2 + i, 1, line, w - 2, attr)
        s.addnstr(h - 2, 1, S['DISCLAIMER'], w - 2)
        s.addnstr(h - 1, 1, S['ADD'], w - 2)
        s.refresh()
        key = s.getch()
        if key in (27, ord('q')): return
        if key in (curses.KEY_UP, ord('k')) and symbols: selected = (selected - 1) % len(symbols)
        if key in (curses.KEY_DOWN, ord('j')) and symbols: selected = (selected + 1) % len(symbols)
        if key in (10, 13, curses.KEY_ENTER) and symbols: detail(s, symbols[selected], S)
        if key in (ord('r'), ord('R')): pass
        if key in (ord('a'), ord('A')):
            sym = prompt(s, h - 3, S['PROMPT_ADD'])
            if sym and sym not in symbols:
                symbols.append(sym); save_watchlist(symbols)
        if key in (ord('d'), ord('D')) and symbols:
            sym = prompt(s, h - 3, S['PROMPT_DEL'])
            if sym in symbols:
                symbols.remove(sym); save_watchlist(symbols)
                selected = min(selected, max(0, len(symbols) - 1))

if __name__ == '__main__':
    if '--version' in sys.argv:
        print(VERSION)
    else:
        from ui import run
        raise SystemExit(run(loop))
