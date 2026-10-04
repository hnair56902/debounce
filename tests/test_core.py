import unittest

from debounce import Debounced, Throttled, debounce, throttle


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, dt):
        self.now += dt


class DebouncedTests(unittest.TestCase):
    def test_trailing_only_fires_after_wait(self):
        calls = []
        clock = FakeClock()
        d = Debounced(lambda x: calls.append(x), 100, clock=clock)
        d(1)
        d(2)
        self.assertEqual(calls, [])
        clock.advance(99)
        self.assertFalse(d.tick())
        self.assertEqual(calls, [])
        clock.advance(1)
        self.assertTrue(d.tick())
        self.assertEqual(calls, [2])

    def test_leading_fires_immediately(self):
        calls = []
        clock = FakeClock()
        d = Debounced(lambda x: calls.append(x), 100, leading=True, clock=clock)
        d(1)
        self.assertEqual(calls, [1])
        # Subsequent call during the window should not fire again immediately.
        d(2)
        self.assertEqual(calls, [1])
        clock.advance(100)
        self.assertTrue(d.tick())
        self.assertEqual(calls, [1, 2])

    def test_leading_without_trailing(self):
        calls = []
        clock = FakeClock()
        d = Debounced(
            lambda x: calls.append(x), 100, leading=True, trailing=False, clock=clock
        )
        d(1)
        self.assertEqual(calls, [1])
        d(2)
        clock.advance(100)
        self.assertFalse(d.tick())
        self.assertEqual(calls, [1])
        # After the window elapses the next call is a fresh leading call.
        d(3)
        self.assertEqual(calls, [1, 3])

    def test_neither_leading_nor_trailing_does_nothing(self):
        calls = []
        clock = FakeClock()
        d = Debounced(
            lambda x: calls.append(x),
            100,
            leading=False,
            trailing=False,
            clock=clock,
        )
        d(1)
        clock.advance(100)
        self.assertFalse(d.tick())
        self.assertEqual(calls, [])

    def test_flush_fires_pending(self):
        calls = []
        clock = FakeClock()
        d = Debounced(lambda x: calls.append(x), 100, clock=clock)
        d(1)
        d(2)
        d.flush()
        self.assertEqual(calls, [2])
        # Flush again should be a no-op.
        d.flush()
        self.assertEqual(calls, [2])

    def test_cancel_clears_pending(self):
        calls = []
        clock = FakeClock()
        d = Debounced(lambda x: calls.append(x), 100, clock=clock)
        d(1)
        d.cancel()
        clock.advance(100)
        self.assertFalse(d.tick())
        self.assertEqual(calls, [])

    def test_wait_zero_fires_leading_only(self):
        calls = []
        clock = FakeClock()
        d = Debounced(
            lambda x: calls.append(x),
            0,
            leading=True,
            trailing=True,
            clock=clock,
        )
        d(1)
        self.assertEqual(calls, [1])
        # No trailing call should be queued because wait == 0 and leading consumed the args.
        self.assertFalse(d.tick())
        self.assertEqual(calls, [1])

    def test_last_result_returned_on_leading(self):
        clock = FakeClock()
        d = Debounced(lambda x: x * 2, 100, leading=True, clock=clock)
        result = d(5)
        self.assertEqual(result, 10)
        self.assertEqual(d.last_result, 10)

    def test_trailing_uses_latest_args(self):
        calls = []
        clock = FakeClock()
        d = Debounced(lambda *a, **kw: calls.append((a, kw)), 100, clock=clock)
        d(1)
        d(2, x=3)
        clock.advance(100)
        self.assertTrue(d.tick())
        self.assertEqual(calls, [((2,), {'x': 3})])


class ThrottledTests(unittest.TestCase):
    def test_leading_fires_immediately(self):
        calls = []
        clock = FakeClock()
        t = Throttled(lambda x: calls.append(x), 100, clock=clock)
        t(1)
        self.assertEqual(calls, [1])
        t(2)
        t(3)
        self.assertEqual(calls, [1])
        clock.advance(100)
        self.assertTrue(t.tick())
        self.assertEqual(calls, [1, 3])

    def test_no_trailing_when_no_extra_calls(self):
        calls = []
        clock = FakeClock()
        t = Throttled(lambda x: calls.append(x), 100, clock=clock)
        t(1)
        clock.advance(100)
        self.assertFalse(t.tick())
        self.assertEqual(calls, [1])

    def test_leading_false_trailing_true(self):
        calls = []
        clock = FakeClock()
        t = Throttled(
            lambda x: calls.append(x), 100, leading=False, clock=clock
        )
        t(1)
        self.assertEqual(calls, [])
        clock.advance(100)
        self.assertTrue(t.tick())
        self.assertEqual(calls, [1])

    def test_leading_false_trailing_false_raises(self):
        with self.assertRaises(ValueError):
            Throttled(lambda x: x, 100, leading=False, trailing=False)

    def test_flush_fires_trailing(self):
        calls = []
        clock = FakeClock()
        t = Throttled(lambda x: calls.append(x), 100, clock=clock)
        t(1)
        t(2)
        self.assertEqual(calls, [1])
        t.flush()
        self.assertEqual(calls, [1, 2])

    def test_cancel_clears_trailing(self):
        calls = []
        clock = FakeClock()
        t = Throttled(lambda x: calls.append(x), 100, clock=clock)
        t(1)
        t(2)
        t.cancel()
        clock.advance(100)
        self.assertFalse(t.tick())
        self.assertEqual(calls, [1])

    def test_new_window_after_flush(self):
        calls = []
        clock = FakeClock()
        t = Throttled(lambda x: calls.append(x), 100, clock=clock)
        t(1)
        t.flush()
        # A fresh leading call should work right after flush.
        t(2)
        self.assertEqual(calls, [1, 2])

    def test_factory_returns_correct_types(self):
        self.assertIsInstance(debounce(lambda: None, 100), Debounced)
        self.assertIsInstance(throttle(lambda: None, 100), Throttled)

    def test_negative_wait_raises(self):
        with self.assertRaises(ValueError):
            Debounced(lambda: None, -1)
        with self.assertRaises(ValueError):
            Throttled(lambda: None, -1)


if __name__ == "__main__":
    unittest.main()
