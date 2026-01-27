"""Tests for date utility functions."""

from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

from app.core.Utilities.dates import (
    diff_month,
    get_beginning_of_month,
    get_end_of_month,
    get_month_range,
    get_previous_n_months,
)


class TestDiffMonth:
    """Test cases for diff_month function."""

    def test_diff_month_same_month(self):
        """Test diff between same month returns 0."""
        date1 = datetime(2023, 1, 15)
        date2 = datetime(2023, 1, 1)
        assert diff_month(date1, date2) == 0

    def test_diff_month_adjacent_months(self):
        """Test diff between adjacent months returns 1."""
        date1 = datetime(2023, 2, 15)
        date2 = datetime(2023, 1, 1)
        assert diff_month(date1, date2) == 1

    def test_diff_month_multiple_months(self):
        """Test diff between multiple months."""
        date1 = datetime(2023, 6, 15)
        date2 = datetime(2023, 1, 1)
        assert diff_month(date1, date2) == 5

    def test_diff_month_year_boundary(self):
        """Test diff across year boundary."""
        date1 = datetime(2024, 1, 15)
        date2 = datetime(2023, 12, 1)
        assert diff_month(date1, date2) == 1

    def test_diff_month_multiple_years(self):
        """Test diff across multiple years."""
        date1 = datetime(2025, 3, 15)
        date2 = datetime(2023, 1, 1)
        assert diff_month(date1, date2) == 26

    def test_diff_month_invalid_order(self):
        """Test error when d2 > d1."""
        date1 = datetime(2023, 1, 1)
        date2 = datetime(2023, 2, 1)
        with pytest.raises(ValueError, match="d2 must be less than d1"):
            diff_month(date1, date2)


class TestGetBeginningOfMonth:
    """Test cases for get_beginning_of_month function."""

    def test_get_beginning_of_month_with_date(self):
        """Test with specific date."""
        date = datetime(2023, 6, 15, 14, 30, 45)
        result = get_beginning_of_month(date)
        expected = datetime(2023, 6, 1, 14, 30, 45)
        assert result == expected

    def test_get_beginning_of_month_none(self):
        """Test with None returns current month start."""
        result = get_beginning_of_month()
        assert result.day == 1
        assert result.month == datetime.now().month
        assert result.year == datetime.now().year


class TestGetEndOfMonth:
    """Test cases for get_end_of_month function."""

    def test_get_end_of_month_february_non_leap(self):
        """Test February in non-leap year."""
        date = datetime(2023, 2, 15)
        result = get_end_of_month(date)
        expected = datetime(2023, 2, 28, 23, 59, 59)
        assert result == expected

    def test_get_end_of_month_february_leap(self):
        """Test February in leap year."""
        date = datetime(2024, 2, 15)
        result = get_end_of_month(date)
        expected = datetime(2024, 2, 29, 23, 59, 59)
        assert result == expected

    def test_get_end_of_month_31_day_month(self):
        """Test month with 31 days."""
        date = datetime(2023, 7, 15)
        result = get_end_of_month(date)
        expected = datetime(2023, 7, 31, 23, 59, 59)
        assert result == expected

    def test_get_end_of_month_30_day_month(self):
        """Test month with 30 days."""
        date = datetime(2023, 4, 15)
        result = get_end_of_month(date)
        expected = datetime(2023, 4, 30, 23, 59, 59)
        assert result == expected

    def test_get_end_of_month_none(self):
        """Test with None returns current month end."""
        result = get_end_of_month()
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59


class TestGetMonthRange:
    """Test cases for get_month_range function."""

    def test_get_month_range_single_month(self):
        """Test range with single month."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 31)
        result = get_month_range(start, end)
        assert len(result) == 1
        assert result[0].month == 1
        assert result[0].year == 2023

    def test_get_month_range_multiple_months(self):
        """Test range with multiple months."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 3, 31)
        result = get_month_range(start, end)
        assert len(result) == 3
        assert [m.month for m in result] == [1, 2, 3]

    def test_get_month_range_year_boundary(self):
        """Test range across year boundary."""
        start = datetime(2023, 12, 1)
        end = datetime(2024, 1, 31)
        result = get_month_range(start, end)
        assert len(result) == 2
        assert [m.year for m in result] == [2023, 2024]

    def test_get_month_range_invalid_order(self):
        """Test error when start > end."""
        start = datetime(2023, 2, 1)
        end = datetime(2023, 1, 31)
        with pytest.raises(ValueError, match="start must be less than end"):
            get_month_range(start, end)


