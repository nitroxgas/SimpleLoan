/**
 * API Client for Fantasma Protocol
 */

import axios, { AxiosInstance } from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    let message = error.message;

    if (error.response?.data) {
      // FastAPI validation error format
      if (error.response.data.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Pydantic validation errors
          message = error.response.data.detail
            .map((err: any) => `${err.loc.join(".")}: ${err.msg}`)
            .join(", ");
        } else if (typeof error.response.data.detail === "string") {
          message = error.response.data.detail;
        }
      } else if (error.response.data.error?.message) {
        message = error.response.data.error.message;
      }
    }

    console.error("API Error:", message, error.response?.data);
    return Promise.reject(new Error(message));
  },
);

// Types
export interface SupplyRequest {
  user_address: string;
  asset_id: string;
  amount: number;
  signature?: string;
}

export interface SupplyResponse {
  position_id: number;
  user_address: string;
  asset_id: string;
  amount_supplied: number;
  atoken_amount: number;
  liquidity_index: number;
  tx_id: string | null;
}

export interface WithdrawRequest {
  user_address: string;
  asset_id: string;
  amount: number; // 0 = withdraw all
}

export interface WithdrawResponse {
  user_address: string;
  asset_id: string;
  amount_withdrawn: number;
  atoken_burned: number;
  liquidity_index: number;
  tx_id: string | null;
}

export interface Position {
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

export interface BorrowRequest {
  user_address: string;
  collateral_asset_id: string;
  collateral_amount: number;
  borrow_asset_id: string;
  borrow_amount: number;
}

export interface BorrowResponse {
  position_id: number;
  user_address: string;
  collateral_asset_id: string;
  collateral_amount: number;
  borrowed_asset_id: string;
  borrowed_amount: number;
  health_factor: number;
  tx_id: string | null;
}

export interface RepayRequest {
  user_address: string;
  position_id: number;
  repay_amount: number;
}

export interface DebtPosition {
  position_id: number;
  user_address: string;
  borrowed_asset_id: string;
  collateral_asset_id: string;
  principal: number;
  current_debt: number;
  accrued_interest: number;
  collateral_amount: number;
  health_factor: number;
  created_at: string;
}

/**
 * Supply assets to lending pool
 */
export async function supplyAssets(
  request: SupplyRequest,
): Promise<SupplyResponse> {
  const response = await apiClient.post<SupplyResponse>("/supply", request);
  return response.data;
}

/**
 * Withdraw supplied assets from lending pool
 */
export async function withdrawAssets(
  request: WithdrawRequest,
): Promise<WithdrawResponse> {
  const response = await apiClient.post<WithdrawResponse>("/withdraw", request);
  return response.data;
}

/**
 * Get user positions
 */
export async function getPositions(userAddress: string): Promise<Position[]> {
  const response = await apiClient.get<Position[]>(`/positions/${userAddress}`);
  return response.data;
}

/**
 * Get API health
 */
export async function getHealth(): Promise<{ status: string }> {
  const response = await apiClient.get("/health");
  return response.data;
}

/**
 * Borrow assets against collateral
 */
export async function borrowAssets(
  request: BorrowRequest,
): Promise<BorrowResponse> {
  const response = await apiClient.post<BorrowResponse>("/borrow", request);
  return response.data;
}

/**
 * Repay borrowed assets
 */
export async function repayDebt(request: RepayRequest): Promise<void> {
  await apiClient.post("/repay", request);
}

/**
 * Get user debt positions
 */
export async function getDebtPositions(
  userAddress: string,
): Promise<DebtPosition[]> {
  // TODO: Add dedicated endpoint for debt positions
  // For now, would need to be included in positions endpoint or separate
  const response = await apiClient.get<DebtPosition[]>(
    `/positions/${userAddress}/debt`,
  );
  return response.data;
}

export interface LiquidateRequest {
  liquidator_address: string;
  position_id: number;
  repay_amount?: number;
}

export interface LiquidationResponse {
  position_id: number;
  liquidator_address: string;
  repaid_amount: number;
  collateral_seized: number;
  health_factor_after: number;
  tx_id: string | null;
}

export interface LiquidatablePosition {
  position_id: number;
  user_address: string;
  borrowed_asset_id: string;
  collateral_asset_id: string;
  current_debt: number;
  collateral_amount: number;
  health_factor: number;
}

/**
 * Get liquidatable positions
 */
export async function getLiquidatablePositions(): Promise<
  LiquidatablePosition[]
> {
  const response = await apiClient.get<LiquidatablePosition[]>(
    "/positions/liquidatable",
  );
  return response.data;
}

/**
 * Liquidate an unhealthy position
 */
export async function liquidatePosition(
  request: LiquidateRequest,
): Promise<LiquidationResponse> {
  const response = await apiClient.post<LiquidationResponse>(
    "/liquidate",
    request,
  );
  return response.data;
}

export interface Reserve {
  asset_id: string;
  utxo_id: string;
  total_liquidity: number;
  total_borrowed: number;
  liquidity_index: number;
  variable_borrow_index: number;
  current_liquidity_rate: number; // per second, RAY
  current_variable_borrow_rate: number; // per second, RAY
  last_update_timestamp: number;
  reserve_factor: number; // RAY
  utilization: number; // RAY
}

export async function getReserves(): Promise<Reserve[]> {
  const response = await apiClient.get<Reserve[]>("/reserves");
  return response.data;
}

export async function getReserve(assetId: string): Promise<Reserve> {
  const response = await apiClient.get<Reserve>(`/reserves/${assetId}`);
  return response.data;
}

export default apiClient;
