from app.services.mgf_parser import parse_mgf


files = [
    ("data/unknown/neg/NEG_fbmn.mgf", "NEG"),
    ("data/unknown/pos/POS_fbmn.mgf", "POS"),
    ("data/reference/neg/20241003_enamdisc_neg_ms2.mgf", "NEG"),
    ("data/reference/pos/20241003_enamdisc_pos_ms2.mgf", "POS"),
]


for file_path, ion_mode in files:
    spectra = parse_mgf(file_path, ion_mode=ion_mode)

    print("=" * 80)
    print(file_path)
    print("Spectra detected:", len(spectra))

    if spectra:
        first = spectra[0]
        print("First spectrum:")
        print("  spectrum_id:", first["spectrum_id"])
        print("  feature_id:", first["feature_id"])
        print("  name:", first["name"])
        print("  formula:", first["formula"])
        print("  adduct:", first["adduct"])
        print("  precursor_mz:", first["precursor_mz"])
        print("  retention_time_seconds:", first["retention_time_seconds"])
        print("  ion_mode:", first["ion_mode"])
        print("  peaks:", len(first["peaks"]))