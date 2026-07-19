"use client";

import { FormEvent, useMemo, useState } from "react";

type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

type MatchRow = {
  match_id: number;
  ion_mode: string;
  confidence_level: string | null;
  ppm_error: number;
  mz_error: number;
  unknown: {
    feature_id: string | number;
    mz: number;
    retention_time_minutes: number | null;
  };
  reference: {
    spectrum_id: number;
    name: string | null;
    formula: string | null;
    adduct: string | null;
    precursor_mz: number;
    retention_time_minutes: number | null;
    smiles: string | null;
  };
};

type MatchingResults = {
  sample_id: number;
  count: number;
  results: MatchRow[];
};

type MoleculeDescription = {
  input_smiles: string;
  canonical_smiles: string;
  formula: string;
  exact_molecular_weight: number;
  molecular_weight: number;
  formal_charge: number;
  atom_count: number;
  heavy_atom_count: number;
  bond_count: number;
  ring_count: number;
  aromatic_ring_count: number;
  h_bond_donors: number;
  h_bond_acceptors: number;
  rotatable_bonds: number;
  tpsa: number;
  logp: number;
  molar_refractivity: number;
  fraction_csp3: number;
  qed: number;
  atom_composition: Record<string, number>;
  lipinski_rule_of_five: {
    molecular_weight_ok: boolean;
    logp_ok: boolean;
    h_bond_donors_ok: boolean;
    h_bond_acceptors_ok: boolean;
    violations: number;
  };
};

const defaultApiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return Number.isInteger(value) ? value.toString() : value.toFixed(4);
  return String(value);
}