class TestGetLastNMonths:
    """Test cases for get_last_n_months function."""

    def test_get_last_n_months_one(self):
        """Test getting 1 month."""
        result = get_previous_n_months(n=1)
        assert len(result) == 1
        assert result[0].month == datetime.now().month

    def test_get_last_n_months_twelve(self):
        """Test getting 12 months."""
        result = get_previous_n_months(n=12)
        assert len(result) == 12

    def test_get_last_n_months_with_end_cap(self):
        """Test with end cap."""
        end_cap = datetime(2023, 6, 15)
        result = get_previous_n_months(n=3, end_cap=end_cap)
        assert len(result) == 3
        assert result[0].month == 4  # Should end at June
        assert result[2].month == 6  # Should start at April

    def test_get_last_n_months_with_start_cap(self):
        """Test with start cap."""
        start_cap = datetime(2023, 1, 15)
        result = get_previous_n_months(n=6, start_cap=start_cap)
        assert len(result) <= 6
        assert all(m.month >= 1 for m in result)

    def test_get_last_n_months_with_both_caps_exact_n(self):
        """Test with caps spanning exactly n months."""
        start_cap = datetime(2023, 1, 15)
        end_cap = datetime(2023, 12, 15)
        result = get_previous_n_months(n=12, start_cap=start_cap, end_cap=end_cap)
        assert len(result) == 12
        assert result[0].month == 1
        assert result[-1].month == 12

    def test_get_last_n_months_with_both_caps_less_than_n(self):
        """Test with caps spanning less than n months."""
        start_cap = datetime(2023, 6, 15)
        end_cap = datetime(2023, 8, 15)
        result = get_previous_n_months(n=12, start_cap=start_cap, end_cap=end_cap)
        assert len(result) == 3  # Should return only the capped range

    def test_get_last_n_months_current_before_start_cap(self):
        """Test when current date is before start cap."""
        future_start = datetime.now() + relativedelta(months=6)
        result = get_previous_n_months(n=12, start_cap=future_start)
        assert result == []

    def test_get_last_n_months_invalid_caps(self):
        """Test error when start_cap > end_cap."""
        start_cap = datetime(2023, 6, 15)
        end_cap = datetime(2023, 4, 15)
        with pytest.raises(ValueError, match="start_cap must be less than end_cap"):
            get_previous_n_months(n=12, start_cap=start_cap, end_cap=end_cap)

    def test_get_last_n_months_year_boundary(self):
        """Test getting months across year boundary."""
        # Test with fixed end cap to ensure year boundary behavior
        end_cap = datetime(2024, 1, 15)
        result = get_previous_n_months(n=3, end_cap=end_cap)
        # Should include Dec 2023, Nov 2023, Oct 2023
        months = [m.month for m in result]
        years = [m.year for m in result]
        assert 12 in months  # December
        assert 2023 in years  # Previous year

    def test_get_last_n_months_leap_year_february(self):
        """Test getting months including leap year February."""
        # Test around February 2024 (leap year)
        end_cap = datetime(2024, 3, 15)
        result = get_previous_n_months(n=3, end_cap=end_cap)
        assert len(result) == 3
        # Should include March, February, January 2024
        months = [m.month for m in result]
        assert 2 in months  # February should be included

    def test_get_last_n_months_only_start_cap(self):
        """Test with only start cap set."""
        start_cap = datetime(2023, 6, 15)
        result = get_previous_n_months(n=12, start_cap=start_cap)
        assert len(result) <= 12
        # Should respect start cap and not include months before June 2023
        for month in result:
            if month.year == 2023:
                assert month.month >= 6

    def test_get_last_n_months_only_end_cap(self):
        """Test with only end cap set."""
        end_cap = datetime(2023, 6, 15)
        result = get_previous_n_months(n=12, end_cap=end_cap)
        assert len(result) == 12
        assert result[0].month == 7  # Should end at July 2022
        assert result[11].month == 6  # Should end at July 2022
        # Should end at cap, not current date

    def test_get_last_n_months_start_cap_adjustment(self):
        """Test when starting_month gets adjusted to start_cap."""
        start_cap = datetime(2023, 10, 15)
        result = get_previous_n_months(n=3, start_cap=start_cap)
        assert len(result) <= 3
        # Should respect start cap and not include months before October 2023
        for month in result:
            if month.year == 2023:
                assert month.month >= 10

    def test_get_last_n_months_zero_months(self):
        """Test with n=0."""
        result = get_previous_n_months(n=0)
        assert len(result) == 0

    def test_get_last_n_months_negative_months(self):
        """Test with negative n."""
        result = get_previous_n_months(n=-1)
        assert len(result) == 0
