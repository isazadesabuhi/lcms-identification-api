# LC-MS Compound Identification API

FastAPI backend for identifying unknown compounds in LC-MS analysis of natural product extracts.

This project uses a hybrid workflow:

```text
mzML files
→ processed in MZmine
→ exported as CSV + MGF
→ uploaded to FastAPI
→ stored in database
→ matched against reference library
→ scored and ranked as candidate identifications
```

## Project Goal

The goal of this project is to build a backend platform that identifies unknown compounds from LC-MS data by comparing unknown sample features against an internal reference database.

The platform currently uses:

* FastAPI for the backend API
* SQLite for local development database
* CSV parser for MZmine/GNPS quant files
* MGF parser for MS/MS spectra
* m/z matching
* MS2 spectral similarity scoring
* Retention time scoring
* RDKit molecule descriptors from SMILES
* Ranked candidate results
* CSV export
* Celery task structure in eager mode

## Role of MZmine

Raw LC-MS files such as `.mzML` are not processed directly by FastAPI in the current version.

Instead:

1. mzML files are processed in MZmine.
2. MZmine exports CSV and MGF files.
3. The FastAPI platform ingests those exported files.
4. The backend performs matching and scoring.

## Current Features

### File Parsing

* Parses unknown sample CSV files.
* Parses unknown sample MGF files.
* Parses reference MGF files.
* Supports both NEG and POS ion modes.
* Extracts:

  * feature ID
  * precursor m/z
  * retention time
  * MS2 peaks
  * reference compound name
  * formula
  * adduct
  * SMILES
  * metadata

### Database

The project stores:

* reference libraries
* reference spectra
* reference peaks
* unknown samples
* unknown features
* unknown spectra
* unknown peaks
* match results

### Matching

The current matching system supports:

* m/z matching with ppm tolerance
* candidate reduction by best ppm error
* NEG samples matched only with NEG references
* POS samples matched only with POS references
* MS2 cosine similarity scoring
* retention time comparison
* overall candidate score
* confidence level assignment

### API Endpoints

Current main endpoints:

```text
GET  /health/
POST /reference/upload-mgf
POST /samples/upload
POST /matching/run/{sample_id}
POST /matching/score-ms2/{sample_id}
GET  /matching/ranked-results/{sample_id}
GET  /matching/summary/{sample_id}
GET  /matching/export-csv/{sample_id}
GET  /molecules/describe?smiles={smiles}
POST /molecules/describe
```

Celery-style task endpoints:

```text
POST /matching/run-task/{sample_id}
POST /matching/score-ms2-task/{sample_id}
```

These currently run in Celery eager mode. Real Redis/Celery background processing can be added later.

## Recommended API Workflow

1. Upload reference NEG MGF file.
2. Upload reference POS MGF file.
3. Upload unknown NEG CSV + MGF files.
4. Upload unknown POS CSV + MGF files.
5. Run m/z matching.
6. Run MS2 scoring.
7. View ranked results.
8. View matching summary.
9. Export ranked results as CSV.

Example workflow:

```text
POST /reference/upload-mgf
POST /samples/upload
POST /matching/run/1
POST /matching/score-ms2/1
GET  /matching/ranked-results/1
GET  /matching/summary/1
GET  /matching/export-csv/1
```

Molecule descriptor endpoint:

```text
GET /molecules/describe?smiles=CCO
```

or:

```json
{
  "smiles": "CCO"
}
```

## Local Setup

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment on Windows:

```bash
.\venv\Scripts\Activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create database tables:

```bash
python -m scripts.create_db
```

Run FastAPI:

```bash
python -m uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Local Data Structure

Example local data organization:

```text
data/
├── reference/
│   ├── neg/
│   │   └── 20241003_enamdisc_neg_ms2.mgf
│   └── pos/
│       └── 20241003_enamdisc_pos_ms2.mgf
└── unknown/
    ├── neg/
    │   ├── NEG_fbmn.mgf
    │   └── NEG_fbmn_quant.csv
    └── pos/
        ├── POS_fbmn.mgf
        └── POS_fbmn_quant.csv
```

Important:

```text
data/
uploads/
lcms.db
```

should not be committed to GitHub.

## Current Confidence Logic

The current confidence logic is preliminary.

Current labels include:

```text
L4
MZ_RT_CANDIDATE
MZ_ONLY_CANDIDATE
NO_CONFIDENT_MATCH
```

Current logic:

* `L4`: MS2-supported candidate
* `MZ_RT_CANDIDATE`: m/z and retention time support
* `MZ_ONLY_CANDIDATE`: m/z support only
* `NO_CONFIDENT_MATCH`: insufficient evidence

