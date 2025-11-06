/**
 * Oracle Price Feed Type Definitions
 */

export interface OraclePriceFeed {
  /** Asset pair (e.g., "BTC/USD") */
  assetPair: string;
  
  /** Price in RAY precision (10^27) */
  price: bigint;
  
  /** Timestamp of price (Unix seconds) */
  timestamp: number;
  
  /** Oracle signature (hex) */
  signature: string;
  
  /** Oracle public key (hex) */
  publicKey: string;
}

export interface OraclePrice {
  /** Asset ID */
  assetId: string;
  
  /** Price in USD (RAY precision) */
  priceUsd: bigint;
  
  /** Timestamp */
  timestamp: number;
  
  /** Is price stale? */
  isStale: boolean;
}
