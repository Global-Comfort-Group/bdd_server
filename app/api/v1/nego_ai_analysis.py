import io
import csv
import json
from datetime import datetime
from typing import Optional, List

import openpyxl
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.database import get_async_session
from app.models.negotiation_chronicle import NegotiationChronicleAttachment
from app.models.nego_table import NegoTable
from app.models.user import User
from app.services.file_storage import file_storage_service
from sqlalchemy import select

router = APIRouter()


# --------------------------------------------------------------------------- #
# Response schema                                                              #
# --------------------------------------------------------------------------- #

class PriceComparison(BaseModel):
    askingPrice: Optional[str] = None
    clientOffer: Optional[str] = None
    gap: Optional[str] = None
    currency: Optional[str] = None


class RecentTransaction(BaseModel):
    date: Optional[str] = None
    title: str                    # short 3-6 word label e.g. "Cash Payment Agreed"
    summary: str
    event_type: Optional[str] = None  # payment_method|price_change|offer|agreement|condition|meeting
    outcome: Optional[str] = None


class RawExtracted(BaseModel):
    header: str
    value: str


class AIAnalysisResult(BaseModel):
    useful: bool
    reason: Optional[str] = None
    negotiationStatus: Optional[str] = None
    priceComparison: Optional[PriceComparison] = None
    clientConditions: Optional[List[str]] = None
    recentTransactions: Optional[List[RecentTransaction]] = None
    keyNotes: Optional[List[str]] = None
    rawExtracted: Optional[List[RawExtracted]] = None


class UploadAnalysisResponse(BaseModel):
    attachment_id: int
    ai_result: AIAnalysisResult


# New comparison schema

class NegotiationItem(BaseModel):
    title: str
    bdd_offer: str = ""
    client_offer: str = ""
    status: str = "negotiating"  # "agreed" | "negotiating"
    agreed_date: Optional[str] = None
    final_value: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('title', 'bdd_offer', 'client_offer', mode='before')
    @classmethod
    def coerce_none_to_str(cls, v: object) -> str:
        return "" if v is None else str(v)


class AIComparisonResult(BaseModel):
    useful: bool
    reason: Optional[str] = None
    overall_status: Optional[str] = None
    summary: Optional[str] = None
    negotiation_items: List[NegotiationItem] = []


class UploadForPropertyResponse(BaseModel):
    attachment_id: int
    ai_result: AIComparisonResult
    nego_table_id: int


# --------------------------------------------------------------------------- #
# File → plain-text helpers                                                   #
# --------------------------------------------------------------------------- #

def _cell_to_str(cell) -> str:
    if cell is None:
        return ""
    return str(cell)


def _extract_xlsx_text(content: bytes) -> str:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheets_text: list[str] = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows_text: list[str] = []

        for i, row in enumerate(ws.iter_rows(max_row=200, values_only=True)):
            cells = [_cell_to_str(c) for c in row[:27]]
            if any(c.strip() for c in cells):
                rows_text.append("\t".join(cells))
            if i >= 199:
                break

        if rows_text:
            sheets_text.append(f"=== Sheet: {sheet_name} ===\n" + "\n".join(rows_text))

    wb.close()
    return "\n\n".join(sheets_text)


def _extract_xls_text(content: bytes) -> str:
    try:
        import xlrd
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Legacy .xls format requires xlrd. Please convert to .xlsx and re-upload.",
        )

    wb = xlrd.open_workbook(file_contents=content)
    sheets_text: list[str] = []

    for sheet_name in wb.sheet_names():
        ws = wb.sheet_by_name(sheet_name)
        rows_text: list[str] = []

        for i in range(min(ws.nrows, 200)):
            cells = [
                str(ws.cell_value(i, j)) if j < ws.ncols else ""
                for j in range(min(ws.ncols, 27))
            ]
            if any(c.strip() for c in cells):
                rows_text.append("\t".join(cells))

        if rows_text:
            sheets_text.append(f"=== Sheet: {sheet_name} ===\n" + "\n".join(rows_text))

    return "\n\n".join(sheets_text)


def _extract_csv_text(content: bytes) -> str:
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    reader = csv.reader(io.StringIO(decoded))
    rows: list[str] = []
    for i, row in enumerate(reader):
        if i > 200:
            break
        if any(cell.strip() for cell in row):
            rows.append("\t".join(row))

    return "\n".join(rows)


def _file_to_text(content: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".csv"):
        return _extract_csv_text(content)
    elif lower.endswith(".xls"):
        return _extract_xls_text(content)
    else:
        return _extract_xlsx_text(content)


