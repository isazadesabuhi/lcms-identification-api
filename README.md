# LC-MS Compound Identification

A FastAPI backend and Next.js frontend for identifying unknown compounds from LC-MS data. Raw `.mzML` files are processed in MZmine first; this application imports the resulting quantification CSV and MS/MS MGF files, matches unknown features against an MGF reference library, scores candidates, and exports ranked results.

```text
mzML -> MZmine -> CSV + MGF -> API -> m/z matching -> MS2 scoring -> ranked candidates
```

## Stack and features

- FastAPI, SQLAlchemy, and SQLite
- Next.js 16 and React 19 frontend/API workbench
- MZmine/GNPS CSV and MGF parsing in positive (`POS`) and negative (`NEG`) ion modes
- ppm-based precursor matching, MS2 cosine similarity, retention-time scoring, and candidate ranking
- RDKit descriptors from SMILES
- CSV result export
- Celery task wrappers (configured to run eagerly by default)

## Run locally

Prerequisites: Python 3.11, Node.js with npm, and Windows PowerShell (the activation command below also includes a POSIX alternative).

### 1. Backend

From the repository root:

```powershell
python -m venv venv
```

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

On macOS/Linux, use `source venv/bin/activate` instead. Then install the Python dependencies, initialize the database, and start the API:

```powershell
python -m pip install -r requirements.txt
python -m scripts.create_db
python -m uvicorn app.main:app --reload
```

The backend is available at `http://localhost:8000`. Interactive API documentation is at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

By default the backend uses `sqlite:///./lcms.db`, saves uploaded files below `uploads/`, permits local frontend origins on ports 3000 and 3001, and executes Celery tasks eagerly. These settings can be overridden in a root `.env` file:

```dotenv
DATABASE_URL=sqlite:///./lcms.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_ALWAYS_EAGER=true
```

Redis and a separate Celery worker are not required while `CELERY_TASK_ALWAYS_EAGER=true`.

### 2. Frontend

Keep the backend running. Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend defaults to `http://localhost:8000` as its API base URL. To use another backend URL, create `frontend/.env.local` before starting the frontend:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

For a production-style frontend run:

```powershell
npm run build
npm start
```

## Recommended workflow

1. Upload a reference MGF for each ion mode you use.
2. Upload an unknown sample's quant CSV and MS2 MGF; save the returned `sample_id`.
3. Run precursor m/z matching for that sample.
4. Score the resulting candidates against the MS2 spectra.
5. Inspect raw results, ranked results, or a summary.
6. Export the ranked candidates as CSV.

The frontend exposes this workflow in one page. It can also be performed through Swagger or with the request examples below.

## API endpoints

All URLs below are relative to `http://localhost:8000`. There is currently no authentication.

### Health and status

#### `GET /health/`

Checks whether the API is running. Returns `{"status":"ok"}`.

#### `GET /samples/`

Checks whether the samples router is available. This is a route-status check; it does not list imported samples.

### Reference library

#### `POST /reference/upload-mgf`

Imports a reference library from an MGF file. The request uses `multipart/form-data`.

| Field | Required | Description |
| --- | --- | --- |
| `ion_mode` | Yes | `NEG` or `POS` (case-insensitive) |
| `file` | Yes | Reference file ending in `.mgf` |
| `library_name` | No | Display name; generated from the file and ion mode when omitted |

```bash
curl -X POST http://localhost:8000/reference/upload-mgf \
  -F "ion_mode=NEG" \
  -F "library_name=ENAMDISC negative" \
  -F "file=@data/reference/neg/reference.mgf"
```

The response reports the stored file, library identifiers, and imported spectrum/peak counts.

### Unknown samples

#### `POST /samples/upload`

Imports one unknown sample from a MZmine/GNPS quant CSV and its corresponding MGF. The request uses `multipart/form-data`.

| Field | Required | Description |
| --- | --- | --- |
| `ion_mode` | Yes | `NEG` or `POS` (case-insensitive) |
| `csv_file` | Yes | Quantification file ending in `.csv` |
| `mgf_file` | Yes | MS2 file ending in `.mgf` |
| `sample_name` | No | Display name; generated from the CSV name and ion mode when omitted |

```bash
curl -X POST http://localhost:8000/samples/upload \
  -F "ion_mode=NEG" \
  -F "sample_name=Unknown extract" \
  -F "csv_file=@data/unknown/neg/NEG_fbmn_quant.csv" \
  -F "mgf_file=@data/unknown/neg/NEG_fbmn.mgf"
```

Use the returned `sample_id` in the matching endpoints.

### Matching and scoring

#### `POST /matching/run/{sample_id}`

