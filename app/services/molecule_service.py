from collections import Counter

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, QED, rdMolDescriptors


def _round(value: float) -> float:
    return round(float(value), 4)


def describe_molecule(smiles: str) -> dict | None:
    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        return None

    canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
    atom_composition = Counter(atom.GetSymbol() for atom in mol.GetAtoms())

    molecular_weight = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    h_bond_donors = Lipinski.NumHDonors(mol)
    h_bond_acceptors = Lipinski.NumHAcceptors(mol)

    lipinski_checks = {
        "molecular_weight_ok": molecular_weight <= 500,
        "logp_ok": logp <= 5,
        "h_bond_donors_ok": h_bond_donors <= 5,
        "h_bond_acceptors_ok": h_bond_acceptors <= 10,
    }

    return {
        "input_smiles": smiles,
        "canonical_smiles": canonical_smiles,
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "exact_molecular_weight": _round(Descriptors.ExactMolWt(mol)),
        "molecular_weight": _round(molecular_weight),
        "formal_charge": Chem.GetFormalCharge(mol),
        "atom_count": mol.GetNumAtoms(),
        "heavy_atom_count": mol.GetNumHeavyAtoms(),
        "bond_count": mol.GetNumBonds(),
        "ring_count": rdMolDescriptors.CalcNumRings(mol),
        "aromatic_ring_count": rdMolDescriptors.CalcNumAromaticRings(mol),
        "h_bond_donors": h_bond_donors,
        "h_bond_acceptors": h_bond_acceptors,
        "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
        "tpsa": _round(rdMolDescriptors.CalcTPSA(mol)),
        "logp": _round(logp),
        "molar_refractivity": _round(Crippen.MolMR(mol)),
        "fraction_csp3": _round(rdMolDescriptors.CalcFractionCSP3(mol)),
        "qed": _round(QED.qed(mol)),
        "atom_composition": dict(sorted(atom_composition.items())),
        "lipinski_rule_of_five": {
            **lipinski_checks,
            "violations": sum(not passed for passed in lipinski_checks.values()),
        },
    }
