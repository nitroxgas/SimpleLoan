/**
 * useOracle Hook
 *
 * Fetch and display current asset prices from oracle.
 */

import { useQuery } from "@tanstack/react-query";

interface PriceFeed {
  asset_id: string;
  price: number; // In RAY precision
  timestamp: string;
}

const RAY = BigInt("1000000000000000000000000000"); // 10^27

// Simulated prices for MVP (matching backend)
const SIMULATED_PRICES: Record<string, number> = {
  btc_asset_id_placeholder: 60000, // $60,000
  usdt_asset_id_placeholder: 1, // $1
};

/**
 * Get price for a single asset.
 *
 * For MVP, returns simulated prices.
 * Production would call backend API to get oracle prices.
 */
export function useOraclePrice(assetId: string) {
  return useQuery({
    queryKey: ["oracle", "price", assetId],
    queryFn: async (): Promise<PriceFeed> => {
      // Simulate API call delay
      await new Promise((resolve) => setTimeout(resolve, 100));

      const priceUsd = SIMULATED_PRICES[assetId] || 0;

      return {
        asset_id: assetId,
        price: priceUsd * Number(RAY),
        timestamp: new Date().toISOString(),
      };
    },
    staleTime: 60000, // 60 seconds
    refetchInterval: 60000, // Refetch every 60 seconds
  });
}

/**
 * Get prices for multiple assets.
 */
export function useOraclePrices(assetIds: string[]) {
  return useQuery({
    queryKey: ["oracle", "prices", ...assetIds],
    queryFn: async (): Promise<Record<string, PriceFeed>> => {
      await new Promise((resolve) => setTimeout(resolve, 100));

      const prices: Record<string, PriceFeed> = {};

      for (const assetId of assetIds) {
        const priceUsd = SIMULATED_PRICES[assetId] || 0;
        prices[assetId] = {
          asset_id: assetId,
          price: priceUsd * Number(RAY),
          timestamp: new Date().toISOString(),
        };
      }

      return prices;
    },
    staleTime: 60000,
    refetchInterval: 60000,
  });
}

/**
 * Format price for display.
 */
export function formatPrice(price: number): string {
  const priceUsd = price / Number(RAY);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(priceUsd);
}

/**
 * Calculate USD value of an amount.
 */
export function calculateValue(amount: number, price: number): number {
  // amount in satoshis, price in RAY
  // value = (amount / 10^8) * (price / RAY)
  return (amount / 100000000) * (price / Number(RAY));
}
