from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta


def diff_month(d1: datetime, d2: datetime) -> int:
    if d2 > d1:
        raise ValueError("d2 must be less than d1")
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def get_beginning_of_month(date: datetime | None = None) -> datetime:
    """Get the start of the month for any given date / current date."""
    if not date:
        date = datetime.now()

    # Convert date to datetime if needed
    if hasattr(date, "date"):
        # This is already a datetime
        pass
    else:
        # This is a date, convert to datetime
        date = datetime.combine(date, datetime.min.time())

    return date.replace(day=1)


def get_end_of_month(date: datetime | None = None) -> datetime:
    """
    Get the last day of the month for any given date / current date.

    Args:
        date: Any datetime within the month

    Returns:
        datetime: The last day of that month at 23:59:59
    """
    # Force to first day of the month
    if not date:
        date = datetime.now()

    # Convert date to datetime if needed
    if hasattr(date, "date"):
        # This is already a datetime
        pass
    else:
        # This is a date, convert to datetime
        date = datetime.combine(date, datetime.min.time())

    first_day = date.replace(day=1)

    # Add 32 days (guarantees we're in next month)
    next_month = first_day + timedelta(days=32)

    # Force to first day of next month, then subtract 1 day
    last_day = next_month.replace(day=1) - timedelta(days=1)

    # Set time to end of day
    last_day = last_day.replace(hour=23)
    last_day = last_day.replace(minute=59)
    return last_day.replace(second=59)


def get_month_range(start, end) -> list[datetime]:
    if start > end:
        raise ValueError("start must be less than end")
    months = []
    for i in range(diff_month(end, start) + 1):
        months.append(start + relativedelta(months=i))
    return months[::-1]


def get_previous_n_months(
    n: int = 12,
    starting_date: datetime | None = None,
    start_cap: datetime | None = None,
    end_cap: datetime | None = None,
) -> list[datetime]:
    """Returns required months from current date to n months ago.
    If start_cap or end_cap are provided, they are used to filter the months.
    """
    if n <= 0:
        return []

    # normalize current date and start / end caps
    current_date = starting_date if starting_date else get_end_of_month(datetime.now())
    start_cap = get_beginning_of_month(start_cap) if start_cap else None
    end_cap = get_end_of_month(end_cap) if end_cap else None

    if start_cap and end_cap and start_cap > end_cap:
        raise ValueError("start_cap must be less than end_cap")

    if not end_cap and not start_cap:
        return get_month_range(current_date - relativedelta(months=n - 1), current_date)

    if end_cap and start_cap:
        if diff_month(end_cap, start_cap) < n:
            # maxed out the range already, rest is irrelevant
            return get_month_range(start_cap, end_cap)

    if end_cap and current_date > end_cap:
        # end range already reached, update goal
        current_date = end_cap

    if start_cap and current_date < start_cap:
        # range hasn't started yet, return empty list
        return []

    starting_month = current_date - relativedelta(months=n - 1)
    if start_cap and starting_month < start_cap:
        starting_month = start_cap

    return get_month_range(starting_month, current_date)
