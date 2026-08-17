from __future__ import annotations

from .models import DataAssetRecord


class DataAssetRegistry:
    def __init__(self) -> None:
        self._assets: dict[tuple[str, str], DataAssetRecord] = {}

    def register(self, asset: DataAssetRecord) -> None:
        key = (asset.institution_id, asset.asset_id)
        if key in self._assets:
            raise ValueError("data asset id already registered for institution")
        self._assets[key] = asset

    def get(self, institution_id: str, asset_id: str) -> DataAssetRecord | None:
        return self._assets.get((institution_id, asset_id))

    def list_for_institution(self, institution_id: str) -> tuple[DataAssetRecord, ...]:
        return tuple(sorted((asset for (tenant, _), asset in self._assets.items() if tenant == institution_id), key=lambda item: item.asset_id))
