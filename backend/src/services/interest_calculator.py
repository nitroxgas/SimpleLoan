"""
Interest calculation service.

Handles RAY-based interest accrual and index updates.
"""

import time
from typing import Tuple

from ..utils.ray_math import RAY, accrue_index, ray_div, ray_mul


class InterestCalculator:
    """
    Service for calculating interest rates and index updates.
    
    Implements AAVE's cumulative index accounting:
    - liquidityIndex: Grows with supply interest
    - variableBorrowIndex: Grows with borrow interest
    """
    
    @staticmethod
    def accrue_indices(
        current_liquidity_index: int,
        current_borrow_index: int,
        liquidity_rate: int,
        borrow_rate: int,
        last_update_timestamp: int,
    ) -> Tuple[int, int]:
        """
        Calculate new indices after time passes.
        
        Args:
            current_liquidity_index: Current supply index (RAY)
            current_borrow_index: Current borrow index (RAY)
            liquidity_rate: Supply rate per second (RAY)
            borrow_rate: Borrow rate per second (RAY)
            last_update_timestamp: Last update time (Unix seconds)
        
        Returns:
            Tuple of (new_liquidity_index, new_borrow_index)
        """
        current_time = int(time.time())
        time_delta = current_time - last_update_timestamp
        
        if time_delta <= 0:
            return current_liquidity_index, current_borrow_index
        
        # Accrue supply index
        new_liquidity_index = accrue_index(
            current_liquidity_index,
            liquidity_rate,
            time_delta
        )
        
        # Accrue borrow index
        new_borrow_index = accrue_index(
            current_borrow_index,
            borrow_rate,
            time_delta
        )
        
        return new_liquidity_index, new_borrow_index
    
    @staticmethod
    def calculate_atoken_amount(
        underlying_amount: int,
        liquidity_index: int
    ) -> int:
        """
        Calculate aToken amount for a given underlying amount.
        
        Formula: atoken = underlying / liquidity_index
        
        Args:
            underlying_amount: Amount of underlying asset (satoshis)
            liquidity_index: Current liquidity index (RAY)
        
        Returns:
            aToken amount (satoshis)
        """
        # Convert underlying to RAY precision
        underlying_ray = underlying_amount * RAY
        
        # Divide by index to get aToken amount
        atoken_amount = ray_div(underlying_ray, liquidity_index)
        
        # Convert back to satoshis
        return atoken_amount // RAY
    
    @staticmethod
    def calculate_underlying_amount(
        atoken_amount: int,
        liquidity_index: int
    ) -> int:
        """
        Calculate underlying amount for a given aToken amount.
        
        Formula: underlying = atoken * liquidity_index
        
        Args:
            atoken_amount: Amount of aTokens (satoshis)
            liquidity_index: Current liquidity index (RAY)
        
        Returns:
            Underlying asset amount (satoshis)
        """
        # Convert aToken to RAY precision
        atoken_ray = atoken_amount * RAY
        
        # Multiply by index to get underlying
        underlying_amount = ray_mul(atoken_ray, liquidity_index)
        
        # Convert back to satoshis
        return underlying_amount // RAY
    
    @staticmethod
    def calculate_accrued_interest(
        principal: int,
        initial_index: int,
        current_index: int
    ) -> int:
        """
        Calculate interest accrued on a position.
        
        Formula: interest = principal * (current_index / initial_index - 1)
        
        Args:
            principal: Initial principal amount (satoshis)
            initial_index: Index when position opened (RAY)
            current_index: Current index (RAY)
        
        Returns:
            Accrued interest (satoshis)
        """
        if current_index <= initial_index:
            return 0
        
        # Calculate growth factor
        growth_factor = ray_div(current_index, initial_index)
        
        # Calculate new amount
        principal_ray = principal * RAY
        new_amount = ray_mul(principal_ray, growth_factor) // RAY
        
        # Interest is the difference
        return new_amount - principal
