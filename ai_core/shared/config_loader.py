"""
YAML configuration loader.

Reads all config files from configs/ directory
and provides type-safe access to configuration values.
This centralizes all tunable parameters outside of code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml


class ConfigLoader:
    """
    Centralized YAML configuration loader.

    Loads all config files from configs/ directory once at startup.
    Provides type-safe access to configuration values.
    """

    _instance: Optional[ConfigLoader] = None
    _config: dict[str, Any] = {}

    def __new__(cls) -> ConfigLoader:
        """Singleton pattern: only one ConfigLoader instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_configs()
        return cls._instance

    def _load_configs(self) -> None:
        """
        Load all YAML files from configs/ directory.

        Raises:
            FileNotFoundError: If configs directory not found.
            yaml.YAMLError: If any YAML file is invalid.
        """
        configs_dir = Path(__file__).parent.parent.parent / "configs"

        if not configs_dir.exists():
            raise FileNotFoundError(f"Configs directory not found: {configs_dir}")

        self._config = {}

        for yaml_file in sorted(configs_dir.glob("*.yaml")):
            config_name = yaml_file.stem
            try:
                with open(yaml_file, "r") as f:
                    config_data = yaml.safe_load(f)
                    if config_data is not None:
                        self._config[config_name] = config_data
                        print(f"Loaded config: {config_name}")
            except yaml.YAMLError as e:
                raise yaml.YAMLError(
                    f"Failed to parse {yaml_file}: {e}"
                ) from e

    def get(
        self,
        config_name: str,
        key: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Get a configuration value.

        Args:
            config_name: Name of config file (without .yaml)
                        e.g. "app_config" for app_config.yaml
            key: Dot-separated nested key e.g. "app.name"
                If None, returns entire config.
            default: Default value if key not found.

        Returns:
            Configuration value or default if not found.

        Example:
            loader = ConfigLoader()
            app_name = loader.get("app_config", "app.name")
            interview_timeout = loader.get("app_config", "interview.timeout", 300)
        """
        if config_name not in self._config:
            return default

        config = self._config[config_name]

        if key is None:
            return config

        # Handle dot-separated nested keys
        keys = key.split(".")
        current = config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def get_int(
        self,
        config_name: str,
        key: str,
        default: int = 0,
    ) -> int:
        """Get an integer config value."""
        value = self.get(config_name, key, default)
        return int(value) if value is not None else default

    def get_float(
        self,
        config_name: str,
        key: str,
        default: float = 0.0,
    ) -> float:
        """Get a float config value."""
        value = self.get(config_name, key, default)
        return float(value) if value is not None else default

    def get_bool(
        self,
        config_name: str,
        key: str,
        default: bool = False,
    ) -> bool:
        """Get a boolean config value."""
        value = self.get(config_name, key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        return default

    def get_str(
        self,
        config_name: str,
        key: str,
        default: str = "",
    ) -> str:
        """Get a string config value."""
        value = self.get(config_name, key, default)
        return str(value) if value is not None else default

    def get_list(
        self,
        config_name: str,
        key: str,
        default: Optional[list[Any]] = None,
    ) -> list[Any]:
        """Get a list config value."""
        if default is None:
            default = []
        value = self.get(config_name, key, default)
        return value if isinstance(value, list) else default

    def reload(self) -> None:
        """Reload all configs from disk. For testing only."""
        self._config = {}
        self._load_configs()


# Global singleton instance
config = ConfigLoader()