function ResultBlock({ data }: { data: unknown }) {
  if (!data) return null;

  return (
    <pre className="max-h-72 overflow-auto rounded-md border border-slate-200 bg-slate-950 p-4 text-xs leading-5 text-slate-100">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function StatusPill({ tone, children }: { tone: "ready" | "busy" | "error"; children: React.ReactNode }) {
  const classes = {
    ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
    busy: "border-amber-200 bg-amber-50 text-amber-700",
    error: "border-rose-200 bg-rose-50 text-rose-700",
  };

  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-1 text-xs font-medium ${classes[tone]}`}>
      {children}
    </span>
  );
}

export default function Home() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sampleUploadResult, setSampleUploadResult] = useState<JsonValue | null>(null);
  const [referenceUploadResult, setReferenceUploadResult] = useState<JsonValue | null>(null);
  const [moleculeResult, setMoleculeResult] = useState<MoleculeDescription | null>(null);
  const [operationResult, setOperationResult] = useState<JsonValue | null>(null);
  const [matchingResults, setMatchingResults] = useState<MatchingResults | null>(null);
  const [rankedResults, setRankedResults] = useState<JsonValue | null>(null);
  const [summary, setSummary] = useState<JsonValue | null>(null);
  const [sampleId, setSampleId] = useState("1");
  const [sampleName, setSampleName] = useState("");
  const [sampleIonMode, setSampleIonMode] = useState("NEG");
  const [referenceLibrary, setReferenceLibrary] = useState("");
  const [referenceIonMode, setReferenceIonMode] = useState("NEG");
  const [smiles, setSmiles] = useState("");
  const [ppmTolerance, setPpmTolerance] = useState("10");
  const [maxCandidates, setMaxCandidates] = useState("5");
  const [mzTolerance, setMzTolerance] = useState("0.02");
  const [minMs2Score, setMinMs2Score] = useState("0.7");
  const [limit, setLimit] = useState("1000");

  const cleanBase = useMemo(() => apiBase.replace(/\/+$/, ""), [apiBase]);

  async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
    setError(null);
    const response = await fetch(`${cleanBase}${path}`, options);
    const text = await response.text();
    const payload = text ? JSON.parse(text) : null;

    if (!response.ok || payload?.error) {
      throw new Error(payload?.detail ?? payload?.error ?? `Request failed with ${response.status}`);
    }

    return payload as T;
  }

  async function runAction<T>(key: string, action: () => Promise<T>, onSuccess: (data: T) => void) {
    setBusy(key);
    setError(null);

    try {
      const data = await action();
      onSuccess(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unexpected request failure");
    } finally {
      setBusy(null);
    }
  }

  async function uploadSample(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const csv = form.elements.namedItem("csv_file") as HTMLInputElement;
    const mgf = form.elements.namedItem("mgf_file") as HTMLInputElement;
    const body = new FormData();

    body.append("sample_name", sampleName);
    body.append("ion_mode", sampleIonMode);
    if (csv.files?.[0]) body.append("csv_file", csv.files[0]);
    if (mgf.files?.[0]) body.append("mgf_file", mgf.files[0]);

    await runAction("sample-upload", () => requestJson<JsonValue>("/samples/upload", { method: "POST", body }), setSampleUploadResult);
  }

  async function uploadReference(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const file = form.elements.namedItem("reference_file") as HTMLInputElement;
    const body = new FormData();

    body.append("library_name", referenceLibrary);
    body.append("ion_mode", referenceIonMode);
    if (file.files?.[0]) body.append("file", file.files[0]);

    await runAction("reference-upload", () => requestJson<JsonValue>("/reference/upload-mgf", { method: "POST", body }), setReferenceUploadResult);
  }

  async function describeMolecule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(
      "molecule",
      () =>
        requestJson<MoleculeDescription>("/molecules/describe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ smiles }),
        }),
      setMoleculeResult,
    );
  }

  async function exportCsv() {
    setBusy("export");
    setError(null);

    try {
      const params = new URLSearchParams({
        ppm_tolerance: ppmTolerance,
        ms2_threshold: minMs2Score,
        limit,
      });
      const response = await fetch(`${cleanBase}/matching/export-csv/${sampleId}?${params}`);

      if (!response.ok) {
        throw new Error(`CSV export failed with ${response.status}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `sample_${sampleId}_ranked_results.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "CSV export failed");
    } finally {
      setBusy(null);
    }
  }

  const operationParams = new URLSearchParams({
    ppm_tolerance: ppmTolerance,
    max_candidates_per_feature: maxCandidates,
  });
  const scoringParams = new URLSearchParams({
    mz_tolerance: mzTolerance,
    min_ms2_score: minMs2Score,
    limit,
  });

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-teal-700">LC-MS identification</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-normal text-slate-950">API Workbench</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Upload libraries and samples, run candidate matching, score MS2 spectra, inspect ranked hits, and export CSV reports.
            </p>
          </div>
          <label className="flex w-full max-w-xl flex-col gap-2 text-sm font-medium text-slate-700">
            Backend URL
            <input
              className="h-11 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100"
              value={apiBase}
              onChange={(event) => setApiBase(event.target.value)}
              placeholder="http://localhost:8000"
            />
          </label>
        </header>

        <section className="flex flex-wrap items-center gap-3 rounded-md border border-slate-200 bg-white px-4 py-3">
          <StatusPill tone={busy ? "busy" : error ? "error" : "ready"}>{busy ? "Request running" : error ? "Request failed" : "Ready"}</StatusPill>
          {error ? <span className="text-sm text-rose-700">{error}</span> : <span className="text-sm text-slate-600">Connected target: {cleanBase}</span>}
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
          <section className="space-y-6">
            <form onSubmit={uploadSample} className="rounded-md border border-slate-200 bg-white p-5">
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Unknown Sample</h2>
                  <p className="mt-1 text-sm text-slate-600">POST /samples/upload</p>
                </div>
                <button className="h-10 rounded-md bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:opacity-50" disabled={busy === "sample-upload"}>
                  Upload
                </button>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm font-medium text-slate-700">
                  Sample name
                  <input className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" required value={sampleName} onChange={(event) => setSampleName(event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Ion mode
                  <select className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 outline-none focus:border-teal-600" value={sampleIonMode} onChange={(event) => setSampleIonMode(event.target.value)}>
                    <option>NEG</option>
                    <option>POS</option>
                  </select>
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Quant CSV
                  <input name="csv_file" type="file" accept=".csv" required className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-slate-700" />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  MS2 MGF
                  <input name="mgf_file" type="file" accept=".mgf" required className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-slate-700" />
                </label>
              </div>
              <div className="mt-4">
                <ResultBlock data={sampleUploadResult} />
              </div>
            </form>

            <form onSubmit={uploadReference} className="rounded-md border border-slate-200 bg-white p-5">
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Reference Library</h2>
                  <p className="mt-1 text-sm text-slate-600">POST /reference/upload-mgf</p>
                </div>
                <button className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-50" disabled={busy === "reference-upload"}>
                  Import
                </button>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm font-medium text-slate-700">
                  Library name
                  <input className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" required value={referenceLibrary} onChange={(event) => setReferenceLibrary(event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Ion mode
                  <select className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 outline-none focus:border-teal-600" value={referenceIonMode} onChange={(event) => setReferenceIonMode(event.target.value)}>
                    <option>NEG</option>
                    <option>POS</option>
                  </select>
                </label>
                <label className="text-sm font-medium text-slate-700 sm:col-span-2">
                  Reference MGF
                  <input name="reference_file" type="file" accept=".mgf" required className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-slate-700" />
                </label>
              </div>
              <div className="mt-4">
                <ResultBlock data={referenceUploadResult} />
              </div>
            </form>

            <form onSubmit={describeMolecule} className="rounded-md border border-slate-200 bg-white p-5">
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Molecule Descriptor</h2>
                  <p className="mt-1 text-sm text-slate-600">POST /molecules/describe</p>
                </div>
                <button className="h-10 rounded-md bg-teal-700 px-4 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:opacity-50" disabled={busy === "molecule"}>
                  Describe
                </button>
              </div>
              <label className="text-sm font-medium text-slate-700">
                SMILES
                <input className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 font-mono text-sm outline-none focus:border-teal-600" required value={smiles} onChange={(event) => setSmiles(event.target.value)} placeholder="CC(=O)OC1=CC=CC=C1C(=O)O" />
              </label>
              {moleculeResult ? (
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  {[
                    ["Formula", moleculeResult.formula],
                    ["Exact mass", moleculeResult.exact_molecular_weight],
                    ["LogP", moleculeResult.logp],
                    ["TPSA", moleculeResult.tpsa],
                    ["QED", moleculeResult.qed],
                    ["Lipinski violations", moleculeResult.lipinski_rule_of_five.violations],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
                      <p className="mt-1 text-base font-semibold text-slate-950">{formatValue(value)}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </form>
          </section>

          <section className="space-y-6">
            <div className="rounded-md border border-slate-200 bg-white p-5">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-slate-950">Matching Controls</h2>
                <p className="mt-1 text-sm text-slate-600">Run matching, score MS2 data, view results, and export CSV for a sample.</p>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                <label className="text-sm font-medium text-slate-700">
                  Sample ID
                  <input className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" value={sampleId} onChange={(event) => setSampleId(event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  ppm tolerance
                  <input type="number" step="0.1" className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" value={ppmTolerance} onChange={(event) => setPpmTolerance(event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Max candidates
                  <input type="number" className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" value={maxCandidates} onChange={(event) => setMaxCandidates(event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  m/z tolerance
                  <input type="number" step="0.01" className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" value={mzTolerance} onChange={(event) => setMzTolerance(event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Min MS2 score
                  <input type="number" step="0.05" min="0" max="1" className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" value={minMs2Score} onChange={(event) => setMinMs2Score(event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Limit
                  <input type="number" className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-teal-600" value={limit} onChange={(event) => setLimit(event.target.value)} />
                </label>
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                <button className="h-10 rounded-md bg-teal-700 px-3 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50" disabled={busy === "run"} onClick={() => runAction("run", () => requestJson<JsonValue>(`/matching/run/${sampleId}?${operationParams}`, { method: "POST" }), setOperationResult)}>
                  Run matching
                </button>
                <button className="h-10 rounded-md bg-slate-900 px-3 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50" disabled={busy === "score"} onClick={() => runAction("score", () => requestJson<JsonValue>(`/matching/score-ms2/${sampleId}?${scoringParams}`, { method: "POST" }), setOperationResult)}>
                  Score MS2
                </button>
                <button className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-50" disabled={busy === "run-task"} onClick={() => runAction("run-task", () => requestJson<JsonValue>(`/matching/run-task/${sampleId}?${operationParams}`, { method: "POST" }), setOperationResult)}>
                  Queue matching
                </button>
                <button className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50 disabled:opacity-50" disabled={busy === "score-task"} onClick={() => runAction("score-task", () => requestJson<JsonValue>(`/matching/score-ms2-task/${sampleId}?${scoringParams}`, { method: "POST" }), setOperationResult)}>
                  Queue MS2
                </button>
              </div>
              <div className="mt-4">
                <ResultBlock data={operationResult} />
              </div>
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-5">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Results</h2>
                  <p className="mt-1 text-sm text-slate-600">Fetch result tables and matching summary.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50" onClick={() => runAction("results", () => requestJson<MatchingResults>(`/matching/results/${sampleId}?limit=100`), setMatchingResults)}>
                    Results
                  </button>
                  <button className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50" onClick={() => runAction("ranked", () => requestJson<JsonValue>(`/matching/ranked-results/${sampleId}?limit_features=50&candidates_per_feature=3`), setRankedResults)}>
                    Ranked
                  </button>
                  <button className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-800 hover:bg-slate-50" onClick={() => runAction("summary", () => requestJson<JsonValue>(`/matching/summary/${sampleId}?ppm_tolerance=${ppmTolerance}&ms2_threshold=${minMs2Score}&top_limit=10`), setSummary)}>
                    Summary
                  </button>
                  <button className="h-10 rounded-md bg-teal-700 px-3 text-sm font-semibold text-white hover:bg-teal-800" onClick={exportCsv}>
                    Export CSV
                  </button>
                </div>
              </div>

              {matchingResults?.results?.length ? (
                <div className="overflow-x-auto rounded-md border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
                      <tr>
                        <th className="px-3 py-2">Feature</th>
                        <th className="px-3 py-2">Reference</th>
                        <th className="px-3 py-2">Formula</th>
                        <th className="px-3 py-2">Adduct</th>
                        <th className="px-3 py-2">ppm</th>
                        <th className="px-3 py-2">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white">
                      {matchingResults.results.map((row) => (
                        <tr key={row.match_id} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-mono text-xs">{formatValue(row.unknown.feature_id)}</td>
                          <td className="max-w-64 truncate px-3 py-2">{formatValue(row.reference.name)}</td>
                          <td className="px-3 py-2">{formatValue(row.reference.formula)}</td>
                          <td className="px-3 py-2">{formatValue(row.reference.adduct)}</td>
                          <td className="px-3 py-2">{formatValue(row.ppm_error)}</td>
                          <td className="px-3 py-2">{formatValue(row.confidence_level)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : matchingResults ? (
                <p className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">No matches returned for sample {matchingResults.sample_id}.</p>
              ) : null}

              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                <div>
                  <p className="mb-2 text-sm font-semibold text-slate-700">Ranked payload</p>
                  <ResultBlock data={rankedResults} />
                </div>
                <div>
                  <p className="mb-2 text-sm font-semibold text-slate-700">Summary payload</p>
                  <ResultBlock data={summary} />
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
