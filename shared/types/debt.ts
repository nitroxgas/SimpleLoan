/**
 * Debt UTXO Type Definitions
 * 
 * Mirrors the on-chain Debt UTXO structure (~128 bytes)
 */

export interface DebtUTXO {
  /** User's Liquid address */
  userAddress: string;
  
  /** Borrowed asset ID */
  borrowedAssetId: string;
  
  /** Collateral asset ID */
  collateralAssetId: string;
  
  /** Principal borrowed amount (satoshis) */
  principalBorrowed: bigint;
  
  /** Collateral amount (satoshis) */
  collateralAmount: bigint;
  
  /** Borrow index at position open (RAY) */
  borrowIndexAtOpen: bigint;
  
  /** Timestamp when position opened (Unix seconds) */
  openedAt: number;
}

export interface DebtPosition {
  /** Position ID */
  id: string;
  
  /** User address */
  userAddress: string;
  
  /** Current UTXO reference (txid:vout) */
  utxoId: string;
  
  /** Debt data */
  debt: DebtUTXO;
  
  /** Calculated fields */
  currentDebt: bigint;
  healthFactor: bigint;
  liquidatable: boolean;
}
