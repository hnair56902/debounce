# debounce

Small debounce and throttle helpers for Python, with leading and trailing options.

```python
from debounce import debounce, throttle

f = debounce(lambda x: print(x), 0.100, leading=False, trailing=True)
f(1)
f(2)
f.flush()  # prints 2

g = throttle(lambda x: print(x), 0.100, leading=True, trailing=True)
g(1)  # prints 1 immediately
g(2)
g.flush()  # prints 2
```

The wrappers expose `tick()`, `flush()`, `cancel()`, and a `last_result` attribute.
`tick()` checks the clock and fires the trailing call if the wait has elapsed; `flush()`
fires it immediately.

## Why

A debounce/throttle library is either a wrapper around a real scheduler thread, or a
purely cooperative helper that lets the caller drive time. The former is hard to test
without flakiness; the latter is what this library does. Each constructor accepts a
`clock` callable (defaulting to `time.monotonic`), so tests can pass a fake clock and
remain fully deterministic. No threads, no `sleep`, no asyncio dependencies.

## Edge cases

A `wait` of zero with `leading=True` fires the leading call only — the window is treated
as already elapsed, so no trailing call is armed. `throttle(leading=False, trailing=False)`
raises `ValueError`, since it would never call anything. `debounce(leading=False, trailing=False)`
does not raise but never fires; it is allowed for completeness but useless.

The wrappers are not thread-safe; they are designed for single-threaded event loops.
