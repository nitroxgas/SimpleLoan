/**
 * Dashboard Page - Display all reserves, utilization, and current rates
 */

import { useQuery } from "@tanstack/react-query";
import { getReserves, Reserve } from "../services/api";

const RAY_NUM = 1e27; // numeric approximation for UI only
const SECONDS_PER_YEAR = 31536000;

function formatPercent(value: number, digits = 2): string {
  return `${value.toFixed(digits)}%`;
}

function rayPerSecondToAprPercent(rayPerSec: number): number {
  // APR% = (ray_per_sec * seconds_per_year / RAY) * 100
  return ((rayPerSec * SECONDS_PER_YEAR) / RAY_NUM) * 100;
}

function rayToPercent(ray: number): number {
  // % = (ray / RAY) * 100
  return (ray / RAY_NUM) * 100;
}

const AVAILABLE_ASSETS: Record<string, string> = {
  btc_asset_id_placeholder: "BTC",
  usdt_asset_id_placeholder: "USDT",
};

export function DashboardPage() {
  const { data, isLoading, error, refetch } = useQuery<Reserve[]>({
    queryKey: ["reserves"],
    queryFn: getReserves,
    refetchInterval: 15000,
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-white">Reserves Dashboard</h1>
        <button
          onClick={() => refetch()}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md text-sm"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-900 border border-red-700 rounded-md">
          <p className="text-red-200">
            Error loading reserves: {(error as any).message}
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="p-6 bg-gray-800 rounded-lg text-gray-300">
          Loading reserves...
        </div>
      ) : data && data.length > 0 ? (
        <div className="overflow-x-auto bg-gray-800 rounded-lg border border-gray-700">
          <table className="min-w-full">
            <thead className="bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Asset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Total Liquidity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Total Borrowed
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Utilization
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Supply APR
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Borrow APR
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Reserve Factor
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {data.map((r) => {
                const assetName =
                  AVAILABLE_ASSETS[r.asset_id] || r.asset_id.slice(0, 8);
                const utilPct = rayToPercent(r.utilization);
                const supplyApr = rayPerSecondToAprPercent(
                  r.current_liquidity_rate,
                );
                const borrowApr = rayPerSecondToAprPercent(
                  r.current_variable_borrow_rate,
                );
                const rfPct = rayToPercent(r.reserve_factor);
                return (
                  <tr key={r.asset_id} className="hover:bg-gray-750">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-semibold">
                      {assetName}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {(r.total_liquidity / 1e8).toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {(r.total_borrowed / 1e8).toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${utilPct > 80 ? "bg-red-900 text-red-200" : utilPct > 50 ? "bg-yellow-900 text-yellow-200" : "bg-green-900 text-green-200"}`}
                      >
                        {formatPercent(utilPct)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatPercent(supplyApr)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatPercent(borrowApr)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatPercent(rfPct)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-6 bg-gray-800 rounded-lg text-gray-300">
          No reserves found.
        </div>
      )}

      <div className="mt-6 p-4 bg-gray-800 rounded border border-gray-700 text-xs text-gray-400">
        <p className="mb-1">Notes</p>
        <ul className="list-disc ml-5 space-y-1">
          <li>Rates are shown as APR, derived from per-second RAY rates.</li>
          <li>Utilization is totalBorrowed / totalLiquidity.</li>
          <li>Values are simulated for MVP.</li>
        </ul>
      </div>
    </div>
  );
}
