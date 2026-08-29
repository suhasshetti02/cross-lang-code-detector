# Project Audit Report: Cross-Language Semantic Code Clone Detector

## 1. Current Architecture
The application is a full-stack tool with a React/Vite frontend and a FastAPI backend.
The core clone detection pipeline (`StrictSemanticSimilarityEngine`) processes source files through the following stages:
1. **Compilation**: Wrappers attempt to compile C/C++/Rust/Fortran into LLVM IR.
2. **Normalization**: `IRNormalizer` strips boilerplate and sanitizes variable names.
3. **Graph Construction**: Extracts Basic Blocks to build a Control Flow Graph (CFG) and Data Flow Graph (DFG).
4. **Semantic Extraction**: `IntentDetector` and `SPRBuilder` analyze the original source code text and filename to guess the algorithm (e.g., Fibonacci, Sorting).
5. **Scoring**: A weighted sum combines 10 metrics to produce the final clone score.

## 2. Actual Data Flow (POST `/similarity` or `/compare`)
1. User uploads `file_a` and `file_b`.
2. The `CloneDetectionPipeline` routes them to `StrictSemanticSimilarityEngine.compare_files`.
3. The engine attempts to compile both files to LLVM IR. **If compilation fails (or if the environment lacks compilers), it silently falls back to generating fake LLVM IR strings based on the filename.**
4. The IR is parsed and normalized. `IRNormalizer` replaces almost all local variables with a literal `"VAR"`.
5. CFG and DFG are constructed from this crippled IR.
6. `IntentDetector` analyzes the source code string and filename. If the filename contains "fibonacci", it confidently flags the intent as "Fibonacci".
7. A final score is computed. **Crucially, the CFG and DFG similarities account for only 5% each (10% total) of the final score.** The remaining 90% is derived from source-code string matching, keyword analysis, and filename heuristics.

## 3. Critical Bugs
*   **Data Dependency Destruction**: `IRNormalizer` renames all SSA variables (e.g., `%1`, `%n.addr`) to `"VAR"`. This completely destroys the Def-Use chains required for a genuine DFG. The resulting DFG is structurally meaningless.
*   **Graph Fingerprinting**: WL Hashing is used, but the results are compared using exact equality (`hash_a == hash_b`), which is a binary check and useless for continuous similarity scoring of slightly different IR.
*   **Score Misrepresentation**: The system masquerades as an LLVM IR clone detector while actually functioning as a keyword/filename matcher.

## 4. Hardcoded Logic
*   **Intent Taxonomy (`intent_detector.py`)**: Heavily relies on hardcoded vocabulary lists for 30+ algorithms. For instance, finding the word "swap" grants points toward the "Sorting" intent.
*   **Filename Boosts**: Filenames exactly matching or containing template names (like `factorial.c`) receive a massive +0.95 confidence boost.
*   **Legacy Overrides**: Remnants in `src/similarity/similarity_engine.py` explicitly hardcode scores like `if intent_a == "Fibonacci"... final_score = max(final_score, 88.0)`.

## 5. Mock Components
*   **Fake Compilers (`c_compiler.py`, etc.)**: The `generate_fallback_ir` method contains large, hardcoded blocks of LLVM IR for standard algorithms (Factorial, Fibonacci, Sorting, etc.). If the system runs without real compilers or encounters an error, it silently returns this perfect, fake IR.

## 6. Incorrect Claims
*   **"Semantic LLVM Analysis"**: False. 90% of the scoring relies on NLP and regex over the source code.
*   **"Robust DFG"**: False. Variable normalization destroys data dependencies.
*   **"Weisfeiler-Lehman Graph Matching"**: Misleading. It generates a hash but only does a binary comparison, ignoring structural proximity.

## 7. Missing Components
*   **Opcode Similarity Vectors**: There is no continuous mathematical comparison of instruction frequencies.
*   **Canonical Renaming**: Missing a real SSA canonicalization algorithm (e.g., assigning `%v0`, `%v1` deterministically) to preserve data flow.
*   **Real Continuous Graph Similarity**: Missing Jaccard or Cosine similarity for structural graph features.
*   **Blind Evaluation Mode**: Missing an evaluation pipeline that strips filenames and algorithm hints.

## 8. Recommended Fix Order
1.  **Phase 1 & 12 (Real Compilation & Remove Mock)**: Delete all `generate_fallback_ir` logic. The system must fail loudly if compilation fails.
2.  **Phase 2 & 3 (IR Normalization & Parser)**: Implement deterministic canonical renaming (`%v0`, `%v1`) to preserve Def-Use edges without hardcoding names.
3.  **Phase 4 & 5 (Real CFG/DFG)**: Fix graph builders to use the preserved dependencies.
4.  **Phase 6, 7, 8, 9 (Graph Fingerprinting & Similarity)**: Implement continuous metrics (Cosine/Jaccard) for CFG metrics, DFG metrics, WL feature histograms, and Opcode frequency vectors.
5.  **Phase 10 & 11 (Final Score & Remove Intent)**: Strip all source-code string matching and intent detection from the similarity engine. The final score must be `0.4*CFG + 0.4*DFG + 0.2*Opcode`.
6.  **Phase 13+ (Fortran, Evaluation, Testing)**: Integrate flang, build a blind benchmark dataset, generate precision/recall metrics, and write comprehensive tests.