# --------------------------------------------------------------------------- #
# Gemini prompt                                                                #
# --------------------------------------------------------------------------- #

_SYSTEM_INSTRUCTION = (
    "You are a real estate negotiation analyst specialising in commercial property deals "
    "in the Philippines and Southeast Asia. "
    "Your job is to analyse spreadsheet data and extract a structured negotiation DECISION TIMELINE. "
    "Always respond with valid JSON only — no markdown, no explanation, just the JSON object."
)

_USER_PROMPT_TEMPLATE = """\
Analyse the following spreadsheet data and extract negotiation information, \
focusing on building a chronological DECISION TIMELINE.

SPREADSHEET CONTENT:
{sheet_text}

Return a JSON object with this exact schema:
{{
  "useful": boolean,
  "reason": "string (only if useful=false — explain why the file is not negotiation-related)",
  "negotiationStatus": "string (e.g. 'Active – Counter offer stage')",
  "priceComparison": {{
    "askingPrice": "string (formatted, e.g. '₱150,000/month')",
    "clientOffer": "string (formatted)",
    "gap": "string (the difference, e.g. '₱20,000 or 13%')",
    "currency": "string (e.g. 'PHP', 'USD')"
  }},
  "clientConditions": ["plain-English condition strings"],
  "recentTransactions": [
    {{
      "date": "string or null (e.g. 'Feb 10, 2026')",
      "title": "string — short 3-6 word label for this event (e.g. 'Cash Payment Agreed', \
'Price Reduced to ₱12.5M', 'BDO Loan Declined', 'Lease Term Extended')",
      "summary": "string — 1-3 sentences: WHO did WHAT and WHY",
      "event_type": "one of: payment_method | price_change | offer | agreement | condition | meeting | rejection | other",
      "outcome": "string or null — the result/next step"
    }}
  ],
  "keyNotes": ["important flag / risk / observation strings"],
  "rawExtracted": [
    {{ "header": "label/field name", "value": "the value" }}
  ]
}}

Rules:
- Set useful=false if the file contains no negotiation-related data (e.g. user list, \
financial report, unrelated data). Provide a clear reason.
- Set useful=true if you can extract any meaningful negotiation data.
- recentTransactions MUST be sorted chronologically (oldest first).
- Every recentTransaction MUST have a non-empty title — create a concise label even if \
the date is unknown.
- Detect these events: payment method changes, price reductions/increases, \
offer/counter-offer, loan rejections, lease condition changes, key meetings, agreements.
- rawExtracted must contain ALL key-value pairs that are negotiation-relevant \
(used for backward-compat storage).
- All monetary values must preserve their original currency and formatting.
- Omit any field that has no data (do not include null fields).
- clientConditions and keyNotes should be plain-English bullet-point strings.
"""


_COMPARISON_SYSTEM_INSTRUCTION = (
    "You are a real estate negotiation analyst specialising in commercial property deals "
    "in the Philippines and Southeast Asia. "
    "Your job is to analyse spreadsheet data and extract a per-item BDD Employee vs Client comparison. "
    "Always respond with valid JSON only — no markdown, no explanation, just the JSON object."
)

_COMPARISON_PROMPT_TEMPLATE = """\
You are analyzing a real estate negotiation document between a broker/agent (BDD Employee) and the client (buyer/lessee).

SPREADSHEET CONTENT:
{sheet_text}

Extract a per-item comparison for ALL negotiated topics (Costing, Payment Method, Payment Schedule, \
Lease Term, Security Deposit, Advance Rent, Escalation, Orientation, etc.).

Return a JSON object with this exact schema:
{{
  "useful": boolean,
  "reason": "string (only if useful=false — explain why the file is not negotiation-related)",
  "overall_status": "string (e.g. 'Mostly agreed, cost still negotiating')",
  "summary": "string (optional brief summary)",
  "negotiation_items": [
    {{
      "title": "string — short name of the negotiation topic (e.g. 'Costing', 'Payment Method')",
      "bdd_offer": "string — the broker/BDD employee's position or offer",
      "client_offer": "string — the client's counter-offer or position",
      "status": "agreed | negotiating",
      "agreed_date": "string or null — date when they agreed (only if status is 'agreed')",
      "final_value": "string or null — what they ultimately agreed on (if agreed)",
      "notes": "string or null — any important context"
    }}
  ]
}}

Rules:
- Set useful=false if the file contains no negotiation-related data. Provide a clear reason.
- Set useful=true if you can extract any meaningful negotiation data.
- agreed_date is ONLY non-null when both sides have mutually agreed on that item.
- status must be exactly "agreed" or "negotiating".
- Extract ALL negotiated topics you can find — do not skip any.
- All monetary values must preserve their original currency and formatting.
- Omit optional fields (final_value, notes) if there is no data for them.
- negotiation_items must be a list — never null or omitted.
"""


