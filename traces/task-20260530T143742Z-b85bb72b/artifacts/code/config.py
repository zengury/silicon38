"""
Configuration port — abstract interface for reading application configuration.

All infrastructure config adapters (env-based, dict-based, file-based) must
implement this ABC so that domain services never depend on os.environ directly.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ConfigPort(ABC):
    """Abstract configuration reader.

    Implementations read from environment variables, config files, secrets
    managers, or in-memory dicts (for testing).
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Read a single config value with an optional default."""
        ...

    @abstractmethod
    def get_required(self, key: str) -> str:
        """Read a required config value.  Must raise ConfigurationError if missing."""
        ...

    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """Read a config value as int."""
        ...

    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Read a config value as bool."""
        ...

    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Read a config value as float."""
        ...

    @abstractmethod
    def all(self) -> Dict[str, Any]:
        """Return all configuration as a raw dictionary."""
        ...
