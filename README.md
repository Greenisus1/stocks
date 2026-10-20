# Stocks (beta)

A terminal stock watchlist for the Pi. No API key, no account, no setup: quotes and daily history come from Yahoo Finance's public chart endpoint, cached for 15 minutes so repeat views are instant and light on the network.

Every app also runs fully offline for symbols you have viewed recently (stale cache is shown when the network is down).

## Run

```
bash app-store.sh install
bash app-store.sh run
```

- `A` add a symbol, `D` remove one, arrows or j/k move, Enter opens the detail view (recent closes chart + estimate), R refreshes, Esc/q quits.
- Your watchlist is saved in `~/.local/share/stocks/watchlist.json`.

## Estimates, not advice

The estimate column and the detail view show an on-device statistical estimate: a least-squares trend over recent closes projected forward, with a small pull toward the 7-day average, plus an uncertainty band that widens the further out it looks. It uses past prices only. It will be wrong sometimes, especially around news. **It is an estimate, not financial advice.**

## Languages

Works with the Translations app: pick a language there and the labels switch (English, Espanol, Francais, Deutsch). With no Translations app installed it runs in English as usual.

## Data

Quotes and history: Yahoo Finance public chart API (`query1.finance.yahoo.com/v8/finance/chart/<SYMBOL>`), cached in `~/.cache/stocks` for 15 minutes. No keys, no tracking, no account.

MIT, built with AI assistance from my design.
