"""
validator.py — Input validation helpers for all order types.

Centralizes validation so every order module reuses the same rules:
  - Symbol format
  - Side (BUY / SELL)
  - Positive quantity
  - Positive prices
  - Stop price < Limit price for stop-limit sell, etc.
"""

from src.logger import get_logger

logger = get_logger("validator")


class ValidationError(ValueError):
    """Raised when user-supplied inputs fail validation."""
    pass


# ── Primitive validators ───────────────────────────────────────────────────────

def validate_symbol(symbol: str) -> str:
    """
    Ensures symbol is a non-empty uppercase string (e.g. BTCUSDT).

    Args:
        symbol: Trading pair string.

    Returns:
        Uppercased symbol.

    Raises:
        ValidationError: If symbol is blank.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol cannot be empty.")
    if not symbol.isalpha():
        raise ValidationError(
            f"Symbol '{symbol}' should contain only alphabetic characters (e.g. BTCUSDT)."
        )
    logger.debug(f"Symbol validated: {symbol}")
    return symbol


def validate_side(side: str) -> str:
    """
    Ensures side is BUY or SELL.

    Args:
        side: Order direction string.

    Returns:
        Uppercased side.

    Raises:
        ValidationError: If side is not BUY/SELL.
    """
    side = side.strip().upper()
    if side not in ("BUY", "SELL"):
        raise ValidationError(f"Invalid side '{side}'. Must be BUY or SELL.")
    logger.debug(f"Side validated: {side}")
    return side


def validate_quantity(quantity: float) -> float:
    """
    Ensures quantity is strictly positive.

    Args:
        quantity: Order size in base asset.

    Returns:
        Validated quantity.

    Raises:
        ValidationError: If quantity <= 0.
    """
    if quantity <= 0:
        raise ValidationError(f"Quantity must be positive. Got: {quantity}")
    logger.debug(f"Quantity validated: {quantity}")
    return quantity


def validate_price(price: float, label: str = "Price") -> float:
    """
    Ensures a price value is strictly positive.

    Args:
        price: Numeric price.
        label: Human-readable name for error messages.

    Returns:
        Validated price.

    Raises:
        ValidationError: If price <= 0.
    """
    if price <= 0:
        raise ValidationError(f"{label} must be positive. Got: {price}")
    logger.debug(f"{label} validated: {price}")
    return price


# ── Composite validators ───────────────────────────────────────────────────────

def validate_stop_limit(stop_price: float, limit_price: float, side: str) -> None:
    """
    Cross-validates stop and limit prices for a stop-limit order.

    For a SELL stop-limit (stop-loss):
        stop_price > limit_price  (trigger above, fill below — typical stop-loss)
    For a BUY stop-limit (breakout entry):
        stop_price < limit_price  (trigger below, fill above — typical breakout)

    Both values must be positive (validated separately before calling this).

    Args:
        stop_price:  The price that triggers the limit order.
        limit_price: The price at which the limit order is placed once triggered.
        side:        BUY or SELL (already validated).

    Raises:
        ValidationError: If the relationship between prices is illogical.
    """
    if side == "SELL" and stop_price <= limit_price:
        raise ValidationError(
            f"For a SELL stop-limit, stop_price ({stop_price}) must be > limit_price ({limit_price})."
        )
    if side == "BUY" and stop_price >= limit_price:
        raise ValidationError(
            f"For a BUY stop-limit, stop_price ({stop_price}) must be < limit_price ({limit_price})."
        )
    logger.debug(f"Stop-limit cross-validation passed: stop={stop_price}, limit={limit_price}, side={side}")


def validate_grid_params(
    lower_price: float,
    upper_price: float,
    grids: int,
    quantity_per_grid: float,
) -> None:
    """
    Validates grid strategy parameters.

    Args:
        lower_price:      Lower boundary of the grid.
        upper_price:      Upper boundary of the grid.
        grids:            Number of grid levels.
        quantity_per_grid: Quantity per individual grid order.

    Raises:
        ValidationError: On any invalid combination.
    """
    if lower_price >= upper_price:
        raise ValidationError(
            f"lower_price ({lower_price}) must be strictly less than upper_price ({upper_price})."
        )
    if grids < 2:
        raise ValidationError(f"grids must be at least 2. Got: {grids}")
    if quantity_per_grid <= 0:
        raise ValidationError(f"quantity_per_grid must be positive. Got: {quantity_per_grid}")
    logger.debug(
        f"Grid params validated: lower={lower_price}, upper={upper_price}, grids={grids}, qty={quantity_per_grid}"
    )


def validate_twap_params(total_quantity: float, intervals: int, interval_seconds: int) -> None:
    """
    Validates TWAP execution parameters.

    Args:
        total_quantity:    Total quantity to execute over time.
        intervals:         Number of child orders to split into.
        interval_seconds:  Seconds between each child order.

    Raises:
        ValidationError: On any invalid value.
    """
    if total_quantity <= 0:
        raise ValidationError(f"total_quantity must be positive. Got: {total_quantity}")
    if intervals < 2:
        raise ValidationError(f"intervals must be at least 2. Got: {intervals}")
    if interval_seconds < 1:
        raise ValidationError(f"interval_seconds must be at least 1. Got: {interval_seconds}")
    logger.debug(
        f"TWAP params validated: qty={total_quantity}, intervals={intervals}, every={interval_seconds}s"
    )
