import io
import csv
import json
from typing import Optional, List

import openpyxl
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.models.user import User

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
    summary: str
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
# Endpoint                                                                     #
# --------------------------------------------------------------------------- #

_SYSTEM_INSTRUCTION = (
    "You are a real estate negotiation analyst specialising in commercial property deals "
    "in the Philippines and Southeast Asia. "
    "Your job is to analyse spreadsheet data and extract structured negotiation insights. "
    "Always respond with valid JSON only — no markdown, no explanation, just the JSON object."
)

_USER_PROMPT_TEMPLATE = """\
Analyse the following spreadsheet data and extract negotiation information.

SPREADSHEET CONTENT:
{sheet_text}

Return a JSON object with this exact schema:
{{
  "useful": boolean,
  "reason": "string (only if useful=false — explain why)",
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
      "date": "string or null",
      "summary": "string describing what happened",
      "outcome": "string or null"
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
- rawExtracted must contain ALL key-value pairs that are negotiation-relevant \
(used for saving to chronicle).
- All monetary values must preserve their original currency and formatting.
- Omit any field that has no data (do not include null fields).
- clientConditions and keyNotes should be plain-English bullet-point strings.
"""


@router.post("/analyze", response_model=AIAnalysisResult)
async def analyze_negotiation_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Analyse an uploaded negotiation file (xlsx, xls, csv) using Google Gemini AI.
    Returns structured negotiation insights regardless of the original file layout.
    Requires authentication to prevent unauthorised Gemini API usage.
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

    # Convert spreadsheet to plain text
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

    # Call Gemini via REST (avoids SDK dependency conflicts)
    try:
        import httpx

        gemini_url = (
            "https://generativelanguage.googleapis.com/v1beta/models"
            f"/gemini-2.0-flash:generateContent?key={api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": _SYSTEM_INSTRUCTION}]},
            "contents": [
                {"parts": [{"text": _USER_PROMPT_TEMPLATE.format(sheet_text=sheet_text)}]}
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=90.0) as http_client:
            gemini_response = await http_client.post(gemini_url, json=payload)

        if gemini_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini API error {gemini_response.status_code}: {gemini_response.text[:300]}",
            )

        gemini_data = gemini_response.json()
        result_text = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
        result_dict = json.loads(result_text)
        return AIAnalysisResult(**result_dict)

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
