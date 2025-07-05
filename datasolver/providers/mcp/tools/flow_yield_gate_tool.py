import asyncio
from typing import Dict, Any, List

from .tool import MCPTool
from datasolver.providers.flow.flow_evm import FlowEVMProvider

class FlowYieldGateTool(MCPTool):
    """
    MCP Tool for checking NFT-gated yield opportunities on Flow EVM.
    """
    @property
    def name(self) -> str:
        return "flow_yield_gate"

    @property
    def description(self) -> str:
        return "Get Flow EVM gated yield opportunities based on NFT holdings and reputation."

    @property
    def capabilities(self) -> Dict[str, Any]:
        return {
            "service": self.name,
            "version": "0.1.0",
            "inputs": ["user_address", "nft_collections"],
            "outputs": ["user_address", "nft_score", "reputation", "available_yields", "premium_access"],
        }

    def validate_rfd(self, rfd: Dict[str, Any]) -> bool:
        """
        Validate if this tool can handle the RFD.
        It must have the correct service name and required parameters.
        """
        return (
            rfd.get("service") == self.name and
            "user_address" in rfd and
            "nft_collections" in rfd
        )

    def cost(self, rfd: Dict[str, Any]) -> float:
        """
        Return a base cost for using this tool.
        Can be made more complex later (e.g., based on number of collections).
        """
        return 5.0  # Arbitrary cost

    async def _get_gated_yields_async(self, rfd: Dict[str, Any]) -> Dict[str, Any]:
        """
        The core asynchronous logic for the tool.
        """
        user_address = rfd["user_address"]
        nft_collections = rfd["nft_collections"]
        reputation_threshold = rfd.get("reputation_threshold", 1000)

        flow_provider = FlowEVMProvider()

        # 1. Check NFT holdings
        nft_score = await flow_provider.check_nft_holdings(user_address, nft_collections)
        
        # 2. Calculate reputation
        reputation = await flow_provider.calculate_reputation(user_address)
        
        # 3. Get available yields
        yields = await flow_provider.get_gated_yields(user_address, nft_score, reputation)
        
        return {
            "user_address": user_address,
            "nft_score": nft_score,
            "reputation": reputation,
            "available_yields": yields,
            "premium_access": reputation > reputation_threshold or nft_score > 100
        }

    def generate_data(self, rfd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper required by the MCPTool interface.
        It runs the asynchronous core logic.
        """
        return asyncio.run(self._get_gated_yields_async(rfd))
    
    def generate(self, rfd: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        The standard entry point called by some routers.
        """
        if not self.validate_rfd(rfd):
            raise ValueError("Invalid RFD for flow_yield_gate tool.")
        
        # The result of generate_data is already a dictionary, not a list of records,
        # so we return it directly.
        return self.generate_data(rfd)

