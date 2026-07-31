"""
module_c_services.py — Setup Status, Quality Management, Document Center services.
These follow the identical pattern as services.py (repo + audit log + orchestrator bridge).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ValidationException
from app.supplier_portal.models.setup_status import SupplierSetupStatus
from app.supplier_portal.models.quality_record import SupplierQualityRecord, SupplierQualityHistory
from app.supplier_portal.models.document_center import SupplierDocumentRecord, SupplierDocumentAudit
from app.supplier_portal.models.company_profile import SupplierCompanyProfile
from app.supplier_portal.models.production_capacity import SupplierProductionCapacity
from app.supplier_portal.models.lead_time import SupplierLeadTime
from app.supplier_portal.repositories.repos import AuditLogRepo, CompanyProfileRepo
from app.supplier_portal.services.orchestrator_bridge import orchestrator_bridge
from app.orchestrator.events import EventType

logger = logging.getLogger("supplier_portal.module_c_services")


# ══════════════════════════════════════════════════════════════════════════════
# SETUP STATUS SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class SetupStatusService:
    """Manages the supplier wizard completion state."""

    def __init__(self, db: Session):
        self.db    = db
        self.audit = AuditLogRepo(db)

    def _get_or_create(self, supplier_id: str) -> SupplierSetupStatus:
        row = self.db.query(SupplierSetupStatus).filter(
            SupplierSetupStatus.supplier_id == supplier_id
        ).first()
        if not row:
            row = SupplierSetupStatus(
                id=str(uuid.uuid4()), supplier_id=supplier_id,
                wizard_started_at=datetime.now(timezone.utc)
            )
            self.db.add(row)
            self.db.flush()
        return row

    def _infer_steps(self, supplier_id: str, row: SupplierSetupStatus) -> None:
        """Auto-infer step completion from existing DB data."""
        profile_repo = CompanyProfileRepo(self.db)
        profile = profile_repo.get_by_supplier_id(supplier_id)
        if profile:
            if profile.company_name and profile.description:
                row.step_company_profile = True
            if profile.contacts and len(profile.contacts) > 0:
                row.step_contacts = True
            if profile.locations and len(profile.locations) > 0:
                row.step_locations = True
            if profile.products and len(profile.products) > 0:
                row.step_products = True
            if profile.certifications and len(profile.certifications) > 0:
                row.step_certifications = True
            if profile.logo_url:
                row.step_media = True

        prod = self.db.query(SupplierProductionCapacity).filter(
            SupplierProductionCapacity.supplier_id == supplier_id
        ).first()
        if prod:
            row.step_production = True

        lt = self.db.query(SupplierLeadTime).filter(
            SupplierLeadTime.supplier_id == supplier_id
        ).first()
        if lt:
            row.step_lead_times = True

    def get_status(self, supplier_id: str) -> dict:
        row = self._get_or_create(supplier_id)
        self._infer_steps(supplier_id, row)
        row.recalculate()
        self.db.commit()
        self.db.refresh(row)
        return self._to_dict(supplier_id, row)

    def _to_dict(self, supplier_id: str, row: SupplierSetupStatus) -> dict:
        steps = {
            "company_profile": row.step_company_profile,
            "contacts":        row.step_contacts,
            "locations":       row.step_locations,
            "products":        row.step_products,
            "production":      row.step_production,
            "lead_times":      row.step_lead_times,
            "certifications":  row.step_certifications,
            "media":           row.step_media,
        }
        return {
            "supplier_id":         supplier_id,
            "is_complete":         row.is_complete,
            "completion_pct":      row.completion_pct,
            "wizard_started_at":   row.wizard_started_at.isoformat() if row.wizard_started_at else None,
            "wizard_completed_at": row.wizard_completed_at.isoformat() if row.wizard_completed_at else None,
            "steps":               steps,
            "missing_steps":       [k for k, v in steps.items() if not v],
        }

    def mark_step(self, supplier_id: str, step: str) -> dict:
        mapped = f"step_{step}" if not step.startswith("step_") else step
        if mapped not in SupplierSetupStatus.STEPS:
            raise ValidationException(f"Unknown step: {step}")
        row = self._get_or_create(supplier_id)
        setattr(row, mapped, True)
        row.recalculate()
        self.db.commit()
        return self.get_status(supplier_id)

    def mark_complete(self, supplier_id: str) -> dict:
        row = self._get_or_create(supplier_id)
        for step in SupplierSetupStatus.STEPS:
            setattr(row, step, True)
        row.recalculate()
        self.db.commit()
        self.audit.log(supplier_id=supplier_id, user_id=supplier_id,
                       action="SETUP_WIZARD_COMPLETED",
                       entity="supplier_setup_status",
                       entity_id=str(row.id))
        return self.get_status(supplier_id)


# ══════════════════════════════════════════════════════════════════════════════
# QUALITY MANAGEMENT SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class QualityService:
    def __init__(self, db: Session):
        self.db    = db
        self.audit = AuditLogRepo(db)

    def _next_record_number(self) -> str:
        try:
            if self.db.bind and self.db.bind.dialect.name == "postgresql":
                from sqlalchemy import text
                result = self.db.execute(text("SELECT public.next_quality_record_number()"))
                val = result.scalar()
                if val:
                    return val
        except Exception:
            pass
        return f"QR-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}"

    def list_records(self, supplier_id: str, record_type: Optional[str] = None,
                     severity: Optional[str] = None, status: Optional[str] = None,
                     search: Optional[str] = None,
                     page: int = 1, page_size: int = 20) -> Tuple[List, int]:
        q = self.db.query(SupplierQualityRecord).filter(
            SupplierQualityRecord.supplier_id == supplier_id,
            SupplierQualityRecord.deleted_at.is_(None),
        )
        if record_type: q = q.filter(SupplierQualityRecord.record_type == record_type)
        if severity:    q = q.filter(SupplierQualityRecord.severity == severity)
        if status:      q = q.filter(SupplierQualityRecord.status == status)
        if search:
            like = f"%{search}%"
            from sqlalchemy import or_
            q = q.filter(or_(
                SupplierQualityRecord.title.ilike(like),
                SupplierQualityRecord.description.ilike(like),
                SupplierQualityRecord.record_number.ilike(like),
            ))
        total = q.count()
        rows  = q.order_by(SupplierQualityRecord.created_at.desc())\
                  .offset((page - 1) * page_size).limit(page_size).all()
        return rows, total

    def get_record(self, supplier_id: str, record_id: str) -> SupplierQualityRecord:
        row = self.db.query(SupplierQualityRecord).filter(
            SupplierQualityRecord.id == record_id,
            SupplierQualityRecord.supplier_id == supplier_id,
            SupplierQualityRecord.deleted_at.is_(None),
        ).first()
        if not row:
            raise NotFoundException(f"Quality record {record_id} not found")
        return row

    def create_record(self, supplier_id: str, user_id: str, data: dict,
                      ip_address: str = None) -> SupplierQualityRecord:
        data["record_number"] = self._next_record_number()
        data["created_by"]    = user_id
        if data.get("quantity_failed") and data.get("quantity_inspected"):
            data["defect_rate_pct"] = round(
                data["quantity_failed"] / data["quantity_inspected"] * 100, 2
            )
        row = SupplierQualityRecord(id=str(uuid.uuid4()), supplier_id=supplier_id, **data)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="QUALITY_RECORD_CREATED", entity="supplier_quality_records",
                       entity_id=str(row.id), new_value=data, ip_address=ip_address)
        orchestrator_bridge.notify_sync(
            EventType.SUPPLIER_PORTAL_INCIDENT_REPORTED.value, supplier_id,
            {"action": "quality_record_created", "record_id": str(row.id),
             "severity": data.get("severity"), "title": data.get("title")}
        )
        return row

    def update_record(self, supplier_id: str, user_id: str, record_id: str,
                      data: dict, ip_address: str = None) -> SupplierQualityRecord:
        row = self.get_record(supplier_id, record_id)
        old_snapshot = {c.name: str(getattr(row, c.name)) for c in row.__table__.columns}
        change_parts = []
        for k, v in data.items():
            old_v = getattr(row, k, None)
            if str(old_v) != str(v):
                change_parts.append(f"{k}: {old_v} → {v}")
            setattr(row, k, v)
        row.version += 1
        if data.get("status") == "CLOSED" and not row.closed_at:
            row.closed_at = datetime.now(timezone.utc)
            row.closed_by = user_id
        self.db.add(SupplierQualityHistory(
            id=uuid.uuid4(), quality_id=row.id, version=row.version - 1,
            changed_by=user_id,
            change_summary="; ".join(change_parts) or "Updated",
            snapshot=old_snapshot,
        ))
        self.db.commit()
        self.db.refresh(row)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="QUALITY_RECORD_UPDATED", entity="supplier_quality_records",
                       entity_id=str(row.id), new_value=data, ip_address=ip_address)
        return row

    def delete_record(self, supplier_id: str, user_id: str, record_id: str,
                      ip_address: str = None) -> None:
        row = self.get_record(supplier_id, record_id)
        row.deleted_at = datetime.now(timezone.utc)
        row.deleted_by = user_id
        self.db.commit()
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="QUALITY_RECORD_DELETED", entity="supplier_quality_records",
                       entity_id=record_id, ip_address=ip_address)

    def get_history(self, supplier_id: str, record_id: str) -> List:
        self.get_record(supplier_id, record_id)
        return self.db.query(SupplierQualityHistory).filter(
            SupplierQualityHistory.quality_id == record_id
        ).order_by(SupplierQualityHistory.changed_at.desc()).all()

    def get_kpis(self, supplier_id: str) -> dict:
        from sqlalchemy import func
        q = self.db.query(SupplierQualityRecord).filter(
            SupplierQualityRecord.supplier_id == supplier_id,
            SupplierQualityRecord.deleted_at.is_(None),
        )
        avg_defect = self.db.query(func.avg(SupplierQualityRecord.defect_rate_pct)).filter(
            SupplierQualityRecord.supplier_id == supplier_id,
            SupplierQualityRecord.deleted_at.is_(None),
            SupplierQualityRecord.defect_rate_pct.isnot(None),
        ).scalar()
        return {
            "total":               q.count(),
            "open":                q.filter(SupplierQualityRecord.status == "OPEN").count(),
            "closed":              q.filter(SupplierQualityRecord.status == "CLOSED").count(),
            "critical":            q.filter(SupplierQualityRecord.severity == "CRITICAL").count(),
            "avg_defect_rate_pct": round(float(avg_defect or 0), 2),
        }


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT CENTER SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class DocumentCenterService:
    BUCKET_DOCS   = "supplier-documents"
    BUCKET_ASSETS = "supplier-assets"

    def __init__(self, db: Session):
        self.db    = db
        self.audit = AuditLogRepo(db)

    def _get_supabase(self):
        from app.db.supabase_client import get_supabase
        sb = get_supabase()
        if not sb:
            raise ValidationException("Supabase Storage not configured")
        return sb

    def _ensure_buckets(self) -> None:
        try:
            sb = self._get_supabase()
            existing = [b.name for b in sb.storage.list_buckets()]
            if self.BUCKET_DOCS not in existing:
                sb.storage.create_bucket(
                    self.BUCKET_DOCS,
                    options={"public": True, "file_size_limit": 52428800}
                )
                logger.info(f"[DocumentCenterService] Created bucket: {self.BUCKET_DOCS}")
            else:
                sb.storage.update_bucket(self.BUCKET_DOCS, options={"public": True})

            if self.BUCKET_ASSETS not in existing:
                sb.storage.create_bucket(
                    self.BUCKET_ASSETS,
                    options={"public": True, "file_size_limit": 10485760}
                )
                logger.info(f"[DocumentCenterService] Created bucket: {self.BUCKET_ASSETS}")
            else:
                sb.storage.update_bucket(self.BUCKET_ASSETS, options={"public": True})
        except Exception as exc:
            logger.warning(f"[DocumentCenterService] bucket init: {exc}")


    def list_documents(self, supplier_id: str, category: Optional[str] = None,
                       status: Optional[str] = None, search: Optional[str] = None,
                       page: int = 1, page_size: int = 20) -> Tuple[List, int]:
        q = self.db.query(SupplierDocumentRecord).filter(
            SupplierDocumentRecord.supplier_id == supplier_id,
            SupplierDocumentRecord.deleted_at.is_(None),
            SupplierDocumentRecord.is_latest == True,
        )
        if category: q = q.filter(SupplierDocumentRecord.category == category)
        if status:   q = q.filter(SupplierDocumentRecord.status == status)
        if search:
            like = f"%{search}%"
            from sqlalchemy import or_
            q = q.filter(or_(
                SupplierDocumentRecord.display_name.ilike(like),
                SupplierDocumentRecord.file_name.ilike(like),
                SupplierDocumentRecord.description.ilike(like),
            ))
        total = q.count()
        rows  = q.order_by(SupplierDocumentRecord.uploaded_at.desc())\
                  .offset((page - 1) * page_size).limit(page_size).all()
        return rows, total

    def get_document(self, supplier_id: str, doc_id: str) -> SupplierDocumentRecord:
        row = self.db.query(SupplierDocumentRecord).filter(
            SupplierDocumentRecord.id == doc_id,
            SupplierDocumentRecord.supplier_id == supplier_id,
            SupplierDocumentRecord.deleted_at.is_(None),
        ).first()
        if not row:
            raise NotFoundException(f"Document {doc_id} not found")
        return row

    async def upload_document(self, supplier_id: str, user_id: str,
                              file_bytes: bytes, file_name: str, content_type: str,
                              category: str = "GENERAL", display_name: str = None,
                              description: str = None, document_date=None,
                              expiry_date=None, issuing_body: str = None,
                              tags: list = None, ip_address: str = None,
                              is_asset: bool = False) -> SupplierDocumentRecord:
        self._ensure_buckets()
        bucket = self.BUCKET_ASSETS if is_asset else self.BUCKET_DOCS
        import time as _time
        ts   = int(_time.time())
        safe = "".join([c if c.isalnum() or c in "._-" else "_" for c in (file_name or "doc").strip()])
        path = f"{supplier_id}/{ts}_{safe}"


        public_url = path
        try:
            sb = self._get_supabase()
            sb.storage.from_(bucket).upload(
                path, file_bytes,
                {"content-type": content_type, "upsert": "false"},
            )
            public_url = sb.storage.from_(bucket).get_public_url(path)
        except Exception as exc:
            logger.warning(f"[DocumentCenterService] upload to storage failed: {exc}")

        row = SupplierDocumentRecord(
            id=uuid.uuid4(), supplier_id=supplier_id,
            file_name=file_name, display_name=display_name or file_name,
            description=description, category=category,
            storage_bucket=bucket, storage_path=path,
            public_url=public_url, content_type=content_type,
            size_bytes=len(file_bytes),
            document_date=document_date, expiry_date=expiry_date,
            issuing_body=issuing_body, tags=tags or [],
            uploaded_by=user_id,
        )
        self.db.add(row)
        self.db.flush()
        self.db.add(SupplierDocumentAudit(
            id=uuid.uuid4(), document_id=row.id, supplier_id=supplier_id,
            action="UPLOAD", actor_id=user_id, ip_address=ip_address,
        ))
        self.db.commit()
        self.db.refresh(row)
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="DOCUMENT_UPLOADED", entity="supplier_documents",
                       entity_id=str(row.id), ip_address=ip_address)
        return row

    def update_document(self, supplier_id: str, user_id: str, doc_id: str,
                        data: dict, ip_address: str = None) -> SupplierDocumentRecord:
        row = self.get_document(supplier_id, doc_id)
        allowed = {"display_name", "description", "category", "tags",
                   "document_date", "expiry_date", "issuing_body", "status"}
        for k, v in data.items():
            if k in allowed:
                setattr(row, k, v)
        self.db.commit()
        self.db.refresh(row)
        self.db.add(SupplierDocumentAudit(
            id=uuid.uuid4(), document_id=row.id, supplier_id=supplier_id,
            action="UPDATE", actor_id=user_id, ip_address=ip_address,
        ))
        self.db.commit()
        return row

    def delete_document(self, supplier_id: str, user_id: str, doc_id: str,
                        ip_address: str = None) -> None:
        row = self.get_document(supplier_id, doc_id)
        try:
            sb = self._get_supabase()
            sb.storage.from_(row.storage_bucket).remove([row.storage_path])
        except Exception as exc:
            logger.warning(f"[DocumentCenterService] storage delete failed: {exc}")
        row.deleted_at = datetime.now(timezone.utc)
        row.deleted_by = user_id
        self.db.add(SupplierDocumentAudit(
            id=uuid.uuid4(), document_id=row.id, supplier_id=supplier_id,
            action="DELETE", actor_id=user_id, ip_address=ip_address,
        ))
        self.db.commit()
        self.audit.log(supplier_id=supplier_id, user_id=user_id,
                       action="DOCUMENT_DELETED", entity="supplier_documents",
                       entity_id=doc_id, ip_address=ip_address)

    def get_versions(self, supplier_id: str, doc_id: str) -> List:
        self.get_document(supplier_id, doc_id)
        return self.db.query(SupplierDocumentRecord).filter(
            SupplierDocumentRecord.supplier_id == supplier_id,
            SupplierDocumentRecord.deleted_at.is_(None),
        ).filter(
            (SupplierDocumentRecord.id == doc_id) |
            (SupplierDocumentRecord.parent_doc_id == doc_id)
        ).order_by(SupplierDocumentRecord.version.desc()).all()

    def get_audit_log(self, supplier_id: str, doc_id: str) -> List:
        self.get_document(supplier_id, doc_id)
        return self.db.query(SupplierDocumentAudit).filter(
            SupplierDocumentAudit.document_id == doc_id,
            SupplierDocumentAudit.supplier_id == supplier_id,
        ).order_by(SupplierDocumentAudit.created_at.desc()).all()

    def get_expiring_soon(self, supplier_id: str, days: int = 30) -> List:
        from datetime import date, timedelta
        cutoff = date.today() + timedelta(days=days)
        return self.db.query(SupplierDocumentRecord).filter(
            SupplierDocumentRecord.supplier_id == supplier_id,
            SupplierDocumentRecord.deleted_at.is_(None),
            SupplierDocumentRecord.expiry_date.isnot(None),
            SupplierDocumentRecord.expiry_date <= cutoff,
            SupplierDocumentRecord.is_latest == True,
        ).all()
