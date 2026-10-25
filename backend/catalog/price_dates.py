"""Actual source precision and conservative time bounds, with no invented date."""
from calendar import monthrange
from datetime import date
import re


def _get(record,key,default=None):
    return record.get(key,default) if isinstance(record,dict) else getattr(record,key,default)


def price_bounds(record):
    """Return internal earliest/latest possible days, never observation dates."""
    precision=_get(record,'date_precision','day')
    day=_get(record,'observed_on')
    period=_get(record,'observed_period','')
    if precision=='day' and day and not period:
        value=date.fromisoformat(day) if isinstance(day,str) else day
        if not isinstance(value,date):raise ValueError('A day-precision price requires a valid source date.')
        return value,value
    if precision=='month' and day is None and isinstance(period,str) and re.fullmatch(r'[12]\d{3}-(0[1-9]|1[0-2])',period):
        year,month=map(int,period.split('-'))
        return date(year,month,1),date(year,month,monthrange(year,month)[1])
    raise ValueError('Use either an actual source day or a YYYY-MM source month, matching the declared precision.')


def price_label(record):
    if _get(record,'date_precision','day')=='month':return _get(record,'observed_period')
    value=_get(record,'observed_on')
    return value.isoformat() if isinstance(value,date) else value


def conservative_span(records):
    bounds=[price_bounds(row) for row in records]
    if not bounds:return 0
    # The earliest record could be at its month's end, and the latest at its
    # month's beginning. Only this guaranteed duration counts toward 20 years.
    return max(0,(max(low for low,high in bounds)-min(high for low,high in bounds)).days)/365.2425


def comparable_basis(basis):
    if basis in ['retail_offer','archive_capture','historical_ad']:return 'retail'
    if basis=='wholesale_list':return 'wholesale'
    return None
