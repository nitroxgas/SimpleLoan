/**
 * SupplyForm Component
 *
 * Form for supplying assets to lending pools.
 */

import React, { useState } from "react";

interface SupplyFormProps {
  onSubmit: (amount: number, assetId: string) => Promise<void>;
  disabled?: boolean;
  availableAssets?: Array<{ id: string; name: string }>;
}

export function SupplyForm({
  onSubmit,
  disabled = false,
  availableAssets = [],
}: SupplyFormProps) {
  const [amount, setAmount] = useState<string>("");
  const [selectedAsset, setSelectedAsset] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    const amountNum = parseFloat(amount);
    if (isNaN(amountNum) || amountNum <= 0) {
      setError("Please enter a valid amount");
      return;
    }

    if (!selectedAsset) {
      setError("Please select an asset");
      return;
    }

    // Convert to satoshis (assuming 8 decimals)
    const satoshis = Math.floor(amountNum * 100000000);

    if (satoshis < 1000) {
      setError("Minimum amount is 0.00001 (1000 satoshis)");
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(satoshis, selectedAsset);

      // Reset form on success
      setAmount("");
      setSelectedAsset("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to supply assets");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 p-6 bg-white rounded-lg shadow"
    >
      <div>
        <h2 className="text-2xl font-bold mb-4">Supply Assets</h2>
        <p className="text-gray-600 mb-6">
          Deposit assets to earn interest. You'll receive aTokens representing
          your share.
        </p>
      </div>

      {/* Asset Selector */}
      <div>
        <label
          htmlFor="asset"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Asset
        </label>
        <select
          id="asset"
          value={selectedAsset}
          onChange={(e) => setSelectedAsset(e.target.value)}
          disabled={disabled || isSubmitting}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          required
        >
          <option value="">Select an asset</option>
          {availableAssets.map((asset) => (
            <option key={asset.id} value={asset.id}>
              {asset.name}
            </option>
          ))}
        </select>
      </div>

      {/* Amount Input */}
      <div>
        <label
          htmlFor="amount"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Amount
        </label>
        <div className="relative">
          <input
            type="number"
            id="amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            disabled={disabled || isSubmitting}
            placeholder="0.00"
            step="0.00000001"
            min="0.00001"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            required
          />
          <span className="absolute right-4 top-2 text-gray-500">
            {selectedAsset
              ? availableAssets.find((a) => a.id === selectedAsset)?.name
              : "Asset"}
          </span>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Minimum: 0.00001 (1000 satoshis)
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm font-semibold text-red-800 mb-1">Error:</p>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={disabled || isSubmitting || !amount || !selectedAsset}
        className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? "Supplying..." : "Supply Assets"}
      </button>

      {/* Info */}
      <div className="mt-4 p-4 bg-blue-50 rounded-md">
        <h3 className="text-sm font-medium text-blue-900 mb-2">How it works</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• You receive aTokens representing your share of the pool</li>
          <li>• Your share grows automatically as interest accrues</li>
          <li>• Withdraw anytime (subject to available liquidity)</li>
        </ul>
      </div>
    </form>
  );
}
