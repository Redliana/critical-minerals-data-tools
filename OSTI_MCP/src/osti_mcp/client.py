"""OSTI client backed by cmm_data shared clients."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from cmm_data.clients import OSTIClient as CoreOSTIClient


class OSTIDocument(BaseModel):
    """OSTI document metadata."""

    osti_id: str
    title: str
    authors: list[str] = []
    publication_date: Optional[str] = None
    description: Optional[str] = None
    subjects: list[str] = []
    commodity_category: Optional[str] = None
    doi: Optional[str] = None
    product_type: Optional[str] = None
    research_orgs: list[str] = []
    sponsor_orgs: list[str] = []


class OSTIClient:
    """Compatibility wrapper for OSTI operations used by MCP server."""

    COMMODITIES = CoreOSTIClient.COMMODITIES

    @staticmethod
    def _has_valid_catalog(path: Path) -> bool:
        catalog = path / "document_catalog.json"
        if not catalog.exists():
            return False
        try:
            with catalog.open(encoding="utf-8") as handle:
                json.load(handle)
            return True
        except (OSError, ValueError, TypeError):
            return False

    @classmethod
    def _resolve_default_data_path(cls) -> Path:
        workspace_root = Path(__file__).resolve().parents[5]
        candidates = [
            workspace_root / "Globus_Sharing" / "OSTI_retrieval",
            workspace_root / "Globus_Sharing" / "OSTI_retrieval_2",
            workspace_root / "Corpus" / "OSTI" / "OSTI_retrieval_2",
            workspace_root / "Corpus" / "OSTI" / "OSTI_retrieval_1",
            workspace_root / "LLM_Fine_Tuning" / "OSTI_retrieval_1",
        ]
        for candidate in candidates:
            if cls._has_valid_catalog(candidate):
                return candidate
        # Fallback preserves previous behavior and surfaces a clear error downstream.
        return workspace_root / "Globus_Sharing" / "OSTI_retrieval"

    def __init__(self, data_path: Optional[str] = None):
        if data_path:
            resolved = Path(data_path)
        else:
            env_path = os.environ.get("OSTI_DATA_PATH")
            if env_path:
                resolved = Path(env_path)
            else:
                resolved = self._resolve_default_data_path()
        self._core = CoreOSTIClient(data_path=resolved)

    @staticmethod
    def _to_document(doc) -> OSTIDocument:
        return OSTIDocument(
            osti_id=doc.osti_id,
            title=doc.title,
            authors=doc.authors,
            publication_date=doc.publication_date,
            description=doc.description,
            subjects=doc.subjects,
            commodity_category=doc.commodity_category,
            doi=doc.doi,
            product_type=doc.product_type,
            research_orgs=doc.research_orgs,
            sponsor_orgs=doc.sponsor_orgs,
        )

    def get_statistics(self) -> dict:
        return self._core.get_statistics()

    def search_documents(
        self,
        query: Optional[str] = None,
        commodity: Optional[str] = None,
        product_type: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 50,
    ) -> list[OSTIDocument]:
        docs = self._core.search_documents(
            query=query,
            commodity=commodity,
            product_type=product_type,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
        )
        return [self._to_document(doc) for doc in docs]

    def get_document(self, osti_id: str) -> Optional[OSTIDocument]:
        doc = self._core.get_document(osti_id)
        return self._to_document(doc) if doc else None

    def list_commodities(self) -> dict[str, str]:
        return self._core.list_commodities()

    def get_documents_by_commodity(self, commodity: str, limit: int = 100) -> list[OSTIDocument]:
        docs = self._core.get_documents_by_commodity(commodity=commodity, limit=limit)
        return [self._to_document(doc) for doc in docs]

    def get_recent_documents(self, limit: int = 20) -> list[OSTIDocument]:
        docs = self._core.get_recent_documents(limit=limit)
        return [self._to_document(doc) for doc in docs]