Runs precursor m/z matching synchronously. Only references with the sample's ion mode are considered.

| Query parameter | Default | Validation | Description |
| --- | ---: | --- | --- |
| `ppm_tolerance` | `10.0` | greater than 0 | Maximum precursor mass error in ppm |
| `max_candidates_per_feature` | `5` | 1-50 | Maximum candidates retained per feature |

```bash
curl -X POST "http://localhost:8000/matching/run/1?ppm_tolerance=10&max_candidates_per_feature=5"
```

#### `POST /matching/score-ms2/{sample_id}`

Scores existing matches against the sample's MS2 spectra synchronously.

| Query parameter | Default | Validation | Description |
| --- | ---: | --- | --- |
| `mz_tolerance` | `0.02` | greater than 0 | Fragment peak matching tolerance |
| `min_ms2_score` | `0.7` | 0-1 | Threshold used for MS2-supported confidence |
| `limit` | `1000` | greater than 0 | Maximum matches to score; omit the parameter to use the default |

```bash
curl -X POST "http://localhost:8000/matching/score-ms2/1?mz_tolerance=0.02&min_ms2_score=0.7&limit=1000"
```

#### `POST /matching/run-task/{sample_id}`

Celery-wrapped version of m/z matching. It accepts the same `ppm_tolerance` and `max_candidates_per_feature` parameters as `/matching/run/{sample_id}`. With the default eager configuration, it runs during the request and returns the task ID and result immediately.

#### `POST /matching/score-ms2-task/{sample_id}`

Celery-wrapped version of MS2 scoring. It accepts the same `mz_tolerance`, `min_ms2_score`, and `limit` parameters as `/matching/score-ms2/{sample_id}`. With the default eager configuration, it also returns its result immediately.

### Results

#### `GET /matching/results/{sample_id}`

Returns raw matches ordered by ascending ppm error, including unknown feature and reference spectrum details.

| Query parameter | Default | Validation |
| --- | ---: | --- |
| `limit` | `50` | 1-500 |

#### `GET /matching/ranked-results/{sample_id}`

Groups matches by unknown feature and returns ranked candidates.

| Query parameter | Default | Validation |
| --- | ---: | --- |
| `limit_features` | `50` | 1-500 |
| `candidates_per_feature` | `3` | 1-20 |

#### `GET /matching/summary/{sample_id}`

Returns aggregate match counts and the top candidates for a sample.

| Query parameter | Default | Validation |
| --- | ---: | --- |
| `ppm_tolerance` | `10.0` | greater than 0 |
| `ms2_threshold` | `0.7` | 0-1 |
| `top_limit` | `10` | 1-100 |

#### `GET /matching/export-csv/{sample_id}`

Downloads ranked results as `sample_{sample_id}_ranked_results.csv`.

| Query parameter | Default | Validation |
| --- | ---: | --- |
| `ppm_tolerance` | `10.0` | greater than 0 |
| `ms2_threshold` | `0.7` | 0-1 |
| `limit` | `1000` | 1-10000 |

```bash
curl -o sample_1_ranked_results.csv \
  "http://localhost:8000/matching/export-csv/1?ppm_tolerance=10&ms2_threshold=0.7&limit=1000"
```

### Molecule descriptors

Both descriptor endpoints return RDKit-derived physicochemical properties, atom composition, QED, and Lipinski Rule-of-Five results. Invalid SMILES return HTTP `400`.

#### `GET /molecules/describe`

Requires a non-empty `smiles` query parameter:

```bash
curl --get http://localhost:8000/molecules/describe --data-urlencode "smiles=CCO"
```

#### `POST /molecules/describe`

Accepts JSON:

```bash
curl -X POST http://localhost:8000/molecules/describe \
  -H "Content-Type: application/json" \
  -d '{"smiles":"CCO"}'
```

## Example data layout

```text
data/
├── reference/
│   ├── neg/reference.mgf
│   └── pos/reference.mgf
└── unknown/
    ├── neg/
    │   ├── NEG_fbmn.mgf
    │   └── NEG_fbmn_quant.csv
    └── pos/
        ├── POS_fbmn.mgf
        └── POS_fbmn_quant.csv
```

Runtime data (`data/`, `uploads/`, and `lcms.db`) should remain outside version control.

## Confidence labels and limitations

Current result labels are `L4` (MS2-supported), `MZ_RT_CANDIDATE`, `MZ_ONLY_CANDIDATE`, and `NO_CONFIDENT_MATCH`. This confidence logic is preliminary. Formula/adduct matching and retention-index calculation are not yet implemented, MS2 scoring uses a basic cosine similarity, Celery runs eagerly by default, and SQLite may be unsuitable for very large datasets.
