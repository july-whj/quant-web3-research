"""In-process registry for versioned strategy implementations."""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel

from .base import Strategy


class StrategyNotFoundError(ValueError):
    pass


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[tuple[str, str], Strategy] = {}
        self._versions: dict[str, list[str]] = defaultdict(list)

    def register(self, strategy: Strategy) -> Strategy:
        identity = (strategy.spec.key, strategy.spec.version)
        if identity in self._strategies:
            raise ValueError(f"strategy already registered: {identity[0]}@{identity[1]}")
        self._strategies[identity] = strategy
        self._versions[strategy.spec.key].append(strategy.spec.version)
        return strategy

    def get(self, key: str, version: str | None = None) -> Strategy:
        versions = self._versions.get(key)
        if not versions:
            raise StrategyNotFoundError(f"unknown strategy: {key}")
        resolved_version = version or versions[-1]
        try:
            return self._strategies[(key, resolved_version)]
        except KeyError as exc:
            raise StrategyNotFoundError(
                f"unknown strategy version: {key}@{resolved_version}"
            ) from exc

    def list(self) -> list[Strategy]:
        return sorted(
            self._strategies.values(),
            key=lambda strategy: (strategy.spec.key, strategy.spec.version),
        )

    def validate_parameters(
        self,
        key: str,
        values: dict[str, object],
        version: str | None = None,
    ) -> tuple[Strategy, BaseModel]:
        strategy = self.get(key, version)
        return strategy, strategy.spec.validate_parameters(values)


strategy_registry = StrategyRegistry()
