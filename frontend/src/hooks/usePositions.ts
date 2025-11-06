/**
 * usePositions Hook
 *
 * Fetches and caches user supply positions.
 */

import { useQuery } from "@tanstack/react-query";
import { getPositions } from "../services/api";

interface Position {
  position_id: number;
  user_address: string;
  asset_id: string;
  atoken_amount: number;
  underlying_amount: number;
  accrued_interest: number;
  liquidity_index_at_supply: bigint;
  current_liquidity_index: bigint;
  created_at: string;
}

export function usePositions(userAddress: string | null) {
  return useQuery<Position[], Error>({
    queryKey: ["positions", userAddress],
    queryFn: () => {
      if (!userAddress) {
        throw new Error("User address is required");
      }
      return getPositions(userAddress);
    },
    enabled: !!userAddress,
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  });
}