async def _call_gemini_comparison(sheet_text: str, api_key: str) -> AIComparisonResult:
    """Call Gemini REST API with the comparison prompt and return parsed AIComparisonResult."""
    import httpx

    gemini_url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": _COMPARISON_SYSTEM_INSTRUCTION}]},
        "contents": [
            {"parts": [{"text": _COMPARISON_PROMPT_TEMPLATE.format(sheet_text=sheet_text)}]}
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "maxOutputTokens": 65536,
        },
    }

    async with httpx.AsyncClient(timeout=300.0) as http_client:
        gemini_response = await http_client.post(gemini_url, json=payload)

    if gemini_response.status_code != 200:
        print(f"💥 Gemini API error {gemini_response.status_code}: {gemini_response.text[:500]}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error {gemini_response.status_code}: {gemini_response.text[:300]}",
        )

    gemini_data = gemini_response.json()
    candidate = gemini_data["candidates"][0]
    finish_reason = candidate.get("finishReason", "STOP")
    if finish_reason == "MAX_TOKENS":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI response was truncated (output token limit hit). Please try with a smaller file.",
        )
    result_text = candidate["content"]["parts"][0]["text"]
    result_dict = json.loads(result_text)
    return AIComparisonResult(**result_dict)


async def _call_gemini(sheet_text: str, api_key: str) -> AIAnalysisResult:
    """Call Gemini REST API and return parsed AIAnalysisResult."""
    import httpx

    gemini_url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": _SYSTEM_INSTRUCTION}]},
        "contents": [
            {"parts": [{"text": _USER_PROMPT_TEMPLATE.format(sheet_text=sheet_text)}]}
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "maxOutputTokens": 65536,
        },
    }

    async with httpx.AsyncClient(timeout=300.0) as http_client:
        gemini_response = await http_client.post(gemini_url, json=payload)

    if gemini_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error {gemini_response.status_code}: {gemini_response.text[:300]}",
        )

    gemini_data = gemini_response.json()
    candidate = gemini_data["candidates"][0]
    finish_reason = candidate.get("finishReason", "STOP")
    if finish_reason == "MAX_TOKENS":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI response was truncated (output token limit hit). Please try with a smaller file.",
        )
    result_text = candidate["content"]["parts"][0]["text"]
    result_dict = json.loads(result_text)
    return AIAnalysisResult(**result_dict)


# --------------------------------------------------------------------------- #
# Endpoints                                                                    #
# --------------------------------------------------------------------------- #

