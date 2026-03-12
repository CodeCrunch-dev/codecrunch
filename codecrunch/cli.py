"""Click-based CLI for CodeCrunch."""

from __future__ import annotations

import os
import sys

import click

from codecrunch.artifact import save_artifact
from codecrunch.import_analyzer import print_dependency_graph
from codecrunch.pipeline import run


@click.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output path for the .codecrunch file (default: ./<repo_name>.codecrunch)",
)
@click.option(
    "--extensions",
    "-e",
    default=".py,.js,.ts,.jsx,.tsx",
    help="Comma-separated file extensions to include (default: .py,.js,.ts,.jsx,.tsx)",
)
@click.option(
    "--mock/--no-mock",
    default=True,
    help="Use mock summaries vs real LLM (default: --mock)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Print the full dependency graph and detailed metrics",
)
def main(path: str, output: str | None, extensions: str, mock: bool, verbose: bool) -> None:
    """Run CodeCrunch on a repository directory."""
    repo_path = os.path.abspath(path)
    repo_name = os.path.basename(repo_path.rstrip(os.sep))

    ext_list = [e.strip() for e in extensions.split(",") if e.strip()]
    if not ext_list:
        click.echo("Error: at least one extension required", err=True)
        sys.exit(1)

    output_path = output
    if output_path is None:
        output_path = os.path.join(os.getcwd(), f"{repo_name}.codecrunch")

    try:
        xml_final, metrics = run(
            repo_path,
            extensions=ext_list,
            mock_summaries=mock,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    save_artifact(xml_final, output_path)

    # Compression ratio: artifact_tokens / raw_tokens (lower = better compression)
    raw_tokens = metrics.get("raw_tokens", 0)
    artifact_tokens = metrics.get("artifact_tokens", 0)
    compression_ratio = (
        artifact_tokens / raw_tokens if raw_tokens > 0 else 0.0
    )

    if verbose:
        click.echo()
        print_dependency_graph(metrics["dependency_graph"])
        click.echo()

    click.echo("=" * 40)
    click.echo("Pipeline complete")
    click.echo("=" * 40)
    click.echo(f"Files processed:   {metrics['files_processed']}")
    click.echo(f"Edges found:       {metrics['edges_found']}")
    click.echo(f"Patterns:          {metrics.get('patterns_clusters', 0)} clusters (largest={metrics.get('patterns_largest_cluster', 0)})")
    click.echo(f"Raw tokens:        {raw_tokens}")
    click.echo(f"Artifact tokens:   {artifact_tokens}")
    click.echo(f"Compression ratio: {compression_ratio:.2%}")
    click.echo(f"Output path:       {output_path}")
