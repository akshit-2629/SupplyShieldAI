"""
module_c_routers.py — Setup Status, Quality Management, Document Center API routers.
All three routers are exported for registration in api.py.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import require_supplier, UserPrincipal
from app.supplier_portal.schemas import APIResponse, PaginatedResponse, paginate
from app.supplier_portal.services.module_c_services import (
    SetupStatusService, QualityService, DocumentCenterService
)

logger = logging.getLogger("supplier_portal.module_c_routers")


def _ip(request: Request) -> str:
    return request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")


# ══════════════════════════════════════════════════════════════════════════════
# SETUP STATUS ROUTER
# ══════════════════════════════════════════════════════════════════════════════

setup_router = APIRouter(prefix="/setup-status", tags=["Supplier Portal — Setup Status"])


@setup_router.get("", response_model=APIResponse, summary="Get wizard setup status")
async def get_setup_status(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc    = SetupStatusService(db)
    status = svc.get_status(current_user.user_id)
    return APIResponse(data=status, message="Setup status retrieved")


@setup_router.post("/step/{step}", response_model=APIResponse, summary="Mark wizard step complete")
async def mark_step(
    step: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc    = SetupStatusService(db)
    status = svc.mark_step(current_user.user_id, step)
    return APIResponse(data=status, message=f"Step '{step}' marked complete")


@setup_router.post("/complete", response_model=APIResponse, summary="Mark wizard fully complete")
async def mark_wizard_complete(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc    = SetupStatusService(db)
    status = svc.mark_complete(current_user.user_id)
    return APIResponse(data=status, message="Setup wizard completed. Portal is now active.")


# ══════════════════════════════════════════════════════════════════════════════
# QUALITY MANAGEMENT ROUTER
# ══════════════════════════════════════════════════════════════════════════════

quality_router = APIRouter(prefix="/quality", tags=["Supplier Portal — Quality Management"])


@quality_router.get("", response_model=PaginatedResponse, summary="List quality records")
async def list_quality_records(
    record_type: Optional[str] = None,
    severity:    Optional[str] = None,
    status:      Optional[str] = None,
    search:      Optional[str] = None,
    page:        int = Query(1, ge=1),
    page_size:   int = Query(20, ge=1, le=100),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc  = QualityService(db)
    rows, total = svc.list_records(
        current_user.user_id, record_type=record_type, severity=severity,
        status=status, search=search, page=page, page_size=page_size,
    )
    return PaginatedResponse(
        data=[_quality_to_dict(r) for r in rows],
        **paginate(total, page, page_size),
    )


@quality_router.get("/kpis", response_model=APIResponse, summary="Get quality KPIs")
async def get_quality_kpis(
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc  = QualityService(db)
    data = svc.get_kpis(current_user.user_id)
    return APIResponse(data=data)


@quality_router.post("", status_code=201, response_model=APIResponse,
                     summary="Create quality record — triggers orchestrator")
async def create_quality_record(
    body:    dict,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = QualityService(db)
    row = svc.create_record(current_user.user_id, current_user.user_id, body, _ip(request))
    return APIResponse(data=_quality_to_dict(row), message="Quality record created")


@quality_router.get("/{record_id}", response_model=APIResponse, summary="Get quality record")
async def get_quality_record(
    record_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = QualityService(db)
    row = svc.get_record(current_user.user_id, record_id)
    return APIResponse(data=_quality_to_dict(row))


@quality_router.put("/{record_id}", response_model=APIResponse,
                    summary="Update quality record")
async def update_quality_record(
    record_id: str,
    body:    dict,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = QualityService(db)
    row = svc.update_record(current_user.user_id, current_user.user_id,
                             record_id, body, _ip(request))
    return APIResponse(data=_quality_to_dict(row), message="Quality record updated")


@quality_router.delete("/{record_id}", response_model=APIResponse,
                       summary="Soft-delete quality record")
async def delete_quality_record(
    record_id: str,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = QualityService(db)
    svc.delete_record(current_user.user_id, current_user.user_id, record_id, _ip(request))
    return APIResponse(message="Quality record deleted")


@quality_router.get("/{record_id}/history", response_model=APIResponse,
                    summary="Get version history for a quality record")
async def get_quality_history(
    record_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc  = QualityService(db)
    rows = svc.get_history(current_user.user_id, record_id)
    return APIResponse(data=[{
        "version":        r.version,
        "changed_by":     r.changed_by,
        "changed_at":     r.changed_at.isoformat() if r.changed_at else None,
        "change_summary": r.change_summary,
        "snapshot":       r.snapshot,
    } for r in rows])


def _quality_to_dict(r) -> dict:
    return {
        "id":                      str(r.id),
        "record_number":           r.record_number,
        "record_type":             r.record_type,
        "severity":                r.severity,
        "status":                  r.status,
        "title":                   r.title,
        "description":             r.description,
        "inspection_date":         r.inspection_date.isoformat() if r.inspection_date else None,
        "product_sku":             r.product_sku,
        "product_name":            r.product_name,
        "batch_number":            r.batch_number,
        "quantity_inspected":      r.quantity_inspected,
        "quantity_passed":         r.quantity_passed,
        "quantity_failed":         r.quantity_failed,
        "defect_rate_pct":         float(r.defect_rate_pct) if r.defect_rate_pct else None,
        "root_cause":              r.root_cause,
        "corrective_action":       r.corrective_action,
        "corrective_action_date":  r.corrective_action_date.isoformat() if r.corrective_action_date else None,
        "responsible_person":      r.responsible_person,
        "standard_reference":      r.standard_reference,
        "customer_notified":       r.customer_notified,
        "regulatory_reportable":   r.regulatory_reportable,
        "attachments":             r.attachments or [],
        "version":                 r.version,
        "created_by":              r.created_by,
        "closed_at":               r.closed_at.isoformat() if r.closed_at else None,
        "created_at":              r.created_at.isoformat() if r.created_at else None,
        "updated_at":              r.updated_at.isoformat() if r.updated_at else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT CENTER ROUTER
# ══════════════════════════════════════════════════════════════════════════════

documents_router = APIRouter(prefix="/documents", tags=["Supplier Portal — Document Center"])


@documents_router.get("", response_model=PaginatedResponse, summary="List documents")
async def list_documents(
    category:  Optional[str] = None,
    status:    Optional[str] = None,
    search:    Optional[str] = None,
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc  = DocumentCenterService(db)
    rows, total = svc.list_documents(
        current_user.user_id, category=category, status=status,
        search=search, page=page, page_size=page_size,
    )
    return PaginatedResponse(
        data=[_doc_to_dict(r) for r in rows],
        **paginate(total, page, page_size),
    )


@documents_router.post("", status_code=201, response_model=APIResponse,
                       summary="Upload document to Supabase Storage")
async def upload_document(
    request:      Request,
    file:         UploadFile = File(...),
    category:     str  = Form("GENERAL"),
    display_name: str  = Form(None),
    description:  str  = Form(None),
    document_date: str = Form(None),
    expiry_date:  str  = Form(None),
    issuing_body: str  = Form(None),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    from app.core.exceptions import FileUploadException
    contents = await file.read()
    if len(contents) > 52_428_800:   # 50 MB
        raise FileUploadException("File exceeds 50 MB limit")

    from datetime import date as _date, datetime as _dt
    def _parse_date(s):
        if not s: return None
        try: return _date.fromisoformat(s)
        except Exception: pass
        try:
            parts = str(s).strip().split('/')
            if len(parts) == 3:
                return _date(int(parts[2]), int(parts[1]), int(parts[0]))
        except Exception: pass
        return None


    svc = DocumentCenterService(db)
    row = await svc.upload_document(
        supplier_id=current_user.user_id, user_id=current_user.user_id,
        file_bytes=contents, file_name=file.filename,
        content_type=file.content_type or "application/octet-stream",
        category=category, display_name=display_name, description=description,
        document_date=_parse_date(document_date), expiry_date=_parse_date(expiry_date),
        issuing_body=issuing_body, ip_address=_ip(request),
    )
    return APIResponse(data=_doc_to_dict(row), message="Document uploaded successfully")


@documents_router.get("/expiring", response_model=APIResponse, summary="Get expiring documents")
async def get_expiring_documents(
    days: int = Query(30, ge=1, le=365),
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc  = DocumentCenterService(db)
    rows = svc.get_expiring_soon(current_user.user_id, days=days)
    return APIResponse(data=[_doc_to_dict(r) for r in rows],
                       message=f"{len(rows)} document(s) expiring within {days} days")


@documents_router.get("/{doc_id}", response_model=APIResponse, summary="Get document metadata")
async def get_document(
    doc_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = DocumentCenterService(db)
    row = svc.get_document(current_user.user_id, doc_id)
    return APIResponse(data=_doc_to_dict(row))


@documents_router.put("/{doc_id}", response_model=APIResponse, summary="Update document metadata")
async def update_document(
    doc_id:  str,
    body:    dict,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = DocumentCenterService(db)
    row = svc.update_document(current_user.user_id, current_user.user_id,
                               doc_id, body, _ip(request))
    return APIResponse(data=_doc_to_dict(row), message="Document updated")


@documents_router.delete("/{doc_id}", response_model=APIResponse, summary="Delete document + Storage file")
async def delete_document(
    doc_id:  str,
    request: Request,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc = DocumentCenterService(db)
    svc.delete_document(current_user.user_id, current_user.user_id, doc_id, _ip(request))
    return APIResponse(message="Document deleted")


@documents_router.get("/{doc_id}/versions", response_model=APIResponse, summary="Get document versions")
async def get_document_versions(
    doc_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc  = DocumentCenterService(db)
    rows = svc.get_versions(current_user.user_id, doc_id)
    return APIResponse(data=[_doc_to_dict(r) for r in rows])


@documents_router.get("/{doc_id}/audit", response_model=APIResponse, summary="Get document audit log")
async def get_document_audit(
    doc_id: str,
    current_user: UserPrincipal = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    svc  = DocumentCenterService(db)
    rows = svc.get_audit_log(current_user.user_id, doc_id)
    return APIResponse(data=[{
        "action":     r.action,
        "actor_id":   r.actor_id,
        "ip_address": r.ip_address,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "metadata":   r.metadata or {},
    } for r in rows])


def _doc_to_dict(r) -> dict:
    return {
        "id":            str(r.id),
        "file_name":     r.file_name,
        "display_name":  r.display_name,
        "description":   r.description,
        "category":      r.category,
        "storage_bucket": r.storage_bucket,
        "storage_path":  r.storage_path,
        "public_url":    r.public_url,
        "content_type":  r.content_type,
        "size_bytes":    r.size_bytes,
        "document_date": r.document_date.isoformat() if r.document_date else None,
        "expiry_date":   r.expiry_date.isoformat() if r.expiry_date else None,
        "issuing_body":  r.issuing_body,
        "version":       r.version,
        "is_latest":     r.is_latest,
        "status":        r.status,
        "tags":          r.tags or [],
        "uploaded_by":   r.uploaded_by,
        "uploaded_at":   r.uploaded_at.isoformat() if r.uploaded_at else None,
        "updated_at":    r.updated_at.isoformat() if r.updated_at else None,
    }
