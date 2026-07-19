from fastapi import APIRouter, HTTPException, Query

from app.schemas.molecules import MoleculeDescription, MoleculeDescriptionRequest
from app.services.molecule_service import describe_molecule

router = APIRouter()


@router.get("/describe", response_model=MoleculeDescription)
def describe_molecule_from_query(
    smiles: str = Query(..., min_length=1),
):
    description = describe_molecule(smiles)

    if description is None:
        raise HTTPException(status_code=400, detail="Invalid SMILES string.")

    return description


@router.post("/describe", response_model=MoleculeDescription)
def describe_molecule_from_body(
    payload: MoleculeDescriptionRequest,
):
    description = describe_molecule(payload.smiles)

    if description is None:
        raise HTTPException(status_code=400, detail="Invalid SMILES string.")

    return description
