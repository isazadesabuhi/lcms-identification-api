from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.ingestion_service import import_reference_mgf
from app.services.upload_naming import resolve_upload_name

router = APIRouter()


UPLOAD_DIR = Path("uploads/reference")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-mgf")
async def upload_reference_mgf(
    ion_mode: str = Form(...),
    file: UploadFile = File(...),
    library_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Upload and import a reference MGF file.
    Example:
    - 20241003_enamdisc_neg_ms2.mgf
    - 20241003_enamdisc_pos_ms2.mgf
    """

    filename = Path(file.filename or "reference.mgf").name

    if not filename.lower().endswith(".mgf"):
        return {"error": "Only .mgf files are supported for reference upload."}

    ion_mode = ion_mode.upper()

    if ion_mode not in ["NEG", "POS"]:
        return {"error": "ion_mode must be either NEG or POS."}

    resolved_library_name = resolve_upload_name(
        provided_name=library_name,
        kind="reference",
        ion_mode=ion_mode,
        source_filename=filename,
    )
    safe_filename = f"{uuid4()}_{filename}"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    result = import_reference_mgf(
        db=db,
        file_path=file_path,
        library_name=resolved_library_name,
        ion_mode=ion_mode,
    )

    return {
        "message": "Reference MGF imported successfully.",
        "uploaded_file": filename,
        "stored_file": str(file_path),
        **result,
    }
