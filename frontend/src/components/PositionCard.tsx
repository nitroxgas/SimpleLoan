/**
 * PositionCard Component
 *
 * Displays a user's supply position with current value and interest.
 */

import React from "react";
import { rayToPercentage } from "../../../shared/constants/ray";

interface Position {
  position_id: number;
  asset_id: string;
  atoken_amount: number;
  underlying_amount: number;
  accrued_interest: number;
  liquidity_index_at_supply: bigint;
  current_liquidity_index: bigint;
  created_at: string;
}

interface PositionCardProps {
  position: Position;
  assetName?: string;
  onWithdraw?: (positionId: number) => void;
}

export function PositionCard({
  position,
  assetName = "Asset",
  onWithdraw,
}: PositionCardProps) {
  // Convert satoshis to display format (8 decimals)
  const formatAmount = (satoshis: number): string => {
    return (satoshis / 100000000).toFixed(8);
  };

  // Calculate APY from index growth
  const calculateAPY = (): number => {
    const indexGrowth =
      Number(position.current_liquidity_index) /
      Number(position.liquidity_index_at_supply);

    // Approximate APY (simplified)
    const timeDiff =
      (Date.now() - new Date(position.created_at).getTime()) / 1000;
    const yearlyGrowth = Math.pow(indexGrowth, (365 * 24 * 3600) / timeDiff);
    return (yearlyGrowth - 1) * 100;
  };

  const apy = calculateAPY();
  const hasProfit = position.accrued_interest > 0;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{assetName}</h3>
          <p className="text-sm text-gray-500">
            Position #{position.position_id}
          </p>
        </div>
        <div className="text-right">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              hasProfit
                ? "bg-green-100 text-green-800"
                : "bg-gray-100 text-gray-800"
            }`}
          >
            {apy > 0 ? `${apy.toFixed(2)}% APY` : "No yield yet"}
          </span>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Current Value */}
        <div>
          <p className="text-sm text-gray-500 mb-1">Current Value</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatAmount(position.underlying_amount)}
          </p>
          <p className="text-xs text-gray-500">{assetName}</p>
        </div>

        {/* Accrued Interest */}
        <div>
          <p className="text-sm text-gray-500 mb-1">Interest Earned</p>
          <p
            className={`text-2xl font-bold ${
              hasProfit ? "text-green-600" : "text-gray-900"
            }`}
          >
            +{formatAmount(position.accrued_interest)}
          </p>
          <p className="text-xs text-gray-500">{assetName}</p>
        </div>
      </div>

      {/* Additional Details */}
      <div className="border-t border-gray-200 pt-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">aToken Balance</span>
          <span className="font-medium text-gray-900">
            {formatAmount(position.atoken_amount)}
          </span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Supplied On</span>
          <span className="font-medium text-gray-900">
            {new Date(position.created_at).toLocaleDateString()}
          </span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Liquidity Index</span>
          <span className="font-mono text-xs text-gray-600">
            {rayToPercentage(position.current_liquidity_index).toFixed(4)}
          </span>
        </div>
      </div>

      {/* Actions */}
      {onWithdraw && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={() => onWithdraw(position.position_id)}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          >
            Withdraw
          </button>
        </div>
      )}
    </div>
  );
}
