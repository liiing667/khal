"""Central place for all timezone handling in khal.

The rules implemented here are:

* Storage boundary: datetimes are stored in the cache database as unix
  timestamps (seconds since the epoch, UTC). Use `to_unix_time` to cross
  the boundary into storage and `from_unix_time` / `from_unix_time_naive`
  to come back.
* Display boundary: datetimes are presented to the user in the configured
  local timezone. Use `localize` to attach a timezone to a naive
  (wall-clock) datetime, `to_timezone` to convert an aware datetime into
  another timezone, and `now_in_timezone` to get the current time.
* Cross-timezone events: `convert_to_timezone` implements the single rule
  used everywhere: aware datetimes are converted (the instant is kept),
  naive datetimes get the timezone attached (the wall time is kept).
"""

import datetime as dt
from calendar import timegm
from collections.abc import Iterator

import pytz


def is_aware(dtime: dt.datetime) -> bool:
    """test if a datetime instance is timezone aware"""
    return bool(dtime.tzinfo is not None and dtime.tzinfo.utcoffset(dtime) is not None)


def is_naive(dtime: dt.datetime) -> bool:
    """test if a datetime instance is timezone naive"""
    return not is_aware(dtime)


def localize(dtime: dt.datetime, timezone: pytz.BaseTzInfo) -> dt.datetime:
    """attach `timezone` to a naive datetime, keeping the wall time"""
    return timezone.localize(dtime)


def to_timezone(dtime: dt.datetime, timezone: dt.tzinfo) -> dt.datetime:
    """convert an aware datetime to `timezone`, keeping the instant"""
    return dtime.astimezone(timezone)


def convert_to_timezone(dtime: dt.datetime, timezone: pytz.BaseTzInfo) -> dt.datetime:
    """express `dtime` in `timezone`

    aware datetimes are converted (the instant is kept), naive datetimes
    get the timezone attached (the wall time is kept)
    """
    if is_aware(dtime):
        return to_timezone(dtime, timezone)
    else:
        return localize(dtime, timezone)


def now_in_timezone(timezone: pytz.BaseTzInfo) -> dt.datetime:
    """the current time as an aware datetime in `timezone`"""
    return localize(dt.datetime.now(), timezone)


def to_unix_time(dtime: dt.datetime) -> float:
    """convert a datetime object to unix time in UTC (as a float)"""
    if getattr(dtime, "tzinfo", None) is not None:
        dtime = dtime.astimezone(pytz.UTC)
    unix_time = timegm(dtime.timetuple())
    return unix_time


def from_unix_time(timestamp: float) -> dt.datetime:
    """convert a unix timestamp to an aware datetime in UTC"""
    return dt.datetime.fromtimestamp(timestamp, pytz.UTC)


def from_unix_time_naive(timestamp: float) -> dt.datetime:
    """convert a unix timestamp to a naive datetime in UTC"""
    return from_unix_time(timestamp).replace(tzinfo=None)


def to_naive_utc(dtime: dt.datetime) -> dt.datetime:
    """convert a datetime object to UTC and than remove the tzinfo, if
    datetime is naive already, return it
    """
    if not hasattr(dtime, "tzinfo") or dtime.tzinfo is None:
        return dtime

    dtime_utc = dtime.astimezone(pytz.UTC)
    dtime_naive = dtime_utc.replace(tzinfo=None)
    return dtime_naive


def to_naive(dtime: dt.datetime, timezone: dt.tzinfo) -> dt.datetime:
    """convert an aware datetime to `timezone` and drop the tzinfo,
    i.e. return the wall time in `timezone` as a naive datetime
    """
    return to_timezone(dtime, timezone).replace(tzinfo=None)


def localize_strip_tz(dates: list[dt.datetime], timezone: dt.tzinfo) -> Iterator[dt.datetime]:
    """converts a list of dates to timezone, than removes tz info"""
    for one_date in dates:
        if getattr(one_date, "tzinfo", None) is not None:
            one_date = one_date.astimezone(timezone)
            one_date = one_date.replace(tzinfo=None)
        yield one_date
