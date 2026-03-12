# CodeCrunch

A tool that compresses entire codebases into AI-optimized snapshots that fit inside a single LLM context window. Every AI coding tool today is a flashlight — CodeCrunch is the floodlight.

## Installation

```
pip install -r requirements.txt
```

For the VS Code extension:
```
cd vscode-extension
npm install
npm run compile
```

## Usage

### CLI
```
python -m codecrunch <path-to-repo>
python -m codecrunch <path-to-repo> --verbose
python -m codecrunch <path-to-repo> --output my_artifact.codecrunch
```

### VS Code Extension
1. Generate a `.codecrunch` artifact using the CLI
2. Open the repo in VS Code with the extension installed
3. Extension auto-detects the artifact and loads it
4. Use Command Palette > "CodeCrunch: Copy Context to Clipboard"
5. Paste into any AI chat — the AI now understands your entire codebase

## Project Structure

| Module | Purpose |
|--------|---------|
| `codecrunch/parser.py` | Tree-sitter AST parsing for Python, JavaScript, TypeScript |
| `codecrunch/ingestion.py` | Walks repo directories, respects `.gitignore`, collects source files |
| `codecrunch/import_analyzer.py` | Resolves imports, builds dependency graph |
| `codecrunch/patterns.py` | AST structural hashing + clustering for pattern detection |
| `codecrunch/artifact.py` | Defines `.codecrunch` XML schema; builds, saves, loads artifacts |
| `codecrunch/summarizer.py` | LLM summarization pipeline with mock mode and caching |
| `codecrunch/token_count.py` | Token counting for compression ratio metrics |
| `codecrunch/pipeline.py` | End-to-end pipeline assembler |
| `codecrunch/cli.py` | Click-based CLI interface |
| `vscode-extension/` | VS Code extension for context injection |
| `scripts/demo_setup.py` | Clones demo repos (Flask, Express, FastAPI) |
| `scripts/benchmark.py` | Generates benchmark prompt pairs (baseline vs CodeCrunch) |
| `scripts/format_context.py` | Formats `.codecrunch` artifact into readable context block |

## Demo Results (Phase 3)

| Repo | Files | Edges | Raw Tokens | Artifact Tokens | Compression |
|------|-------|-------|------------|-----------------|-------------|
| Flask | 35 | 0 | 90,862 | 14,043 | 85% reduction |
| Express | 50 | 30 | 27,785 | 6,573 | 76% reduction |
| FastAPI | 530 | 532 | 268,779 | 96,579 | 64% reduction |

## Phase Status

**Phase 1 — Foundation (Hunter) ✅**
Tree-sitter parsing, file ingestion, import analyzer, `.codecrunch` XML schema, LLM summarizer spike with mock mode.

**Phase 2 — Core Compression (Aryan) ✅**
Multi-language support (Python/JS/TS), AST structural hashing + clustering, artifact assembler pipeline, summary caching, token counting.

**Phase 3 — Plugin & CLI (Hunter) ✅**
Click CLI (`python -m codecrunch`), VS Code extension (auto-load, copy context), demo repos tested (Flask/Express/FastAPI), benchmark harness (15 questions across 3 repos).

**Phase 4 — Demo UI & Benchmarks (Aryan) ⬅️ YOU ARE HERE**

Done when: full demo runnable in under 5 minutes, judge-ready.

To do:
1. **Wire up real LLM summaries**: In `codecrunch/summarizer.py`, implement `summarize_module` with `mock=False` using the Claude API (claude-sonnet-4-20250514). The prompt template is already built in `build_summary_prompt`. Run the pipeline with `--no-mock` flag.
2. **Build demo web UI**: Side-by-side comparison showing baseline AI answer vs CodeCrunch-enhanced answer for the same question. UI should show question input, both answers, token counts, and time-to-answer. Benchmark prompts are ready in `benchmarks/benchmark_prompts.json`.
3. **Run benchmarks**: Use the 15 questions in `benchmarks/benchmark_prompts.json`. Each has a `baseline_prompt` and `codecrunch_prompt`. Send both to Claude API, collect responses, measure quality difference.
4. **Fix Flask edges**: Flask shows 0 dependency edges because it uses relative package imports (`from .helpers import`). The import resolver in `import_analyzer.py` needs to handle dotted relative imports.
5. **Polish**: Clean up CLI output, improve error handling, tune compression on FastAPI to get artifact tokens lower.

**Phase 5 — Demo Prep (Both)**
Pitch deck, one-command demo setup, rehearsals, backup demo video.

## Notes
- Summaries are currently mock-generated. Real LLM summaries will be wired up in Phase 4.
- Summary cache is written to `.codecrunch_summaries_cache.json` at the repo root.
- Token metrics are heuristic unless `tiktoken` is installed.
- The VS Code extension compiles but needs to be tested in a live VS Code instance with the Extension Development Host.
