from pydantic import BaseModel, Field


class MoleculeDescriptionRequest(BaseModel):
    smiles: str = Field(..., min_length=1)


class LipinskiRuleOfFive(BaseModel):
    molecular_weight_ok: bool
    logp_ok: bool
    h_bond_donors_ok: bool
    h_bond_acceptors_ok: bool
    violations: int


class MoleculeDescription(BaseModel):
    input_smiles: str
    canonical_smiles: str
    formula: str
    exact_molecular_weight: float
    molecular_weight: float
    formal_charge: int
    atom_count: int
    heavy_atom_count: int
    bond_count: int
    ring_count: int
    aromatic_ring_count: int
    h_bond_donors: int
    h_bond_acceptors: int
    rotatable_bonds: int
    tpsa: float
    logp: float
    molar_refractivity: float
    fraction_csp3: float
    qed: float
    atom_composition: dict[str, int]
    lipinski_rule_of_five: LipinskiRuleOfFive
