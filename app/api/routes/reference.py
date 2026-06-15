from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.ingestion_service import import_reference_mgf

router = APIRouter()


UPLOAD_DIR = Path("uploads/reference")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-mgf")
async def upload_reference_mgf(
    library_name: str = Form(...),
    ion_mode: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and import a reference MGF file.
    Example:
    - 20241003_enamdisc_neg_ms2.mgf
    - 20241003_enamdisc_pos_ms2.mgf
    """

    if not file.filename.lower().endswith(".mgf"):
        return {"error": "Only .mgf files are supported for reference upload."}

    ion_mode = ion_mode.upper()

    if ion_mode not in ["NEG", "POS"]:
        return {"error": "ion_mode must be either NEG or POS."}

    safe_filename = f"{uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    result = import_reference_mgf(
        db=db,
        file_path=file_path,
        library_name=library_name,
        ion_mode=ion_mode,
    )

    return {
        "message": "Reference MGF imported successfully.",
        "uploaded_file": file.filename,
        "stored_file": str(file_path),
        **result,
    }