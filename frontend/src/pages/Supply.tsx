/**
 * Supply Page - Main page for supplying assets
 */

import { useState } from "react";
import { SupplyForm } from "../components/SupplyForm";
import { PositionCard } from "../components/PositionCard";
import { usePositions } from "../hooks/usePositions";
import { supplyAssets, withdrawAssets } from "../services/api";

const AVAILABLE_ASSETS = [
  { id: "btc_asset_id_placeholder", name: "BTC" },
  { id: "usdt_asset_id_placeholder", name: "USDT" },
];

export function SupplyPage() {
  const [userAddress] = useState<string>("lq1qtest123"); // TODO: Get from wallet
  const {
    data: positions,
    isLoading,
    error,
    refetch,
  } = usePositions(userAddress);
  const [withdrawAsset, setWithdrawAsset] = useState<string>("");
  const [withdrawAmountStr, setWithdrawAmountStr] = useState<string>("");
  const [withdrawAll, setWithdrawAll] = useState<boolean>(false);
  const [withdrawing, setWithdrawing] = useState<boolean>(false);
  const [withdrawError, setWithdrawError] = useState<string>("");
  const [withdrawSuccess, setWithdrawSuccess] = useState<string>("");

  const handleSupply = async (amount: number, assetId: string) => {
    // Ensure amount is an integer
    const amountInt = Math.floor(amount);

    console.log("Supply request:", {
      user_address: userAddress,
      asset_id: assetId,
      amount: amountInt,
    });

    await supplyAssets({
      user_address: userAddress,
      asset_id: assetId,
      amount: amountInt,
    });
    refetch();
  };

  const handleWithdraw = async (e: React.FormEvent) => {
    e.preventDefault();
    setWithdrawError("");
    setWithdrawSuccess("");
    if (!withdrawAsset) {
      setWithdrawError("Please select an asset to withdraw");
      return;
    }
    try {
      setWithdrawing(true);
      // Amount in satoshis. If withdrawAll, send 0
      const amountFloat = parseFloat(withdrawAmountStr || "0");
      const amountSats = withdrawAll
        ? 0
        : Math.max(0, Math.floor(amountFloat * 1e8));

      console.log("Withdraw request:", {
        user_address: userAddress,
        asset_id: withdrawAsset,
        amount: amountSats,
      });

      const res = await withdrawAssets({
        user_address: userAddress,
        asset_id: withdrawAsset,
        amount: amountSats,
      });

      setWithdrawSuccess(
        `Withdrew ${res.amount_withdrawn / 1e8} from ${AVAILABLE_ASSETS.find((a) => a.id === withdrawAsset)?.name || withdrawAsset}`,
      );
      setWithdrawAmountStr("");
      setWithdrawAll(false);
      setWithdrawAsset("");
      refetch();
    } catch (err: any) {
      setWithdrawError(err.message || "Withdraw failed");
    } finally {
      setWithdrawing(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-white">
        Fantasma Protocol - Supply Assets
      </h1>

      {error && (
        <div className="mb-4 p-4 bg-red-900 border border-red-700 rounded-md">
          <p className="text-red-200">
            Error loading positions: {error.message}
          </p>
          <p className="text-sm text-red-300 mt-2">
            Make sure the backend is running at http://localhost:8000
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <SupplyForm
          onSubmit={handleSupply}
          availableAssets={AVAILABLE_ASSETS}
        />

        <div>
          <h2 className="text-2xl font-bold mb-4 text-white">Your Positions</h2>
          {isLoading ? (
            <p className="text-gray-400">Loading positions...</p>
          ) : positions && positions.length > 0 ? (
            <div className="space-y-4">
              {positions.map((pos) => (
                <PositionCard key={pos.position_id} position={pos} />
              ))}
            </div>
          ) : (
            <div className="p-6 bg-gray-800 rounded-lg">
              <p className="text-gray-400">
                No positions yet. Supply assets to get started!
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Withdraw Card */}
      <div className="mt-8 p-6 bg-gray-800 rounded-lg border border-gray-700 max-w-xl">
        <h2 className="text-2xl font-bold mb-4 text-white">Withdraw Assets</h2>

        {withdrawSuccess && (
          <div className="mb-4 p-3 bg-green-900 border border-green-700 rounded text-green-200">
            {withdrawSuccess}
          </div>
        )}
        {withdrawError && (
          <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded text-red-200">
            {withdrawError}
          </div>
        )}

        <form onSubmit={handleWithdraw} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-300 mb-1">Asset</label>
            <select
              value={withdrawAsset}
              onChange={(e) => setWithdrawAsset(e.target.value)}
              className="w-full bg-gray-900 text-white p-2 rounded border border-gray-700"
              required
            >
              <option value="" disabled>
                Select an asset
              </option>
              {AVAILABLE_ASSETS.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-300 mb-1">Amount</label>
            <input
              type="number"
              step="0.00000001"
              min="0"
              value={withdrawAmountStr}
              onChange={(e) => setWithdrawAmountStr(e.target.value)}
              className="w-full bg-gray-900 text-white p-2 rounded border border-gray-700"
              placeholder="0.0 (leave 0 or check 'All' to withdraw everything)"
              disabled={withdrawAll}
            />
            <div className="mt-2 flex items-center gap-2">
              <input
                id="withdrawAll"
                type="checkbox"
                checked={withdrawAll}
                onChange={(e) => setWithdrawAll(e.target.checked)}
              />
              <label htmlFor="withdrawAll" className="text-sm text-gray-400">
                Withdraw all
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={withdrawing}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50"
          >
            {withdrawing ? "Withdrawing..." : "Withdraw"}
          </button>
        </form>
      </div>
    </div>
  );
}
