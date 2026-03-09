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

## Phase 2 Handoff

For Phase 2, Aryan needs to:

1. **Implement `summarize_module` with `mock=False`** — Wire up the Claude API using the existing `build_summary_prompt` template and function signature
2. **Extend the parser** — Add support for TypeScript/JavaScript (tree-sitter-* grammars)
3. **Build AST structural hashing** — Implement pattern detection via hashed AST subtrees for similarity/code-smell detection
