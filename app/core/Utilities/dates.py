from datetime import datetime, timedelta


def get_end_of_month(date: datetime) -> datetime:
    """
    Get the last day of the month for any given date.

    Args:
        date: Any datetime within the month

    Returns:
        datetime: The last day of that month at 23:59:59
    """
    # Force to first day of the month
    first_day = date.replace(day=1)

    # Add 32 days (guarantees we're in next month)
    next_month = first_day + timedelta(days=32)

    # Force to first day of next month, then subtract 1 day
    last_day = next_month.replace(day=1) - timedelta(days=1)

    # Set time to end of day
    return last_day.replace(hour=23, minute=59, second=59, microsecond=999999)