## Final Target Confidence Levels

The planned confidence levels are:

```text
L1: RT or RI + m/z + molecular formula + adducts + MS2 spectra
L2: m/z + molecular formula + adducts + MS2 spectra
L3: molecular formula + MS2 spectra
L4: MS2 spectra only
L5: molecular formula only
```

## Things Still To Add

### 1. Formula Matching

Current status:

* Reference MGF contains formula.
* Unknown CSV/MGF does not clearly contain formula.

To add:

* Extract molecular formula from unknown annotations if available.
* Compare unknown formula with reference formula.
* Add `formula_match` to ranked results.
* Use formula matching in confidence levels.

### 2. Adduct Matching

Current status:

* Reference MGF contains adduct information.
* Unknown CSV has columns such as `best ion`, but values may be empty.

To add:

* Extract unknown adduct or best ion from MZmine export if available.
* Compare unknown adduct with reference adduct.
* Add `adduct_match` to ranked results.
* Use adduct matching in confidence levels.

### 3. Retention Index Calculation

Current status:

* Retention time scoring is implemented.
* Retention index calculation is not implemented yet.

To add:

* Add calibration compound table.
* Store known retention times and retention indexes.
* Calculate retention index for unknown features.
* Allow user to choose RT or RI matching.
* Use RI in confidence level L1 when available.

### 4. Real Celery + Redis Background Processing

Current status:

* Celery task structure exists.
* Celery runs in eager mode.
* Redis/Docker is not yet configured.

To add:

* Install Docker or Redis.
* Run Redis server.
* Set `CELERY_TASK_ALWAYS_EAGER=false`.
* Start Celery worker.
* Use async task status endpoint.
* Process large MS2 scoring jobs in background.

### 5. PostgreSQL Support

Current status:

* SQLite is used for development.

To add:

* Configure PostgreSQL.
* Add database migration system with Alembic.
* Move large LC-MS data from SQLite to PostgreSQL.
* Add indexes for faster matching.

### 6. Better MS2 Similarity

Current status:

* Basic cosine similarity is implemented.

To add:

* Improve MS2 scoring with MatchMS.
* Add peak filtering.
* Add normalization.
* Add minimum matched peak count.
* Add library comparison settings.
* Compare results with supervisor’s expected scientific thresholds.

### 7. Better Ranking System

Current status:

* Ranking uses m/z score, MS2 score, and retention time score.

To add:

* Include formula score.
* Include adduct score.
* Include RI score.
* Create final weighted score.
* Allow configurable thresholds.

### 8. Validation and Error Handling

To add:

* Better validation for uploaded files.
* Detect missing columns in CSV.
* Detect invalid MGF files.
* Prevent duplicate uploads.
* Return clear API errors.
* Add sample status information.

### 9. Tests

To add:

* Unit tests for CSV parser.
* Unit tests for MGF parser.
* Unit tests for m/z matching.
* Unit tests for MS2 scoring.
* Unit tests for confidence levels.
* API endpoint tests.

### 10. Documentation

To add:

* API usage examples.
* Example Swagger workflow.
* Explanation of matching logic.
* Explanation of confidence levels.
* Known limitations.
* Screenshots of Swagger results.
* Internship progress notes.

### 11. Optional Frontend

Optional future frontend features:

* Upload reference files.
* Upload unknown samples.
* Start matching jobs.
* View ranked candidates.
* Filter by confidence level.
* Download CSV results.
* View MS2 scores and metadata.

## Current Limitations

* Unknown formula and adduct information are not clearly available in the current unknown sample files.
* Retention index is not implemented yet.
* Celery is currently in eager mode, not real background mode.
* SQLite may be slow for very large datasets.
* MS2 scoring can be slow without optimized background processing.
* Current confidence logic is preliminary and should be validated with the supervisor.

## Suggested Next Development Order

1. Finish and test all current API endpoints.
2. Add tests for CSV and MGF parsers.
3. Improve MS2 similarity scoring.
4. Add formula/adduct matching if unknown annotations are available.
5. Add retention index calculation.
6. Add PostgreSQL.
7. Add real Celery + Redis.
8. Improve final confidence levels L1-L5.
9. Add final documentation and supervisor demo instructions.
10. Add optional frontend if required.

## Status

The project currently has a working backend MVP that can:

```text
upload CSV/MGF files
store LC-MS data
match unknown features by m/z
score MS2 similarity
calculate ranked candidates
return summaries
export CSV results
```

The remaining work is mainly focused on scientific completeness, production-level processing, and final documentation.
