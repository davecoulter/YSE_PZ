"""Format magnitudes and uncertainties for UI display."""

from __future__ import annotations


def format_magnitude(value) -> str:
    """Two decimal places for magnitudes (e.g. 18.32 not 18.3248572)."""
    if value is None or value == '':
        return '-'
    try:
        return f'{float(value):.2f}'
    except (TypeError, ValueError):
        return str(value)


def format_magnitude_with_error(mag, mag_err=None) -> str:
    """Format mag ± err when an uncertainty is present."""
    mag_str = format_magnitude(mag)
    if mag_err is None or mag_err == '':
        return mag_str
    try:
        err = float(mag_err)
    except (TypeError, ValueError):
        return mag_str
    if err <= 0:
        return mag_str
    return f'{mag_str} ± {err:.2f}'
