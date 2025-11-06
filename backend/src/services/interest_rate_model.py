"""
Interest Rate Model (AAVE-style) for Fantasma Protocol

Calculates variable borrow rate and liquidity (supply) rate based on utilization.
Rates are returned as per-second rates in RAY precision (1e27).
"""

from typing import Tuple

from ..utils.ray_math import RAY, ray_div, ray_mul

SECONDS_PER_YEAR = 31536000


class InterestRateModel:
    """Piecewise-linear interest rate model similar to AAVE v2."""

    # Parameters (annual, RAY precision)
    BASE_BORROW_RATE = int(0.02 * RAY)  # 2% base per year
    OPTIMAL_UTILIZATION = int(0.80 * RAY)  # 80%
    SLOPE1 = int(0.20 * RAY)  # 20% per year until optimal
    SLOPE2 = int(1.00 * RAY)  # +100% per year above optimal

    @staticmethod
    def _to_per_second(rate_annual: int) -> int:
        """Convert annual rate (RAY) to per-second rate (RAY)."""
        # per_second = annual / SECONDS_PER_YEAR
        return ray_div(rate_annual, SECONDS_PER_YEAR)

    def calculate_borrow_rate_annual(self, utilization: int) -> int:
        """
        Calculate variable borrow rate (annual, RAY) given utilization (RAY).
        """
        u = utilization
        u_opt = self.OPTIMAL_UTILIZATION
        base = self.BASE_BORROW_RATE
        s1 = self.SLOPE1
        s2 = self.SLOPE2

        if u <= 0:
            return base

        if u <= u_opt:
            # base + s1 * (u/u_opt)
            ratio = ray_div(u, u_opt)
            return base + ray_mul(s1, ratio)

        # Above optimal: base + s1 + s2 * ((u - u_opt) / (1 - u_opt))
        excess = u - u_opt
        denom = RAY - u_opt
        step2 = ray_mul(s2, ray_div(excess, denom))
        return base + s1 + step2

    def calculate_rates(self, total_liquidity: int, total_borrowed: int, reserve_factor: int) -> Tuple[int, int]:
        """
        Calculate per-second borrow and liquidity rates (RAY).

        Returns: (liquidity_rate_per_sec, borrow_rate_per_sec)
        """
        if total_liquidity <= 0:
            return 0, 0

        utilization = (total_borrowed * RAY) // total_liquidity
        borrow_rate_annual = self.calculate_borrow_rate_annual(utilization)
        borrow_rate_per_sec = self._to_per_second(borrow_rate_annual)

        # supply_rate = borrow_rate * utilization * (1 - reserve_factor)
        one_minus_rf = RAY - reserve_factor
        liquidity_rate_per_sec = ray_mul(ray_mul(borrow_rate_per_sec, utilization), one_minus_rf)

        return liquidity_rate_per_sec, borrow_rate_per_sec
