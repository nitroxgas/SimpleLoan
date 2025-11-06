/**
 * HealthFactor Component
 *
 * Visual gauge showing user's health factor.
 * Healthy: >= 1.5 (green)
 * Warning: 1.0-1.5 (yellow)
 * Danger: < 1.0 (red, liquidatable)
 */

interface HealthFactorProps {
  value: number; // Health factor in RAY precision (10^27)
  showDetails?: boolean;
}

const RAY = BigInt("1000000000000000000000000000"); // 10^27

export function HealthFactor({
  value,
  showDetails = false,
}: HealthFactorProps) {
  // Convert from RAY to decimal
  const healthFactor = value / Number(RAY);

  const getStatus = () => {
    if (healthFactor >= 1.5)
      return { label: "Healthy", color: "green", bgColor: "bg-green-500" };
    if (healthFactor >= 1.0)
      return { label: "Warning", color: "yellow", bgColor: "bg-yellow-500" };
    return { label: "Liquidatable", color: "red", bgColor: "bg-red-500" };
  };

  const status = getStatus();

  // Calculate percentage for visual display (0-200% range, cap at 100% display)
  const percentage = Math.min((healthFactor / 2) * 100, 100);

  return (
    <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-medium text-gray-300">Health Factor</h3>
        <span className={`text-2xl font-bold text-${status.color}-400`}>
          {healthFactor.toFixed(2)}
        </span>
      </div>

      {/* Visual gauge */}
      <div className="relative w-full h-4 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${status.bgColor} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />

        {/* Liquidation threshold marker */}
        <div
          className="absolute top-0 h-full w-0.5 bg-white"
          style={{ left: "50%" }}
          title="Liquidation threshold (1.0)"
        />
      </div>

      {/* Status label */}
      <div className="flex justify-between items-center mt-2">
        <span className={`text-xs font-semibold text-${status.color}-400`}>
          {status.label}
        </span>
        <span className="text-xs text-gray-500">Threshold: 1.0</span>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-700 space-y-2 text-xs">
          <div className="flex justify-between text-gray-400">
            <span>Status:</span>
            <span className={`font-medium text-${status.color}-400`}>
              {healthFactor >= 1.0 ? "✓ Healthy" : "⚠ At Risk"}
            </span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Liquidation Risk:</span>
            <span className={`font-medium text-${status.color}-400`}>
              {healthFactor >= 1.5
                ? "Low"
                : healthFactor >= 1.0
                  ? "Medium"
                  : "High"}
            </span>
          </div>
          {healthFactor < 1.0 && (
            <div className="mt-2 p-2 bg-red-900 rounded text-red-200 text-xs">
              ⚠ Your position may be liquidated. Add collateral or repay debt
              to improve health factor.
            </div>
          )}
          {healthFactor >= 1.0 && healthFactor < 1.2 && (
            <div className="mt-2 p-2 bg-yellow-900 rounded text-yellow-200 text-xs">
              ⚠ Health factor is low. Consider adding collateral to reduce
              liquidation risk.
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      {!showDetails && (
        <div className="mt-3 flex justify-between text-xs text-gray-500">
          <span>0.0</span>
          <span>1.0</span>
          <span>2.0+</span>
        </div>
      )}
    </div>
  );
}
