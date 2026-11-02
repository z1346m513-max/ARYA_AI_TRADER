"""قرارداد Provider داده سهامداران — جدا از MarketDataProvider."""
from __future__ import annotations

from abc import ABC, abstractmethod

from arya.models.shareholders import ShareholderFlowMetrics


class ShareholderDataProvider(ABC):
    name: str = "shareholder_base"

    @abstractmethod
    def fetch_shareholder_flow(self, ticker: str, days: int = 5) -> ShareholderFlowMetrics:
        raise NotImplementedError


class ShareholderProviderRegistry:
    _registry: dict[str, type[ShareholderDataProvider]] = {}

    @classmethod
    def register(cls, driver_name: str):
        def _wrap(provider_cls: type[ShareholderDataProvider]):
            cls._registry[driver_name] = provider_cls
            return provider_cls

        return _wrap

    @classmethod
    def create(cls, driver_name: str, **kwargs) -> ShareholderDataProvider:
        if driver_name not in cls._registry:
            raise ValueError(
                f"درایور سهامداران ناشناخته: '{driver_name}'. "
                f"موجود: {list(cls._registry)}"
            )
        return cls._registry[driver_name](**kwargs)