@router.post("/analyze", response_model=AIAnalysisResult)
async def analyze_negotiation_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Analyse an uploaded negotiation file (xlsx, xls, csv) using Google Gemini AI.
    Returns structured negotiation insights — does NOT persist to database.
    """
    api_key = settings.GOOGLE_GEMINI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis is not configured on this server (missing GOOGLE_GEMINI_API_KEY).",
        )

    filename = file.filename or ""
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in (".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload .xlsx, .xls, or .csv",
        )

    content = await file.read()

    try:
        sheet_text = _file_to_text(content, filename)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read file: {exc}",
        )

    if not sheet_text.strip():
        return AIAnalysisResult(useful=False, reason="The uploaded file appears to be empty.")

    try:
        return await _call_gemini(sheet_text, api_key)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response: {exc}",
        )
    except Exception as exc:
        print(f"💥 Gemini analysis error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {exc}",
        )


@router.post("/upload/{nego_table_id}", response_model=UploadAnalysisResponse)
async def upload_and_analyze(
    nego_table_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a negotiation file, run Gemini AI analysis, auto-save to DB, and return the result.
    This is the single-step endpoint used by the new Negotiation Timeline UI.
    """
    api_key = settings.GOOGLE_GEMINI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis is not configured on this server (missing GOOGLE_GEMINI_API_KEY).",
        )

    # Validate nego table exists in DB
    result = await db.execute(select(NegoTable).filter(NegoTable.id == nego_table_id))
    nego_table = result.scalar_one_or_none()
    if not nego_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation table {nego_table_id} not found",
        )

    filename = file.filename or ""
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in (".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload .xlsx, .xls, or .csv",
        )

    content = await file.read()

    # Parse spreadsheet to text
    try:
        sheet_text = _file_to_text(content, filename)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read file: {exc}",
        )

    if not sheet_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file appears to be empty.",
        )

    # Call Gemini AI
    try:
        ai_result = await _call_gemini(sheet_text, api_key)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response: {exc}",
        )
    except Exception as exc:
        print(f"💥 Gemini upload+analyze error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {exc}",
        )

    # Upload file to OSS storage
    await file.seek(0)
    try:
        upload_result = await file_storage_service.save_file(file, subfolder="negotiation_chronicles")
        file_url = upload_result["secure_url"]
    except Exception as exc:
        print(f"⚠️  OSS upload failed, storing without file URL: {exc}")
        file_url = ""

    # Build rawExtracted for backward-compat parsed_data column
    raw_extracted = ai_result.rawExtracted or []
    parsed_data = [{"header": r.header, "value": r.value} for r in raw_extracted]

    # Persist to database
    attachment = NegotiationChronicleAttachment(
        nego_table_id=nego_table_id,
        filename=filename,
        file_url=file_url,
        file_type=lower.rsplit(".", 1)[-1],
        file_size=len(content),
        parsed_data=parsed_data,
        ai_result=ai_result.model_dump(),
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    print(f"✅ Saved AI timeline attachment {attachment.id} for nego table {nego_table_id}")

    return UploadAnalysisResponse(
        attachment_id=attachment.id,
        ai_result=ai_result,
    )


@router.post("/upload-for-property/{property_id}", response_model=UploadForPropertyResponse)
async def upload_for_property(
    property_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a negotiation file for a property. Auto-creates a NegoTable if one doesn't exist.
    Runs Gemini AI comparison analysis (BDD Employee vs Client per item) and saves to DB.
    Only BDD_USER (assigned reviewer) and ADMIN may upload.
    """
    from app.models.nego_table import NegoTableStatus

    api_key = settings.GOOGLE_GEMINI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis is not configured on this server (missing GOOGLE_GEMINI_API_KEY).",
        )

    filename = file.filename or ""
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in (".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload .xlsx, .xls, or .csv",
        )

    content = await file.read()

    # Parse spreadsheet to text
    try:
        sheet_text = _file_to_text(content, filename)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read file: {exc}",
        )

    if not sheet_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file appears to be empty.",
        )

    # Call Gemini AI with comparison prompt first — before touching the DB
    try:
        ai_result = await _call_gemini_comparison(sheet_text, api_key)
    except HTTPException:
        raise  # let 502/503 from Gemini propagate with its real detail
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response: {exc}",
        )
    except Exception as exc:
        print(f"💥 Gemini comparison error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {type(exc).__name__}: {exc}",
        )

    # If Gemini says the file is not negotiation-related, return early — nothing is saved
    if not ai_result.useful:
        print(f"⚠️  File '{filename}' rejected by AI for property {property_id}: {ai_result.reason}")
        return UploadForPropertyResponse(
            attachment_id=-1,
            ai_result=ai_result,
            nego_table_id=-1,
        )

    # Get or create NegoTable for this property (only reached when file is useful)
    result = await db.execute(select(NegoTable).where(NegoTable.property_id == property_id))
    nego_table = result.scalar_one_or_none()
    if not nego_table:
        nego_table = NegoTable(
            property_id=property_id,
            status=NegoTableStatus.ACTIVE,
            created_by_id=current_user.id,
            referred_date=datetime.utcnow(),
        )
        db.add(nego_table)
        await db.commit()
        await db.refresh(nego_table)
        print(f"✅ Auto-created NegoTable {nego_table.id} for property {property_id}")

    # Upload file to OSS storage
    await file.seek(0)
    try:
        upload_result = await file_storage_service.save_file(file, subfolder="negotiation_chronicles")
        file_url = upload_result["secure_url"]
    except Exception as exc:
        print(f"⚠️  OSS upload failed, storing without file URL: {exc}")
        file_url = ""

    # Persist attachment with ai_result
    attachment = NegotiationChronicleAttachment(
        nego_table_id=nego_table.id,
        filename=filename,
        file_url=file_url,
        file_type=lower.rsplit(".", 1)[-1],
        file_size=len(content),
        parsed_data=[],
        ai_result=ai_result.model_dump(),
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    print(f"✅ Saved AI comparison attachment {attachment.id} for property {property_id} (nego table {nego_table.id})")

    return UploadForPropertyResponse(
        attachment_id=attachment.id,
        ai_result=ai_result,
        nego_table_id=nego_table.id,
    )
