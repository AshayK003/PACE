from abc import ABC, abstractmethod
from typing import Any


class BaseIngestor(ABC):
    @abstractmethod
    def ingest(self, source: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def validate(self, source: str) -> bool:
        pass
