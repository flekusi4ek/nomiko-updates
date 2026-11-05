"""Pure horizontal tab layout arithmetic, kept separate from Qt for regression tests."""


def fitted_tab_width(available: int, count: int, *, minimum: int = 76,
                     maximum: int = 190) -> int:
    """Fit all tabs evenly, retaining native scroll fallback below minimum."""
    if count <= 0:
        return maximum
    return max(minimum, min(maximum, max(0, int(available)) // int(count)))
