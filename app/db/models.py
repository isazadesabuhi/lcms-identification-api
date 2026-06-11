from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class ReferenceLibrary(Base):
    __tablename__ = "reference_libraries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ion_mode = Column(String, nullable=False, index=True)  # NEG or POS
    source_filename = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    spectra = relationship(
        "ReferenceSpectrum",
        back_populates="library",
        cascade="all, delete-orphan",
    )


class ReferenceSpectrum(Base):
    __tablename__ = "reference_spectra"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("reference_libraries.id"), nullable=False)

    spectrum_id = Column(Text, nullable=True)
    feature_id = Column(Text, nullable=True)
    scans = Column(Text, nullable=True)

    name = Column(String, nullable=True)
    formula = Column(String, nullable=True)
    adduct = Column(String, nullable=True)
    smiles = Column(Text, nullable=True)
    inchi = Column(Text, nullable=True)

    precursor_mz = Column(Float, nullable=True, index=True)
    retention_time_seconds = Column(Float, nullable=True)
    ion_mode = Column(String, nullable=False, index=True)

    charge = Column(String, nullable=True)
    ms_level = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    library = relationship("ReferenceLibrary", back_populates="spectra")
    peaks = relationship(
        "ReferencePeak",
        back_populates="spectrum",
        cascade="all, delete-orphan",
    )


class ReferencePeak(Base):
    __tablename__ = "reference_peaks"

    id = Column(Integer, primary_key=True, index=True)
    spectrum_id = Column(Integer, ForeignKey("reference_spectra.id"), nullable=False)

    mz = Column(Float, nullable=False, index=True)
    intensity = Column(Float, nullable=False)

    spectrum = relationship("ReferenceSpectrum", back_populates="peaks")


class UnknownSample(Base):
    __tablename__ = "unknown_samples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ion_mode = Column(String, nullable=False, index=True)  # NEG or POS

    csv_filename = Column(String, nullable=True)
    mgf_filename = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    features = relationship(
        "UnknownFeature",
        back_populates="sample",
        cascade="all, delete-orphan",
    )

    spectra = relationship(
        "UnknownSpectrum",
        back_populates="sample",
        cascade="all, delete-orphan",
    )


class UnknownFeature(Base):
    __tablename__ = "unknown_features"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("unknown_samples.id"), nullable=False)

    feature_id = Column(String, nullable=False, index=True)
    mz = Column(Float, nullable=False, index=True)

    # From CSV: row retention time looks like minutes.
    retention_time_minutes = Column(Float, nullable=True)

    ion_mode = Column(String, nullable=False, index=True)

    best_ion = Column(String, nullable=True)
    neutral_mass = Column(Float, nullable=True)

    peak_areas_json = Column(JSON, nullable=True)
    row_data_json = Column(JSON, nullable=True)

    sample = relationship("UnknownSample", back_populates="features")


class UnknownSpectrum(Base):
    __tablename__ = "unknown_spectra"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("unknown_samples.id"), nullable=False)

    feature_id = Column(String, nullable=True, index=True)
    spectrum_id = Column(Text, nullable=True)
    scans = Column(Text, nullable=True)

    precursor_mz = Column(Float, nullable=True, index=True)

    # From MGF: RTINSECONDS is seconds.
    retention_time_seconds = Column(Float, nullable=True)

    ion_mode = Column(String, nullable=False, index=True)

    charge = Column(String, nullable=True)
    ms_level = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    sample = relationship("UnknownSample", back_populates="spectra")
    peaks = relationship(
        "UnknownPeak",
        back_populates="spectrum",
        cascade="all, delete-orphan",
    )


class UnknownPeak(Base):
    __tablename__ = "unknown_peaks"

    id = Column(Integer, primary_key=True, index=True)
    spectrum_id = Column(Integer, ForeignKey("unknown_spectra.id"), nullable=False)

    mz = Column(Float, nullable=False, index=True)
    intensity = Column(Float, nullable=False)

    spectrum = relationship("UnknownSpectrum", back_populates="peaks")


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)

    unknown_feature_id = Column(Integer, ForeignKey("unknown_features.id"), nullable=False)
    reference_spectrum_id = Column(Integer, ForeignKey("reference_spectra.id"), nullable=False)

    ion_mode = Column(String, nullable=False, index=True)

    mz_error = Column(Float, nullable=True)
    ppm_error = Column(Float, nullable=True)
    rt_error_seconds = Column(Float, nullable=True)
    ms2_score = Column(Float, nullable=True)

    confidence_level = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)