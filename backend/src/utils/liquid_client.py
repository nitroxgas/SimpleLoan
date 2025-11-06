"""
Elements/Liquid Network RPC Client Wrapper

Provides interface to Elements Core node for UTXO operations.
"""

from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from ..config import settings


class LiquidClient:
    """
    Wrapper for Elements Core RPC calls.
    
    Handles communication with Elements daemon for:
    - UTXO fetching and validation
    - Transaction construction and broadcast
    - Asset queries
    - Block and mempool monitoring
    """
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        rpc_user: Optional[str] = None,
        rpc_password: Optional[str] = None,
    ):
        """
        Initialize Liquid RPC client.
        
        Args:
            rpc_url: Elements RPC URL (default from settings)
            rpc_user: RPC username (default from settings)
            rpc_password: RPC password (default from settings)
        """
        self.rpc_url = rpc_url or settings.ELEMENTS_RPC_URL
        self.rpc_user = rpc_user or settings.ELEMENTS_RPC_USER
        self.rpc_password = rpc_password or settings.ELEMENTS_RPC_PASSWORD
        
        self.auth = (self.rpc_user, self.rpc_password)
        self.headers = {"content-type": "application/json"}
    
    async def _call(self, method: str, params: List[Any] = []) -> Any:
        """
        Make RPC call to Elements node.
        
        Args:
            method: RPC method name
            params: Method parameters
        
        Returns:
            RPC response result
        
        Raises:
            httpx.HTTPError: If RPC call fails
        """
        payload = {
            "jsonrpc": "2.0",
            "id": "fantasma",
            "method": method,
            "params": params,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.rpc_url,
                    json=payload,
                    auth=self.auth,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                
                if "error" in data and data["error"] is not None:
                    error = data["error"]
                    logger.error(f"RPC error: {error}")
                    raise Exception(f"RPC error: {error['message']}")
                
                return data.get("result")
            
            except httpx.HTTPError as e:
                logger.error(f"HTTP error calling {method}: {e}")
                raise
    
    async def get_blockchain_info(self) -> Dict[str, Any]:
        """Get blockchain information."""
        return await self._call("getblockchaininfo")
    
    async def get_utxo(self, txid: str, vout: int) -> Optional[Dict[str, Any]]:
        """
        Get UTXO details.
        
        Args:
            txid: Transaction ID
            vout: Output index
        
        Returns:
            UTXO data or None if spent/not found
        """
        result = await self._call("gettxout", [txid, vout, True])
        return result
    
    async def get_raw_transaction(
        self,
        txid: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Get raw transaction.
        
        Args:
            txid: Transaction ID
            verbose: Return decoded transaction (True) or hex (False)
        
        Returns:
            Transaction data
        """
        return await self._call("getrawtransaction", [txid, verbose])
    
    async def list_unspent(
        self,
        min_conf: int = 1,
        max_conf: int = 9999999,
        addresses: Optional[List[str]] = None,
        asset: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List unspent UTXOs.
        
        Args:
            min_conf: Minimum confirmations
            max_conf: Maximum confirmations
            addresses: Filter by addresses
            asset: Filter by asset ID
        
        Returns:
            List of UTXOs
        """
        params = [min_conf, max_conf]
        if addresses:
            params.append(addresses)
        
        utxos = await self._call("listunspent", params)
        
        # Filter by asset if specified
        if asset:
            utxos = [u for u in utxos if u.get("asset") == asset]
        
        return utxos
    
    async def create_raw_transaction(
        self,
        inputs: List[Dict[str, Any]],
        outputs: Dict[str, Any],
    ) -> str:
        """
        Create raw transaction.
        
        Args:
            inputs: List of inputs [{"txid": "...", "vout": 0}, ...]
            outputs: Output map {address: amount, ...}
        
        Returns:
            Raw transaction hex
        """
        return await self._call("createrawtransaction", [inputs, outputs])
    
    async def sign_raw_transaction_with_wallet(
        self,
        hex_string: str
    ) -> Dict[str, Any]:
        """
        Sign raw transaction with wallet.
        
        Args:
            hex_string: Raw transaction hex
        
        Returns:
            Signed transaction data
        """
        return await self._call("signrawtransactionwithwallet", [hex_string])
    
    async def send_raw_transaction(self, hex_string: str) -> str:
        """
        Broadcast raw transaction.
        
        Args:
            hex_string: Signed transaction hex
        
        Returns:
            Transaction ID
        """
        return await self._call("sendrawtransaction", [hex_string])
    
    async def get_new_address(self, label: str = "") -> str:
        """
        Generate new address.
        
        Args:
            label: Address label
        
        Returns:
            New Liquid address
        """
        return await self._call("getnewaddress", [label])
    
    async def get_balance(self, asset: Optional[str] = None) -> Dict[str, float]:
        """
        Get wallet balance.
        
        Args:
            asset: Specific asset ID (None for all)
        
        Returns:
            Balance map {asset_id: amount}
        """
        if asset:
            balance = await self._call("getbalance", ["*", 1, False, asset])
            return {asset: balance}
        else:
            return await self._call("getbalance")
    
    async def issue_asset(
        self,
        amount: float,
        reissuance_tokens: float = 0,
        blind: bool = False,
    ) -> Dict[str, Any]:
        """
        Issue new asset (testnet only).
        
        Args:
            amount: Amount to issue
            reissuance_tokens: Reissuance token amount
            blind: Use confidential issuance
        
        Returns:
            Issuance data with asset ID
        """
        return await self._call("issueasset", [amount, reissuance_tokens, blind])
    
    async def generate_blocks(self, num_blocks: int) -> List[str]:
        """
        Generate blocks (regtest only).
        
        Args:
            num_blocks: Number of blocks to generate
        
        Returns:
            List of block hashes
        """
        address = await self.get_new_address()
        return await self._call("generatetoaddress", [num_blocks, address])
    
    async def decode_raw_transaction(self, hex_string: str) -> Dict[str, Any]:
        """
        Decode raw transaction.
        
        Args:
            hex_string: Transaction hex
        
        Returns:
            Decoded transaction
        """
        return await self._call("decoderawtransaction", [hex_string])
    
    async def get_asset_info(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get asset information.
        
        Args:
            asset_id: Asset ID
        
        Returns:
            Asset info or None
        """
        try:
            return await self._call("getassetinfo", [asset_id])
        except Exception:
            return None


# Global client instance
liquid_client = LiquidClient()
