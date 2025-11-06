"""
RAY Fixed-Point Arithmetic Library

RAY = 10^27 precision for interest rate calculations (AAVE standard)
All operations use Python's arbitrary precision integers to avoid overflow.
"""

from typing import Union

# RAY constant: 10^27
RAY: int = 10**27

# Half RAY for rounding
HALF_RAY: int = RAY // 2

# Seconds per year (365 days)
SECONDS_PER_YEAR: int = 31536000


def ray_mul(a: int, b: int) -> int:
    """
    Multiply two RAY values.
    
    Formula: (a * b + HALF_RAY) // RAY
    
    Args:
        a: First RAY value
        b: Second RAY value
    
    Returns:
        Product in RAY precision
    
    Example:
        >>> ray_mul(2 * RAY, 3 * RAY)  # 2.0 * 3.0 = 6.0
        6000000000000000000000000000
    """
    if a == 0 or b == 0:
        return 0
    
    return (a * b + HALF_RAY) // RAY


def ray_div(a: int, b: int) -> int:
    """
    Divide two RAY values.
    
    Formula: (a * RAY + b // 2) // b
    
    Args:
        a: Numerator in RAY
        b: Denominator in RAY
    
    Returns:
        Quotient in RAY precision
    
    Raises:
        ZeroDivisionError: If b is zero
    
    Example:
        >>> ray_div(6 * RAY, 2 * RAY)  # 6.0 / 2.0 = 3.0
        3000000000000000000000000000
    """
    if b == 0:
        raise ZeroDivisionError("Division by zero in ray_div")
    
    half_b = b // 2
    return (a * RAY + half_b) // b


def accrue_index(
    current_index: int,
    rate_per_second: int,
    time_delta: int
) -> int:
    """
    Calculate new cumulative index after time passes.
    
    Formula: current_index * (1 + rate_per_second * time_delta)
    
    This is the core of AAVE's cumulative index accounting:
    - liquidityIndex grows with supply interest
    - variableBorrowIndex grows with borrow interest
    
    Args:
        current_index: Current index value in RAY
        rate_per_second: Interest rate per second in RAY
        time_delta: Seconds elapsed since last update
    
    Returns:
        New index value in RAY
    
    Example:
        >>> # 2% annual rate = 0.02 / 31536000 per second
        >>> rate = (2 * RAY) // (100 * SECONDS_PER_YEAR)
        >>> accrue_index(RAY, rate, 86400)  # 1 day
        1000000000548000000000000000
    """
    if time_delta == 0:
        return current_index
    
    # Calculate: rate_per_second * time_delta
    rate_delta = rate_per_second * time_delta
    
    # Calculate: 1 + rate_delta (in RAY)
    growth_factor = RAY + rate_delta
    
    # Multiply: current_index * growth_factor
    return ray_mul(current_index, growth_factor)


def calculate_compound_interest(
    principal: int,
    rate_per_second: int,
    time_delta: int
) -> int:
    """
    Calculate compound interest accrued.
    
    Formula: principal * ((1 + rate)^time - 1)
    Approximation: principal * rate * time (for small rates)
    
    Args:
        principal: Principal amount in RAY
        rate_per_second: Interest rate per second in RAY
        time_delta: Seconds elapsed
    
    Returns:
        Interest accrued in RAY
    """
    if time_delta == 0 or rate_per_second == 0:
        return 0
    
    # For small time periods, use linear approximation
    # interest = principal * rate * time
    interest = ray_mul(principal, rate_per_second * time_delta)
    
    return interest


def calculate_linear_interest(
    principal: int,
    rate_per_second: int,
    time_delta: int
) -> int:
    """
    Calculate simple (linear) interest.
    
    Formula: principal * rate * time
    
    Args:
        principal: Principal amount in RAY
        rate_per_second: Interest rate per second in RAY
        time_delta: Seconds elapsed
    
    Returns:
        Interest accrued in RAY
    """
    if time_delta == 0 or rate_per_second == 0:
        return 0
    
    return ray_mul(principal, rate_per_second * time_delta)


def ray_to_decimal(value: int, decimals: int = 18) -> int:
    """
    Convert RAY value to token decimal representation.
    
    Args:
        value: Value in RAY (10^27)
        decimals: Token decimals (default 18 for BTC/ETH)
    
    Returns:
        Value in token decimals
    
    Example:
        >>> ray_to_decimal(RAY, 18)  # 1.0 RAY to 18 decimals
        1000000000000000000
    """
    if decimals >= 27:
        return value * (10 ** (decimals - 27))
    else:
        return value // (10 ** (27 - decimals))


def decimal_to_ray(value: int, decimals: int = 18) -> int:
    """
    Convert token decimal value to RAY.
    
    Args:
        value: Value in token decimals
        decimals: Token decimals (default 18)
    
    Returns:
        Value in RAY (10^27)
    
    Example:
        >>> decimal_to_ray(1000000000000000000, 18)  # 1.0 in 18 decimals
        1000000000000000000000000000
    """
    if decimals >= 27:
        return value // (10 ** (decimals - 27))
    else:
        return value * (10 ** (27 - decimals))


def percentage_to_ray(percentage: float) -> int:
    """
    Convert percentage to RAY.
    
    Args:
        percentage: Percentage value (e.g., 5.5 for 5.5%)
    
    Returns:
        RAY value
    
    Example:
        >>> percentage_to_ray(5.5)  # 5.5%
        55000000000000000000000000
    """
    return int(percentage * RAY / 100)


def ray_to_percentage(value: int) -> float:
    """
    Convert RAY to percentage.
    
    Args:
        value: RAY value
    
    Returns:
        Percentage (e.g., 5.5 for 5.5%)
    
    Example:
        >>> ray_to_percentage(55000000000000000000000000)
        5.5
    """
    return (value * 100) / RAY
