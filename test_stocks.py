import json, os, tempfile, unittest
import forecast, quotes, stocks

SAMPLE_CLIMB = [100 + i for i in range(40)]
SAMPLE_FALL = [140 - i for i in range(40)]
SAMPLE_FLAT = [100 + (i % 2) * 0.1 for i in range(40)]

def fake_payload(closes, price=None, currency='USD'):
    return {"chart": {"result": [{"meta": {"symbol": "FAKE", "currency": currency,
            "regularMarketPrice": price if price is not None else closes[-1],
            "regularMarketChangePercent": 1.5},
            "indicators": {"quote": [{"close": closes}]}}]}}

class ForecastTests(unittest.TestCase):
    def test_moving_average(self):
        self.assertEqual(forecast.moving_average([1, 2, 3, 4], 2), 3.5)
        self.assertIsNone(forecast.moving_average([1], 5))
    def test_trend_recovers_slope(self):
        a, b, sigma = forecast.linear_trend(SAMPLE_CLIMB)
        self.assertAlmostEqual(b, 1.0, places=6)
        self.assertAlmostEqual(a, 100.0, places=6)
        self.assertAlmostEqual(sigma, 0.0, places=6)
    def test_forecast_up_series_points_up(self):
        est = forecast.forecast(SAMPLE_CLIMB)
        self.assertGreater(est['trend_pct'], 0)
        self.assertGreater(est['high'], est['estimate'])
        self.assertGreater(est['estimate'], est['low'])
    def test_forecast_down_series_points_down(self):
        self.assertLess(forecast.forecast(SAMPLE_FALL)['trend_pct'], 0)
    def test_forecast_flat_series_is_flat(self):
        self.assertAlmostEqual(forecast.forecast(SAMPLE_FLAT)['trend_pct'], 0.0, places=1)
    def test_forecast_needs_history(self):
        self.assertIsNone(forecast.forecast([1, 2, 3]))
        self.assertIsNone(forecast.forecast([]))
    def test_uncertainty_widens_with_horizon(self):
        near = forecast.forecast(SAMPLE_CLIMB, days_ahead=1)
        far = forecast.forecast(SAMPLE_CLIMB, days_ahead=7)
        self.assertGreater(far['high'] - far['low'], near['high'] - near['low'])

class QuoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['STOCKS_CACHE'] = self.tmp.name
        import importlib; importlib.reload(quotes)
    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop('STOCKS_CACHE', None)
    def test_parses_payload_and_caches(self):
        calls = []
        def fake(symbol, range_='3mo', interval='1d', timeout=10):
            calls.append(symbol)
            return fake_payload(SAMPLE_CLIMB, price=139.0)
        quotes._fetch = fake
        h = quotes.get_history('fake')
        self.assertEqual(h['price'], 139.0)
        self.assertEqual(h['currency'], 'USD')
        self.assertEqual(len(h['closes']), 40)
        h2 = quotes.get_history('fake')  # served from cache
        self.assertEqual(len(calls), 1)
        self.assertEqual(h2['closes'][-1], 139)
    def test_stale_cache_used_when_offline(self):
        quotes._fetch = lambda *a, **k: fake_payload(SAMPLE_CLIMB)
        quotes.get_history('fake', max_age=0)  # write cache (already stale)
        def boom(*a, **k): raise OSError('offline')
        quotes._fetch = boom
        h = quotes.get_history('fake', max_age=0)
        self.assertIsNotNone(h)
    def test_no_data_returns_none(self):
        def boom(*a, **k): raise OSError('offline')
        quotes._fetch = boom
        self.assertIsNone(quotes.get_history('nope'))
    def test_bad_payload_returns_none(self):
        quotes._fetch = lambda *a, **k: {"chart": {"result": []}}
        self.assertIsNone(quotes.get_history('nope'))

class WatchlistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['STOCKS_HOME'] = self.tmp.name
        import importlib; importlib.reload(stocks)
    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop('STOCKS_HOME', None)
    def test_roundtrip(self):
        self.assertEqual(stocks.load_watchlist(), [])
        stocks.save_watchlist(['AAPL', 'MSFT'])
        self.assertEqual(stocks.load_watchlist(), ['AAPL', 'MSFT'])
    def test_corrupt_file_is_empty(self):
        os.makedirs(self.tmp.name, exist_ok=True)
        with open(stocks.WATCH_FILE, 'w') as fh: fh.write('{oops')
        self.assertEqual(stocks.load_watchlist(), [])
    def test_trend_label(self):
        self.assertEqual(stocks.trend_label(2.0), 'up')
        self.assertEqual(stocks.trend_label(-2.0), 'down')
        self.assertEqual(stocks.trend_label(0.1), 'flat')
        self.assertEqual(stocks.trend_label(None), '')

if __name__ == '__main__':
    unittest.main()
