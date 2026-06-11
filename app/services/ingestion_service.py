from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import (
    ReferenceLibrary,
    ReferencePeak,
    ReferenceSpectrum,
    UnknownFeature,
    UnknownPeak,
    UnknownSample,
    UnknownSpectrum,
)
from app.services.csv_parser import parse_mzmine_quant_csv
from app.services.mgf_parser import parse_mgf


def import_reference_mgf(
    db: Session,
    file_path: str | Path,
    library_name: str,
    ion_mode: str,
) -> dict:
    """
    Import a reference MGF file into the database.
    Used for:
    - 20241003_enamdisc_neg_ms2.mgf
    - 20241003_enamdisc_pos_ms2.mgf
    """

    file_path = Path(file_path)
    ion_mode = ion_mode.upper()

    spectra = parse_mgf(file_path, ion_mode=ion_mode)

    library = ReferenceLibrary(
        name=library_name,
        ion_mode=ion_mode,
        source_filename=file_path.name,
    )

    db.add(library)
    db.flush()

    spectra_count = 0
    peaks_count = 0

    for spectrum_data in spectra:
        spectrum = ReferenceSpectrum(
            library_id=library.id,
            spectrum_id=spectrum_data.get("spectrum_id"),
            feature_id=spectrum_data.get("feature_id"),
            scans=spectrum_data.get("scans"),
            name=spectrum_data.get("name"),
            formula=spectrum_data.get("formula"),
            adduct=spectrum_data.get("adduct"),
            smiles=spectrum_data.get("smiles"),
            inchi=spectrum_data.get("inchi"),
            precursor_mz=spectrum_data.get("precursor_mz"),
            retention_time_seconds=spectrum_data.get("retention_time_seconds"),
            ion_mode=ion_mode,
            charge=spectrum_data.get("charge"),
            ms_level=spectrum_data.get("ms_level"),
            metadata_json=spectrum_data.get("metadata"),
        )

        db.add(spectrum)
        db.flush()

        for peak_data in spectrum_data.get("peaks", []):
            peak = ReferencePeak(
                spectrum_id=spectrum.id,
                mz=peak_data["mz"],
                intensity=peak_data["intensity"],
            )
            db.add(peak)
            peaks_count += 1

        spectra_count += 1

    db.commit()

    return {
        "library_id": library.id,
        "library_name": library.name,
        "ion_mode": library.ion_mode,
        "spectra_imported": spectra_count,
        "peaks_imported": peaks_count,
    }


def import_unknown_sample(
    db: Session,
    csv_file_path: str | Path,
    mgf_file_path: str | Path,
    sample_name: str,
    ion_mode: str,
) -> dict:
    """
    Import an unknown sample using:
    - quant CSV
    - MGF MS2 spectra
    """

    csv_file_path = Path(csv_file_path)
    mgf_file_path = Path(mgf_file_path)
    ion_mode = ion_mode.upper()

    features = parse_mzmine_quant_csv(csv_file_path, ion_mode=ion_mode)
    spectra = parse_mgf(mgf_file_path, ion_mode=ion_mode)

    sample = UnknownSample(
        name=sample_name,
        ion_mode=ion_mode,
        csv_filename=csv_file_path.name,
        mgf_filename=mgf_file_path.name,
    )

    db.add(sample)
    db.flush()

    features_count = 0
    spectra_count = 0
    peaks_count = 0

    for feature_data in features:
        feature = UnknownFeature(
            sample_id=sample.id,
            feature_id=feature_data["feature_id"],
            mz=feature_data["mz"],
            retention_time_minutes=feature_data["retention_time_minutes"],
            ion_mode=ion_mode,
            best_ion=feature_data.get("best_ion"),
            neutral_mass=feature_data.get("neutral_mass"),
            peak_areas_json=feature_data.get("peak_areas"),
            row_data_json=feature_data.get("raw_row"),
        )

        db.add(feature)
        features_count += 1

    for spectrum_data in spectra:
        spectrum = UnknownSpectrum(
            sample_id=sample.id,
            feature_id=str(spectrum_data.get("feature_id"))
            if spectrum_data.get("feature_id") is not None
            else None,
            spectrum_id=spectrum_data.get("spectrum_id"),
            scans=spectrum_data.get("scans"),
            precursor_mz=spectrum_data.get("precursor_mz"),
            retention_time_seconds=spectrum_data.get("retention_time_seconds"),
            ion_mode=ion_mode,
            charge=spectrum_data.get("charge"),
            ms_level=spectrum_data.get("ms_level"),
            metadata_json=spectrum_data.get("metadata"),
        )

        db.add(spectrum)
        db.flush()

        for peak_data in spectrum_data.get("peaks", []):
            peak = UnknownPeak(
                spectrum_id=spectrum.id,
                mz=peak_data["mz"],
                intensity=peak_data["intensity"],
            )
            db.add(peak)
            peaks_count += 1

        spectra_count += 1

    db.commit()

    return {
        "sample_id": sample.id,
        "sample_name": sample.name,
        "ion_mode": sample.ion_mode,
        "features_imported": features_count,
        "spectra_imported": spectra_count,
        "peaks_imported": peaks_count,
    }