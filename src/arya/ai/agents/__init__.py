"""Optional external multi-agent research integrations for ARYA."""
from arya.ai.agents.tradingagents_adapter import (
    TradingAgentsAdapter,
    TradingAgentsDependencyError,
    TradingAgentsIntegrationError,
    TradingAgentsOptions,
    TradingAgentsResearchResult,
)

__all__ = [
    "TradingAgentsAdapter",
    "TradingAgentsDependencyError",
    "TradingAgentsIntegrationError",
    "TradingAgentsOptions",
    "TradingAgentsResearchResult",
]
