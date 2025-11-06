/**
 * Liquidate Page - Liquidate unhealthy positions
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getLiquidatablePositions,
  liquidatePosition,
  LiquidatablePosition,
} from "../services/api";
import { formatPrice, useOraclePrices } from "../hooks/useOracle";

const RAY = BigInt("1000000000000000000000000000"); // 10^27

const AVAILABLE_ASSETS = [
  { id: "btc_asset_id_placeholder", name: "BTC" },
  { id: "usdt_asset_id_placeholder", name: "USDT" },
];

export function LiquidatePage() {
  const [liquidatorAddress] = useState<string>("lq1qliquidator123"); // TODO: Get from wallet
  const [liquidationSuccess, setLiquidationSuccess] = useState(false);
  const [error, setError] = useState<string>("");

  // Fetch liquidatable positions
  const {
    data: positions,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["liquidatable-positions"],
    queryFn: getLiquidatablePositions,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  // Fetch prices
  const { data: prices } = useOraclePrices(AVAILABLE_ASSETS.map((a) => a.id));

  const handleLiquidate = async (position: LiquidatablePosition) => {
    try {
      setError("");

      const response = await liquidatePosition({
        liquidator_address: liquidatorAddress,
        position_id: position.position_id,
        // Full liquidation by default (repay_amount omitted)
      });

      setLiquidationSuccess(true);

      // Refetch positions
      setTimeout(() => {
        refetch();
        setLiquidationSuccess(false);
      }, 3000);

      console.log("Liquidation successful:", response);
    } catch (err: any) {
      setError(err.message || "Liquidation failed");
      console.error("Liquidation error:", err);
    }
  };

  const getAssetName = (assetId: string) => {
    return (
      AVAILABLE_ASSETS.find((a) => a.id === assetId)?.name ||
      assetId.slice(0, 8)
    );
  };

  const formatAmount = (amount: number, assetId: string) => {
    const decimals = assetId.includes("btc") ? 8 : 8;
    return (amount / Math.pow(10, decimals)).toFixed(decimals);
  };

  const formatHealthFactor = (hf: number) => {
    return (hf / Number(RAY)).toFixed(2);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-white">
        Liquidate Positions
      </h1>

      {/* Success Message */}
      {liquidationSuccess && (
        <div className="mb-6 p-4 bg-green-900 border border-green-700 rounded-md">
          <p className="text-green-200 font-semibold">
            ✓ Liquidation successful!
          </p>
          <p className="text-green-300 text-sm mt-1">
            Position liquidated. Collateral transferred to your address.
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-md">
          <p className="text-red-200 font-semibold">✗ Liquidation failed</p>
          <p className="text-red-300 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Info Box */}
      <div className="mb-6 p-6 bg-gray-800 rounded-lg border border-gray-700">
        <h2 className="text-lg font-semibold text-white mb-3">
          How Liquidation Works
        </h2>
        <div className="space-y-2 text-sm text-gray-400">
          <p>
            • Positions with{" "}
            <span className="text-red-400 font-semibold">
              health factor &lt; 1.0
            </span>{" "}
            can be liquidated
          </p>
          <p>
            • Liquidators repay the debt and receive collateral +{" "}
            <span className="text-green-400 font-semibold">5% bonus</span>
          </p>
          <p>• This maintains protocol solvency and protects lenders</p>
        </div>
      </div>

      {/* Current Prices */}
      {prices && (
        <div className="mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <h2 className="text-sm font-semibold text-gray-300 mb-3">
            Current Prices
          </h2>
          <div className="flex gap-6">
            {AVAILABLE_ASSETS.map((asset) => {
              const price = prices[asset.id];
              return (
                <div key={asset.id} className="flex items-center gap-2">
                  <span className="text-gray-400">{asset.name}:</span>
                  <span className="text-white font-medium">
                    {price ? formatPrice(price.price) : "Loading..."}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Liquidatable Positions */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">
            Liquidatable Positions ({positions?.length || 0})
          </h2>
        </div>

        {isLoading && (
          <div className="p-8 text-center text-gray-400">
            Loading positions...
          </div>
        )}

        {!isLoading && positions && positions.length === 0 && (
          <div className="p-8 text-center text-gray-400">
            <p className="text-lg mb-2">🎉 All positions are healthy!</p>
            <p className="text-sm">No liquidatable positions at the moment.</p>
          </div>
        )}

        {!isLoading && positions && positions.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Position ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Collateral
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Debt
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Health Factor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {positions.map((position) => (
                  <tr key={position.position_id} className="hover:bg-gray-750">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      #{position.position_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {position.user_address.slice(0, 10)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="text-white">
                        {formatAmount(
                          position.collateral_amount,
                          position.collateral_asset_id,
                        )}{" "}
                        {getAssetName(position.collateral_asset_id)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="text-white">
                        {formatAmount(
                          position.current_debt,
                          position.borrowed_asset_id,
                        )}{" "}
                        {getAssetName(position.borrowed_asset_id)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="px-2 py-1 rounded-full text-xs font-semibold bg-red-900 text-red-200">
                        {formatHealthFactor(position.health_factor)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleLiquidate(position)}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md font-medium transition-colors"
                      >
                        Liquidate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Liquidation Details */}
      {positions && positions.length > 0 && (
        <div className="mt-6 p-4 bg-yellow-900 border border-yellow-700 rounded-md">
          <h3 className="text-sm font-semibold text-yellow-200 mb-2">
            ⚠ Important
          </h3>
          <ul className="text-xs text-yellow-300 space-y-1">
            <li>• You must have sufficient balance to repay the debt</li>
            <li>• You will receive collateral + 5% liquidation bonus</li>
            <li>• Liquidation is final and cannot be reversed</li>
            <li>• Make sure you understand the risks before proceeding</li>
          </ul>
        </div>
      )}
    </div>
  );
}
