from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.ingestion_service import import_unknown_sample

router = APIRouter()

UPLOAD_DIR = Path("uploads/samples")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/")
def get_samples_status():
    return {"message": "Samples route is working"}


@router.post("/upload")
async def upload_unknown_sample(
    sample_name: str = Form(...),
    ion_mode: str = Form(...),
    csv_file: UploadFile = File(...),
    mgf_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and import an unknown sample using:
    - MZmine/GNPS quant CSV
    - MGF MS2 spectra
    """

    if not csv_file.filename.lower().endswith(".csv"):
        return {"error": "csv_file must be a .csv file."}

    if not mgf_file.filename.lower().endswith(".mgf"):
        return {"error": "mgf_file must be a .mgf file."}

    ion_mode = ion_mode.upper()

    if ion_mode not in ["NEG", "POS"]:
        return {"error": "ion_mode must be either NEG or POS."}

    sample_upload_dir = UPLOAD_DIR / f"{uuid4()}_{sample_name}"
    sample_upload_dir.mkdir(parents=True, exist_ok=True)

    csv_path = sample_upload_dir / csv_file.filename
    mgf_path = sample_upload_dir / mgf_file.filename

    with open(csv_path, "wb") as buffer:
        content = await csv_file.read()
        buffer.write(content)

    with open(mgf_path, "wb") as buffer:
        content = await mgf_file.read()
        buffer.write(content)

    result = import_unknown_sample(
        db=db,
        csv_file_path=csv_path,
        mgf_file_path=mgf_path,
        sample_name=sample_name,
        ion_mode=ion_mode,
    )

    return {
        "message": "Unknown sample imported successfully.",
        "uploaded_csv": csv_file.filename,
        "uploaded_mgf": mgf_file.filename,
        "stored_csv": str(csv_path),
        "stored_mgf": str(mgf_path),
        **result,
    }