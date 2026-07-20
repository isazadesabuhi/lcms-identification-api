from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.ingestion_service import import_unknown_sample
from app.services.upload_naming import resolve_upload_name, safe_path_component

router = APIRouter()

UPLOAD_DIR = Path("uploads/samples")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/")
def get_samples_status():
    return {"message": "Samples route is working"}


@router.post("/upload")
async def upload_unknown_sample(
    ion_mode: str = Form(...),
    csv_file: UploadFile = File(...),
    mgf_file: UploadFile = File(...),
    sample_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Upload and import an unknown sample using:
    - MZmine/GNPS quant CSV
    - MGF MS2 spectra
    """

    csv_filename = Path(csv_file.filename or "sample.csv").name
    mgf_filename = Path(mgf_file.filename or "sample.mgf").name

    if not csv_filename.lower().endswith(".csv"):
        return {"error": "csv_file must be a .csv file."}

    if not mgf_filename.lower().endswith(".mgf"):
        return {"error": "mgf_file must be a .mgf file."}

    ion_mode = ion_mode.upper()

    if ion_mode not in ["NEG", "POS"]:
        return {"error": "ion_mode must be either NEG or POS."}

    resolved_sample_name = resolve_upload_name(
        provided_name=sample_name,
        kind="sample",
        ion_mode=ion_mode,
        source_filename=csv_filename,
    )
    sample_upload_dir = UPLOAD_DIR / f"{uuid4()}_{safe_path_component(resolved_sample_name, 'sample')}"
    sample_upload_dir.mkdir(parents=True, exist_ok=True)

    csv_path = sample_upload_dir / csv_filename
    mgf_path = sample_upload_dir / mgf_filename

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
        sample_name=resolved_sample_name,
        ion_mode=ion_mode,
    )

    return {
        "message": "Unknown sample imported successfully.",
        "uploaded_csv": csv_filename,
        "uploaded_mgf": mgf_filename,
        "stored_csv": str(csv_path),
        "stored_mgf": str(mgf_path),
        **result,
    }
