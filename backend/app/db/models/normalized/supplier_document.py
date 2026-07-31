"""
SupplierDocument — alias to SupplierDocumentRecord to prevent duplicate __tablename__ mapping.
"""
from __future__ import annotations

from app.supplier_portal.models.document_center import SupplierDocumentRecord as SupplierDocument

DOC_TYPE_VALUES = (
    "CONTRACT", "LICENSE", "INSURANCE", "FINANCIAL",
    "AUDIT_REPORT", "COMPLIANCE", "CERTIFICATION", "OTHER",
)

__all__ = ["SupplierDocument", "DOC_TYPE_VALUES"]

