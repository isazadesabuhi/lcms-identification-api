from pathlib import Path


def _to_float(value):
    if value is None:
        return None

    try:
        return float(str(value).split()[0])
    except ValueError:
        return None


def parse_mgf(file_path: str | Path, ion_mode: str | None = None) -> list[dict]:
    """
    Parse an MGF file and return spectra.

    Supports both:
    - unknown MGF files with FEATURE_ID, PEPMASS, RTINSECONDS
    - reference MGF files with NAME, FORMULA, ADDUCT, SMILES, IONMODE, etc.
    """

    file_path = Path(file_path)

    spectra = []
    current_metadata = None
    current_peaks = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line:
                continue

            if line == "BEGIN IONS":
                current_metadata = {}
                current_peaks = []
                continue

            if line == "END IONS":
                if current_metadata is not None:
                    precursor_mz = _to_float(current_metadata.get("PEPMASS"))
                    retention_time = _to_float(current_metadata.get("RTINSECONDS"))

                    feature_id = current_metadata.get("FEATURE_ID")
                    scans = current_metadata.get("SCANS")
                    name = current_metadata.get("NAME")

                    spectrum_id = feature_id or scans or name

                    parsed_spectrum = {
                        "spectrum_id": spectrum_id,
                        "feature_id": feature_id,
                        "scans": scans,
                        "name": name,
                        "formula": current_metadata.get("FORMULA"),
                        "adduct": current_metadata.get("ADDUCT"),
                        "smiles": current_metadata.get("SMILES"),
                        "inchi": current_metadata.get("INCHI"),
                        "ion_mode": ion_mode.upper() if ion_mode else current_metadata.get("IONMODE"),
                        "precursor_mz": precursor_mz,
                        "retention_time_seconds": retention_time,
                        "charge": current_metadata.get("CHARGE"),
                        "ms_level": current_metadata.get("MSLEVEL"),
                        "metadata": current_metadata,
                        "peaks": current_peaks,
                    }

                    spectra.append(parsed_spectrum)

                current_metadata = None
                current_peaks = []
                continue

            if current_metadata is None:
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                current_metadata[key.strip()] = value.strip()
                continue

            parts = line.split()

            if len(parts) >= 2:
                try:
                    mz = float(parts[0])
                    intensity = float(parts[1])
                    current_peaks.append(
                        {
                            "mz": mz,
                            "intensity": intensity,
                        }
                    )
                except ValueError:
                    # Ignore lines like "Num peaks=139" if they are not caught above
                    continue

    return spectra