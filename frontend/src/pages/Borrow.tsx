/**
 * Borrow Page - Borrow assets against collateral
 */

import { useState } from "react";
import { BorrowForm } from "../components/BorrowForm";
import { HealthFactor } from "../components/HealthFactor";
import { borrowAssets } from "../services/api";
import { useOraclePrices, formatPrice } from "../hooks/useOracle";

const AVAILABLE_ASSETS = [
  { id: "btc_asset_id_placeholder", name: "BTC" },
  { id: "usdt_asset_id_placeholder", name: "USDT" },
];

export function BorrowPage() {
  const [userAddress] = useState<string>("lq1qtest123"); // TODO: Get from wallet
  const [healthFactor, setHealthFactor] = useState<number | null>(null);
  const [borrowSuccess, setBorrowSuccess] = useState(false);

  // Fetch prices for display
  const { data: prices, isLoading: pricesLoading } = useOraclePrices(
    AVAILABLE_ASSETS.map((a) => a.id),
  );

  const handleBorrow = async (
    collateralAmount: number,
    collateralAssetId: string,
    borrowAmount: number,
    borrowAssetId: string,
  ) => {
    try {
      console.log("Borrow request:", {
        user_address: userAddress,
        collateral_asset_id: collateralAssetId,
        collateral_amount: collateralAmount,
        borrow_asset_id: borrowAssetId,
        borrow_amount: borrowAmount,
      });

      const response = await borrowAssets({
        user_address: userAddress,
        collateral_asset_id: collateralAssetId,
        collateral_amount: collateralAmount,
        borrow_asset_id: borrowAssetId,
        borrow_amount: borrowAmount,
      });

      // Update health factor
      setHealthFactor(response.health_factor);
      setBorrowSuccess(true);

      // Hide success message after 5 seconds
      setTimeout(() => setBorrowSuccess(false), 5000);

      console.log("Borrow successful:", response);
    } catch (error) {
      console.error("Borrow failed:", error);
      throw error;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-white">Borrow Assets</h1>

      {/* Success Message */}
      {borrowSuccess && (
        <div className="mb-6 p-4 bg-green-900 border border-green-700 rounded-md">
          <p className="text-green-200 font-semibold">✓ Borrow successful!</p>
          <p className="text-green-300 text-sm mt-1">
            Your debt position has been created. Monitor your health factor to
            avoid liquidation.
          </p>
        </div>
      )}

      {/* Current Prices */}
      {!pricesLoading && prices && (
        <div className="mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">
            Current Prices
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {AVAILABLE_ASSETS.map((asset) => {
              const price = prices[asset.id];
              return (
                <div key={asset.id} className="flex justify-between">
                  <span className="text-gray-400">{asset.name}:</span>
                  <span className="text-white font-medium">
                    {price ? formatPrice(price.price) : "Loading..."}
                  </span>
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Prices update every 60 seconds
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Borrow Form - 2/3 width */}
        <div className="lg:col-span-2">
          <BorrowForm
            onSubmit={handleBorrow}
            availableAssets={AVAILABLE_ASSETS}
          />
        </div>

        {/* Health Factor & Info - 1/3 width */}
        <div className="space-y-6">
          {/* Health Factor */}
          {healthFactor !== null && (
            <HealthFactor value={healthFactor} showDetails={true} />
          )}

          {/* Borrow Info Card */}
          <div className="p-6 bg-gray-800 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              How Borrowing Works
            </h3>
            <div className="space-y-3 text-sm text-gray-400">
              <div>
                <p className="font-medium text-gray-300 mb-1">
                  1. Deposit Collateral
                </p>
                <p>Lock your assets (e.g., BTC) as collateral</p>
              </div>
              <div>
                <p className="font-medium text-gray-300 mb-1">
                  2. Borrow Assets
                </p>
                <p>Borrow up to 75% of your collateral value</p>
              </div>
              <div>
                <p className="font-medium text-gray-300 mb-1">
                  3. Monitor Health
                </p>
                <p>Keep health factor above 1.0 to avoid liquidation</p>
              </div>
              <div>
                <p className="font-medium text-gray-300 mb-1">4. Repay Loan</p>
                <p>Repay borrowed amount + interest to unlock collateral</p>
              </div>
            </div>
          </div>

          {/* Risk Warning */}
          <div className="p-4 bg-yellow-900 border border-yellow-700 rounded-md">
            <h4 className="text-sm font-semibold text-yellow-200 mb-2">
              ⚠ Risk Warning
            </h4>
            <p className="text-xs text-yellow-300">
              If your health factor drops below 1.0, your position may be
              liquidated. Price volatility can affect your health factor.
            </p>
          </div>

          {/* Protocol Parameters */}
          <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
            <h4 className="text-sm font-semibold text-gray-300 mb-3">
              Protocol Parameters
            </h4>
            <div className="space-y-2 text-xs text-gray-400">
              <div className="flex justify-between">
                <span>Max LTV:</span>
                <span className="text-white">75%</span>
              </div>
              <div className="flex justify-between">
                <span>Liquidation Threshold:</span>
                <span className="text-white">80%</span>
              </div>
              <div className="flex justify-between">
                <span>Liquidation Bonus:</span>
                <span className="text-white">5%</span>
              </div>
              <div className="flex justify-between">
                <span>Interest Rate:</span>
                <span className="text-white">Variable</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Your Debt Positions */}
      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4 text-white">
          Your Debt Positions
        </h2>
        <div className="p-6 bg-gray-800 rounded-lg">
          <p className="text-gray-400">
            No debt positions yet. Borrow assets to get started!
          </p>
        </div>
      </div>
    </div>
  );
}
