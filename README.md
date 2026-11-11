# Cross-Language Semantic Code Clone Detector

A Python / React application that compares source files across C, C++, Rust, and Fortran using compiler-generated LLVM IR, program-structure representations, control-flow / data-flow graphs, graph fingerprints, and heuristic similarity features.

> **Project status:** Proof of concept / research prototype. A compiler-backed path exists, but similarity scores still combine handcrafted structural and token-based features. They should not be presented as a validated measure of semantic equivalence for arbitrary programs.

## What is implemented

- Language detection for C, C++, Rust, and Fortran source files.
- Compiler discovery for Clang, Clang++, Flang, and Rustc, followed by real compilation to LLVM IR when the relevant toolchain is installed.
- LLVM IR parsing / normalisation and control-flow / data-flow graph construction.
- Weisfeiler–Lehman graph fingerprinting and serialised graph views.
- Structural Program Representation (SPR) and feature extraction for intent, entities, behaviour patterns, and operation pipelines.
- Pairwise and multi-file comparison, graph visualisation, comparison history, and evaluation pages.
- FastAPI endpoints for comparison, analysis, status, test cases, evaluation, and visualisation.
- A React / TypeScript / Vite interface.
- Optional model encoders with deterministic local fallback behaviour when a model cannot be loaded; the main similarity engine also contains its own handcrafted vectorisation logic.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| API | Python, FastAPI, Uvicorn, Pydantic |
| Compilation | Clang, Clang++, Flang, Rustc |
| IR / graph analysis | LLVM IR, NetworkX, CFG / DFG, Weisfeiler–Lehman hashing |
| Similarity | SPR features, structural scores, token-based vectorisation, heuristic rules |
| Optional encoders | Hugging Face Transformers model adapters |

## Architecture

```text
React / Vite client
  │
  ▼
FastAPI API
  │
  ▼
Compiler pipeline
  ├── Clang / Clang++ / Flang / Rustc
  └── LLVM IR validation
       │
       ▼
IR parsing and normalisation
       │
       ├── CFG / DFG construction
       ├── graph fingerprints
       └── SPR feature extraction
                │
                ▼
       staged similarity / classification
                │
                ▼
       comparison report + graph data
```

## Repository map

- `backend/` — FastAPI API routes, configuration, comparison pipeline, and report storage.
- `src/compiler/` — compiler discovery, wrappers, and LLVM IR validation.
- `src/ir/` — IR parsing and normalisation.
- `src/graph/` — CFG / DFG building and graph fingerprints.
- `src/semantic/` — behaviour, purpose, entity, and transformation features.
- `src/evaluation/` — benchmark runner, metrics, and baseline comparisons.
- `frontend/` — current React / Vite web dashboard.
- `src/frontend/` — a second frontend tree with overlapping / older UI files; compare before changing both.
- `testcases/`, `evaluation/` — sample source pairs and evaluation data.
- `scripts/` — compiler toolchain checks and setup helpers.

## Run locally

Requirements: Python 3.10+, Node.js 18+, npm, and the matching language compiler toolchains. For the full cross-language path, install and make available in PATH:

- Clang and Clang++ (LLVM).
- Flang for Fortran.
- Rustc for Rust.

Install backend dependencies from the repository root:

```bash
python -m venv .venv
# Activate the environment
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend is normally served on port `5173`; the API documentation is available at `http://127.0.0.1:8000/docs`.

Windows users can inspect `build.bat` and `run.bat`; Linux/macOS users can inspect `build.sh` and `run.sh`. Confirm the scripts against the current directory layout before use.

## Evaluation

The repository includes benchmark and evaluation utilities under `src/evaluation/`, evaluation cases under `evaluation/`, and generated result files. Treat any existing accuracy / score values as results from the included test set only. Re-run the suite on unseen programs and compare against token / text / AST baselines before making general performance claims.

## Limitations

- Real LLVM IR generation depends on installed native toolchains. Compiler detection and compilation failures should be treated as failures, not silently interpreted as correct semantic analysis.
- The repository also contains fallback / synthetic code paths and model-vector fallbacks. Verify which path was used when interpreting an individual comparison.
- The current main similarity engine includes handcrafted token-vector and weighted feature logic; it is not equivalent to a fully trained semantic model.
- Graph similarity and inferred intent do not prove that two programs are functionally equivalent.
- Sample-specific score adjustments / heuristics should be disclosed when presenting results.
- The repository contains duplicated frontend trees and generated / local artifacts (including a committed virtual environment). Keep generated environments, model caches, and build outputs out of future commits.
- The available tests and evaluation data do not replace a broad, independently labelled benchmark.

## License

See repository license and the licences for compiler, model, and frontend dependencies.
