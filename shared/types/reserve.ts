/**
 * Reserve UTXO Type Definitions
 * 
 * Mirrors the on-chain Reserve UTXO structure (~320 bytes)
 */

export interface ReserveUTXO {
  /** Liquid asset ID (32 bytes hex) */
  assetId: string;
  
  /** Total supplied assets (satoshis) */
  totalLiquidity: bigint;
  
  /** Total borrowed assets (satoshis) */
  totalBorrowed: bigint;
  
  /** Cumulative supply interest index (RAY 10^27) */
  liquidityIndex: bigint;
  
  /** Cumulative borrow interest index (RAY 10^27) */
  variableBorrowIndex: bigint;
  
  /** Current supply rate per second (RAY) */
  currentLiquidityRate: bigint;
  
  /** Current borrow rate per second (RAY) */
  currentVariableBorrowRate: bigint;
  
  /** Last update timestamp (Unix seconds) */
  lastUpdateTimestamp: number;
  
  /** Protocol fee percentage (RAY) */
  reserveFactor: bigint;
  
  /** Liquidation threshold (RAY, e.g., 0.8 * RAY = 80%) */
  liquidationThreshold: bigint;
  
  /** Loan-to-value ratio (RAY, e.g., 0.75 * RAY = 75%) */
  ltv: bigint;
}

export interface ReserveState {
  /** Asset ID */
  assetId: string;
  
  /** Current UTXO reference (txid:vout) */
  utxoId: string;
  
  /** Reserve data */
  reserve: ReserveUTXO;
  
  /** Calculated fields */
  availableLiquidity: bigint;
  utilizationRate: bigint;
}
