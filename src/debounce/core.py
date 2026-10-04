from __future__ import annotations

import time
from typing import Any, Callable

__all__ = ["Debounced", "Throttled", "debounce", "throttle"]


class Debounced:
    def __init__(
        self,
        func: Callable[..., Any],
        wait: float,
        *,
        leading: bool = False,
        trailing: bool = True,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if wait < 0:
            raise ValueError("wait must be non-negative")
        self._func = func
        self._wait = wait
        self._leading = leading
        self._trailing = trailing
        self._clock = clock
        self._last_call_time: float | None = None
        self._pending_args: tuple[Any, ...] = ()
        self._pending_kwargs: dict[str, Any] = {}
        self._has_pending = False
        self._timer_armed = False
        self._leading_fired_in_window = False
        self.last_result: Any = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self._last_call_time = self._clock()
        self._pending_args = args
        self._pending_kwargs = kwargs
        self._has_pending = True

        if not self._leading_fired_in_window:
            if self._leading:
                self._leading_fired_in_window = True
                self.last_result = self._func(*args, **kwargs)
                self._has_pending = False
                if self._trailing or self._wait > 0:
                    self._timer_armed = True
                else:
                    self._timer_armed = False
                    self._leading_fired_in_window = False
            else:
                self._timer_armed = self._trailing
        return self.last_result

    def tick(self) -> bool:
        if not self._timer_armed:
            return False
        assert self._last_call_time is not None
        now = self._clock()
        if now - self._last_call_time < self._wait:
            return False
        return self._flush_now()

    def flush(self) -> Any:
        if not self._timer_armed:
            return None
        return self._flush_now()

    def _flush_now(self) -> bool:
        fired = False
        if self._trailing and self._has_pending:
            self.last_result = self._func(
                *self._pending_args, **self._pending_kwargs
            )
            fired = True
        self._has_pending = False
        self._timer_armed = False
        self._leading_fired_in_window = False
        self._pending_args = ()
        self._pending_kwargs = {}
        return fired

    def cancel(self) -> None:
        self._has_pending = False
        self._timer_armed = False
        self._leading_fired_in_window = False
        self._pending_args = ()
        self._pending_kwargs = {}


def debounce(
    func: Callable[..., Any],
    wait: float,
    *,
    leading: bool = False,
    trailing: bool = True,
    clock: Callable[[], float] = time.monotonic,
) -> Debounced:
    return Debounced(
        func,
        wait,
        leading=leading,
        trailing=trailing,
        clock=clock,
    )


class Throttled:
    def __init__(
        self,
        func: Callable[..., Any],
        wait: float,
        *,
        leading: bool = True,
        trailing: bool = True,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if wait < 0:
            raise ValueError("wait must be non-negative")
        if not leading and not trailing:
            raise ValueError("at least one of leading or trailing must be True")
        self._func = func
        self._wait = wait
        self._leading = leading
        self._trailing = trailing
        self._clock = clock
        self._window_start: float | None = None
        self._pending_args: tuple[Any, ...] = ()
        self._pending_kwargs: dict[str, Any] = {}
        self._has_pending = False
        self.last_result: Any = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        now = self._clock()
        self._pending_args = args
        self._pending_kwargs = kwargs
        self._has_pending = True

        if self._window_start is None:
            if self._leading:
                self._window_start = now
                self.last_result = self._func(*args, **kwargs)
                self._has_pending = False
                return self.last_result
            self._window_start = now
        return self.last_result

    def tick(self) -> bool:
        if self._window_start is None:
            return False
        now = self._clock()
        if now - self._window_start < self._wait:
            return False
        return self._flush_now()

    def flush(self) -> Any:
        if self._window_start is None:
            return None
        return self._flush_now()

    def _flush_now(self) -> bool:
        fired = False
        if self._trailing and self._has_pending:
            self.last_result = self._func(
                *self._pending_args, **self._pending_kwargs
            )
            fired = True
        self._has_pending = False
        self._window_start = None
        self._pending_args = ()
        self._pending_kwargs = {}
        return fired

    def cancel(self) -> None:
        self._has_pending = False
        self._window_start = None
        self._pending_args = ()
        self._pending_kwargs = {}


def throttle(
    func: Callable[..., Any],
    wait: float,
    *,
    leading: bool = True,
    trailing: bool = True,
    clock: Callable[[], float] = time.monotonic,
) -> Throttled:
    return Throttled(
        func,
        wait,
        leading=leading,
        trailing=trailing,
        clock=clock,
    )
