# CodeCrunch

A Python tool for analyzing code structure, dependency graphs, and generating compressed codebase overview artifacts.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python run_pipeline.py <path-to-repo>
```

Example (analyze the sample repo):

```bash
python run_pipeline.py sample_repo
```

If no path is given, defaults to `sample_repo`.

## Project Structure

| Module | Purpose |
|--------|---------|
| `parser.py` | Parses Python files with tree-sitter; extracts functions, classes, and imports |
| `ingestion.py` | Walks repo directories, respects `.gitignore`, collects Python files |
| `import_analyzer.py` | Resolves imports to internal files; builds dependency graph |
| `artifact.py` | Defines the `.codecrunch` XML format; builds, saves, and loads artifacts |
| `summarizer.py` | Prompt template and pipeline for LLM summarization (mock mode for Phase 1) |

## Phase Status

Phase 1 complete: parser, ingestion, import analyzer, artifact schema (XML `.codecrunch`), summarizer spike (mock summaries).

Phase 2 complete: multi-language ingestion (py/js/ts), JS/TS parsing (tree-sitter), JS/TS dependency graph resolution (relative + require best-effort), AST structural hashing + clustering (pattern detection), artifact assembler pipeline, batching + on-disk summary cache (mock-only), token counting (heuristic + optional `tiktoken`), fixtures + tests.

Notes:
- The summarizer cache is written to `.codecrunch_summaries_cache.json` at the analyzed repo root (best-effort; cache failures do not break the pipeline).
- Token metrics are reported as raw included source tokens vs artifact tokens.

## Phase 3 (Hunter) — Plugin & CLI

Done when: VS Code extension works end-to-end on a local repo.

To do:
1. Build CLI tool: `codecrunch <path>` or `codecrunch <github-url>` outputs `.codecrunch` artifact
2. Build VS Code extension scaffold: reads `.codecrunch`, injects context before AI query
3. Integrate with VS Code AI context API (or prepend to prompt as fallback)
4. Run full pipeline on 3 demo repos, fix bugs, tune compression to reliably hit <10K tokens on ~50-file repos
5. Write benchmarking harness: 5 questions x 4 conditions (naive / RAG / Repomix / CodeCrunch)