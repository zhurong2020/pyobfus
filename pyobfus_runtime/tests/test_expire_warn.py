"""Pre-expiry warning behaviour of the runtime ``expire_check`` (Y-2).

``warn_days`` is a backward-compatible addition: an artifact within the window
emits a :class:`LicenseExpiryWarning` and keeps running; only a passed expiry
still raises :class:`LicenseExpired`. Old generated code that calls
``expire_check("date")`` with no ``warn_days`` must behave exactly as before.
"""

from __future__ import annotations

import datetime as dt
import warnings

import pytest

from pyobfus_runtime import LicenseExpired, LicenseExpiryWarning, expire_check
from pyobfus_runtime.binding import LicenseBindingError


def _today(offset_days: int) -> dt.date:
    return dt.date(2027, 1, 1) + dt.timedelta(days=offset_days)


EXPIRE = "2027-06-01"
EXPIRE_DATE = dt.date(2027, 6, 1)


def test_no_warn_days_is_silent_and_unchanged() -> None:
    # The pre-Y-2 call shape: no warning even one day before expiry.
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any warning would fail the test
        expire_check(EXPIRE, now=EXPIRE_DATE - dt.timedelta(days=1))


def test_warns_inside_the_window() -> None:
    with pytest.warns(LicenseExpiryWarning) as record:
        expire_check(EXPIRE, now=EXPIRE_DATE - dt.timedelta(days=10), warn_days=30)
    assert len(record) == 1
    msg = str(record[0].message)
    assert EXPIRE in msg
    assert "10 day(s)" in msg


def test_warns_on_the_boundary_day() -> None:
    # days_left == warn_days is inside the window (inclusive).
    with pytest.warns(LicenseExpiryWarning):
        expire_check(EXPIRE, now=EXPIRE_DATE - dt.timedelta(days=30), warn_days=30)


def test_warns_on_the_last_valid_day_then_does_not_raise() -> None:
    # On the expiry date itself the artifact is still valid (expires the day
    # after), so it warns (days_left == 0) but does not raise.
    with pytest.warns(LicenseExpiryWarning) as record:
        expire_check(EXPIRE, now=EXPIRE_DATE, warn_days=7)
    assert "0 day(s)" in str(record[0].message)


def test_no_warn_before_the_window_opens() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        expire_check(EXPIRE, now=EXPIRE_DATE - dt.timedelta(days=31), warn_days=30)


def test_expired_raises_and_does_not_warn() -> None:
    # Past expiry: it must raise, not merely warn. days_left < 0 is outside the
    # window so no warning is emitted before the raise.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(LicenseExpired):
            expire_check(EXPIRE, now=EXPIRE_DATE + dt.timedelta(days=1), warn_days=30)


def test_warn_days_zero_warns_only_on_the_last_day() -> None:
    with pytest.warns(LicenseExpiryWarning):
        expire_check(EXPIRE, now=EXPIRE_DATE, warn_days=0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        expire_check(EXPIRE, now=EXPIRE_DATE - dt.timedelta(days=1), warn_days=0)


@pytest.mark.parametrize("bad", [-1, "30", 3.0, True])
def test_invalid_warn_days_is_rejected(bad: object) -> None:
    with pytest.raises(LicenseBindingError):
        expire_check(EXPIRE, now=EXPIRE_DATE - dt.timedelta(days=1), warn_days=bad)  # type: ignore[arg-type]


def test_warning_is_a_userwarning_so_hosts_can_route_it() -> None:
    # A host that has not opted in still sees it (UserWarning shows by default),
    # and a host that filters UserWarning can suppress it.
    assert issubclass(LicenseExpiryWarning, UserWarning)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        # Suppressed: no error despite simplefilter("error") not being set.
        expire_check(EXPIRE, now=EXPIRE_DATE - dt.timedelta(days=1), warn_days=30)
