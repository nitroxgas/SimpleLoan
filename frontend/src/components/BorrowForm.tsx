/**
 * BorrowForm Component
 *
 * Form for borrowing assets against collateral.
 */

import { useState } from "react";

interface Asset {
  id: string;
  name: string;
}

interface BorrowFormProps {
  availableAssets: Asset[];
  onSubmit: (
    collateralAmount: number,
    collateralAssetId: string,
    borrowAmount: number,
    borrowAssetId: string,
  ) => Promise<void>;
  disabled?: boolean;
}

export function BorrowForm({
  availableAssets,
  onSubmit,
  disabled = false,
}: BorrowFormProps) {
  const [collateralAsset, setCollateralAsset] = useState("");
  const [collateralAmount, setCollateralAmount] = useState("");
  const [borrowAsset, setBorrowAsset] = useState("");
  const [borrowAmount, setBorrowAmount] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ltv, setLtv] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate inputs
    if (
      !collateralAsset ||
      !collateralAmount ||
      !borrowAsset ||
      !borrowAmount
    ) {
      setError("All fields are required");
      return;
    }

    const collateralNum = parseFloat(collateralAmount);
    const borrowNum = parseFloat(borrowAmount);

    if (isNaN(collateralNum) || collateralNum <= 0) {
      setError("Invalid collateral amount");
      return;
    }

    if (isNaN(borrowNum) || borrowNum <= 0) {
      setError("Invalid borrow amount");
      return;
    }

    // Convert to satoshis
    const collateralSatoshis = Math.floor(collateralNum * 100000000);
    const borrowSatoshis = Math.floor(borrowNum * 100000000);

    // Calculate LTV (simplified for MVP)
    // In production, would use actual oracle prices
    const calculatedLtv = (borrowNum / collateralNum) * 100;

    if (calculatedLtv > 75) {
      setError(
        "LTV exceeds maximum of 75%. Reduce borrow amount or increase collateral.",
      );
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(
        collateralSatoshis,
        collateralAsset,
        borrowSatoshis,
        borrowAsset,
      );

      // Reset form
      setCollateralAsset("");
      setCollateralAmount("");
      setBorrowAsset("");
      setBorrowAmount("");
      setLtv(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to borrow assets");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Calculate LTV on input change
  const handleCollateralChange = (value: string) => {
    setCollateralAmount(value);
    updateLtv(value, borrowAmount);
  };

  const handleBorrowChange = (value: string) => {
    setBorrowAmount(value);
    updateLtv(collateralAmount, value);
  };

  const updateLtv = (collateral: string, borrow: string) => {
    const c = parseFloat(collateral);
    const b = parseFloat(borrow);
    if (c > 0 && b > 0) {
      setLtv((b / c) * 100);
    } else {
      setLtv(0);
    }
  };

  const getLtvColor = () => {
    if (ltv === 0) return "text-gray-400";
    if (ltv < 50) return "text-green-600";
    if (ltv < 75) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 p-6 bg-gray-800 rounded-lg shadow"
    >
      <div>
        <h2 className="text-2xl font-bold mb-4 text-white">Borrow Assets</h2>
        <p className="text-gray-400 mb-6">
          Deposit collateral to borrow assets. Max LTV: 75%
        </p>
      </div>

      {/* Collateral Section */}
      <div className="border border-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3 text-white">Collateral</h3>

        <div className="mb-3">
          <label
            htmlFor="collateralAsset"
            className="block text-sm font-medium text-gray-300 mb-2"
          >
            Asset
          </label>
          <select
            id="collateralAsset"
            value={collateralAsset}
            onChange={(e) => setCollateralAsset(e.target.value)}
            disabled={disabled || isSubmitting}
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 disabled:bg-gray-600"
            required
          >
            <option value="">Select collateral asset</option>
            {availableAssets.map((asset) => (
              <option key={asset.id} value={asset.id}>
                {asset.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            htmlFor="collateralAmount"
            className="block text-sm font-medium text-gray-300 mb-2"
          >
            Amount
          </label>
          <input
            type="number"
            id="collateralAmount"
            value={collateralAmount}
            onChange={(e) => handleCollateralChange(e.target.value)}
            disabled={disabled || isSubmitting}
            placeholder="0.00"
            step="0.00000001"
            min="0.00001"
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 disabled:bg-gray-600"
            required
          />
        </div>
      </div>

      {/* Borrow Section */}
      <div className="border border-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3 text-white">Borrow</h3>

        <div className="mb-3">
          <label
            htmlFor="borrowAsset"
            className="block text-sm font-medium text-gray-300 mb-2"
          >
            Asset
          </label>
          <select
            id="borrowAsset"
            value={borrowAsset}
            onChange={(e) => setBorrowAsset(e.target.value)}
            disabled={disabled || isSubmitting}
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 disabled:bg-gray-600"
            required
          >
            <option value="">Select asset to borrow</option>
            {availableAssets.map((asset) => (
              <option key={asset.id} value={asset.id}>
                {asset.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            htmlFor="borrowAmount"
            className="block text-sm font-medium text-gray-300 mb-2"
          >
            Amount
          </label>
          <input
            type="number"
            id="borrowAmount"
            value={borrowAmount}
            onChange={(e) => handleBorrowChange(e.target.value)}
            disabled={disabled || isSubmitting}
            placeholder="0.00"
            step="0.00000001"
            min="0.00001"
            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-2 focus:ring-blue-500 disabled:bg-gray-600"
            required
          />
        </div>
      </div>

      {/* LTV Display */}
      {ltv > 0 && (
        <div className="p-4 bg-gray-700 rounded-md">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-300">
              Loan-to-Value (LTV)
            </span>
            <span className={`text-lg font-bold ${getLtvColor()}`}>
              {ltv.toFixed(2)}%
            </span>
          </div>
          <div className="w-full bg-gray-600 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                ltv < 50
                  ? "bg-green-500"
                  : ltv < 75
                    ? "bg-yellow-500"
                    : "bg-red-500"
              }`}
              style={{ width: `${Math.min(ltv, 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Max LTV: 75% | Liquidation threshold: 80%
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-900 border border-red-700 rounded-md">
          <p className="text-sm font-semibold text-red-200 mb-1">Error:</p>
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={
          disabled ||
          isSubmitting ||
          !collateralAsset ||
          !collateralAmount ||
          !borrowAsset ||
          !borrowAmount
        }
        className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? "Processing..." : "Borrow Assets"}
      </button>
    </form>
  );
}
