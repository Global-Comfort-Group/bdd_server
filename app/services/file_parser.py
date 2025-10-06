import csv
import io
from typing import List, Dict, Any
import openpyxl
from fastapi import UploadFile

async def parse_csv_file(file: UploadFile) -> List[Dict[str, Any]]:
    """Parse CSV file and extract negotiation data"""
    content = await file.read()
    decoded_content = content.decode('utf-8')
    csv_reader = csv.reader(io.StringIO(decoded_content))
    
    rows = list(csv_reader)
    if len(rows) < 2:
        return []
    
    # Extract headers from first column
    parsed_data = []
    for i, row in enumerate(rows[1:]):  # Skip header row
        if len(row) > 0 and row[0]:  # Check if header exists
            data_row = {
                "header": row[0],
                "value": row[1] if len(row) > 1 else None,
                "agreed_amount": float(row[2]) if len(row) > 2 and row[2] and row[2].replace('.', '').replace('-', '').isdigit() else None,
                "for_nego": float(row[3]) if len(row) > 3 and row[3] and row[3].replace('.', '').replace('-', '').isdigit() else None,
            }
            
            # Calculate percentage difference
            # Formula: (what_we_want - what_they_want) / what_they_want * 100
            # agreed_amount = what we want (BDD's target price)
            # for_nego = what they want (Agent's asking price)
            if data_row["agreed_amount"] and data_row["for_nego"] and data_row["for_nego"] != 0:
                data_row["difference_percentage"] = round(
                    ((data_row["agreed_amount"] - data_row["for_nego"]) / data_row["for_nego"]) * 100, 2
                )
            else:
                data_row["difference_percentage"] = None
            
            parsed_data.append(data_row)
    
    return parsed_data

async def parse_excel_file(file: UploadFile) -> List[Dict[str, Any]]:
    """Parse Excel file and extract negotiation data"""
    content = await file.read()
    workbook = openpyxl.load_workbook(io.BytesIO(content))
    sheet = workbook.active
    
    parsed_data = []
    # Skip header row, start from row 2
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0]:  # Check if header exists
            data_row = {
                "header": str(row[0]),
                "value": str(row[1]) if len(row) > 1 and row[1] else None,
                "agreed_amount": float(row[2]) if len(row) > 2 and isinstance(row[2], (int, float)) else None,
                "for_nego": float(row[3]) if len(row) > 3 and isinstance(row[3], (int, float)) else None,
            }
            
            # Calculate percentage difference
            # Formula: (what_we_want - what_they_want) / what_they_want * 100
            # agreed_amount = what we want (BDD's target price)
            # for_nego = what they want (Agent's asking price)
            if data_row["agreed_amount"] and data_row["for_nego"] and data_row["for_nego"] != 0:
                data_row["difference_percentage"] = round(
                    ((data_row["agreed_amount"] - data_row["for_nego"]) / data_row["for_nego"]) * 100, 2
                )
            else:
                data_row["difference_percentage"] = None
            
            parsed_data.append(data_row)
    
    return parsed_data

async def parse_negotiation_file(file: UploadFile) -> List[Dict[str, Any]]:
    """Parse uploaded file based on file type"""
    filename_lower = file.filename.lower()
    
    if filename_lower.endswith('.csv'):
        return await parse_csv_file(file)
    elif filename_lower.endswith(('.xlsx', '.xls')):
        return await parse_excel_file(file)
    else:
        raise ValueError(f"Unsupported file type: {file.filename}. Please upload CSV or Excel files.")

