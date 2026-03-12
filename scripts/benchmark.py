#!/usr/bin/env python3
"""Benchmark harness: generate prompt pairs (baseline vs CodeCrunch) for AI answer quality testing."""

import json
import os
import re
import sys

# Add project root and scripts to path
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_scripts_dir)
sys.path.insert(0, _project_root)
sys.path.insert(0, _scripts_dir)

from codecrunch.artifact import load_artifact
from codecrunch.token_count import count_tokens
import format_context as _format_context_mod

PROJECT_ROOT = _project_root
BENCHMARKS_DIR = os.path.join(PROJECT_ROOT, "benchmarks")
DEMO_REPOS = ("flask", "express", "fastapi")

QUESTIONS = {
    "flask": [
        "How does a request flow from the WSGI entry point to a view function and back to a response?",
        "What is the relationship between the Flask app object, blueprints, and the request context stack?",
        "How does Flask's template rendering connect to Jinja2 and what context variables are automatically available?",
        "Explain the error handling chain: what happens when a view raises an exception?",
        "How do Flask extensions register themselves and hook into the app lifecycle?",
    ],
    "express": [
        "Trace how an HTTP request flows through the middleware stack to a route handler and back.",
        "How does Express's Router relate to the main app, and how are sub-routers mounted?",
        "Explain how error-handling middleware works differently from regular middleware.",
        "How does Express resolve and execute route parameters and parameter callbacks?",
        "What is the relationship between req, res, and next across the middleware chain?",
    ],
    "fastapi": [
        "How does FastAPI convert a decorated function into an API endpoint with validation?",
        "Trace the dependency injection flow: how are Depends() parameters resolved and cached?",
        "How do Pydantic models integrate with OpenAPI schema generation in FastAPI?",
        "Explain the middleware and exception handler chain for a typical request.",
        "How does FastAPI handle async vs sync route handlers differently?",
    ],
}


def load_artifact_with_repo(filepath: str) -> dict:
    """Load artifact and add repo from XML."""
    artifact = load_artifact(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    repo_match = re.search(r'repo=["\']([^"\']*)["\']', content)
    if repo_match:
        artifact["repo"] = repo_match.group(1)
    else:
        artifact["repo"] = os.path.splitext(os.path.basename(filepath))[0].replace(".codecrunch", "")
    return artifact


def format_context(artifact: dict) -> str:
    """Format artifact as context block (delegate to format_context module)."""
    return _format_context_mod.format_context(artifact)


def main() -> int:
    os.makedirs(BENCHMARKS_DIR, exist_ok=True)
    output_path = os.path.join(BENCHMARKS_DIR, "benchmark_prompts.json")

    all_results = []
    total_questions = 0
    total_context_tokens = 0

    for repo in DEMO_REPOS:
        artifact_path = os.path.join(PROJECT_ROOT, f"{repo}.codecrunch")
        if not os.path.isfile(artifact_path):
            print(f"Warning: {artifact_path} not found, skipping {repo}", file=sys.stderr)
            continue

        artifact = load_artifact_with_repo(artifact_path)
        context_block = format_context(artifact)
        context_tokens = count_tokens(context_block)

        questions_data = []
        for i, question in enumerate(QUESTIONS[repo], 1):
            q_id = f"{repo}_q{i}"
            baseline_prompt = question
            codecrunch_prompt = f"{context_block}\n\n---\n\n{question}"

            questions_data.append({
                "id": q_id,
                "question": question,
                "baseline_prompt": baseline_prompt,
                "codecrunch_prompt": codecrunch_prompt,
                "codecrunch_context_tokens": context_tokens,
            })
            total_questions += 1
            total_context_tokens += context_tokens

        all_results.append({
            "repo": repo,
            "questions": questions_data,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    avg_context = total_context_tokens / total_questions if total_questions else 0

    print("=" * 60)
    print("Benchmark Prompt Generation Complete")
    print("=" * 60)
    print(f"Total questions: {total_questions}")
    print(f"Average context tokens added per question: {avg_context:.0f}")
    print(f"Output: {output_path}")
    print()
    print("Note: Actual LLM comparison (baseline vs CodeCrunch) can be run")
    print("manual or automated in Phase 4.")
    print()

    # Show one example question pair
    if all_results:
        first = all_results[0]
        first_q = first["questions"][0]
        print("Example question pair (first question):")
        print("-" * 60)
        print("BASELINE (first 200 chars):")
        print(first_q["baseline_prompt"][:200] + "..." if len(first_q["baseline_prompt"]) > 200 else first_q["baseline_prompt"])
        print()
        print("CODECRUNCH (context + question, first 500 chars):")
        print(first_q["codecrunch_prompt"][:500] + "..." if len(first_q["codecrunch_prompt"]) > 500 else first_q["codecrunch_prompt"])
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
