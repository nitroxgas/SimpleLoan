/**
 * RAY Fixed-Point Arithmetic Constants
 * 
 * RAY = 10^27 precision for interest rate calculations (AAVE standard)
 */

// RAY constant: 10^27
export const RAY = BigInt("1000000000000000000000000000");

// Half RAY for rounding
export const HALF_RAY = RAY / BigInt(2);

// Seconds per year (365 days)
export const SECONDS_PER_YEAR = 31536000;

/**
 * Multiply two RAY values
 */
export function rayMul(a: bigint, b: bigint): bigint {
  if (a === BigInt(0) || b === BigInt(0)) {
    return BigInt(0);
  }
  return (a * b + HALF_RAY) / RAY;
}

/**
 * Divide two RAY values
 */
export function rayDiv(a: bigint, b: bigint): bigint {
  if (b === BigInt(0)) {
    throw new Error("Division by zero in rayDiv");
  }
  const halfB = b / BigInt(2);
  return (a * RAY + halfB) / b;
}

/**
 * Convert RAY to percentage
 */
export function rayToPercentage(value: bigint): number {
  return Number((value * BigInt(100)) / RAY) / 100;
}

/**
 * Convert percentage to RAY
 */
export function percentageToRay(percentage: number): bigint {
  return BigInt(Math.floor(percentage * 100)) * RAY / BigInt(100);
}
