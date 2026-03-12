/**
 * Formats CodeCrunch artifact data into a clean context block for AI prompts.
 */

import type { CodeCrunchArtifact } from "./artifactParser";

/**
 * Format the artifact into a readable context block that can be prepended to AI prompts.
 */
export function formatContext(artifact: CodeCrunchArtifact): string {
  const lines: string[] = [];

  lines.push("## CodeCrunch: Codebase Context");
  lines.push(`Repository: ${artifact.repo}`);
  lines.push(
    `Files: ${artifact.metadata.filesCount} | Dependencies: ${artifact.dependencyGraph.edges.length}`
  );
  lines.push("");

  // Architecture (dependency graph)
  lines.push("### Architecture");
  for (const node of artifact.dependencyGraph.nodes) {
    if (node.dependsOn.length === 0) {
      lines.push(`  ${node.name} (leaf)`);
    } else {
      lines.push(`  ${node.name} -> ${node.dependsOn.join(", ")}`);
    }
  }
  lines.push("");

  // Module summaries
  lines.push("### Module Summaries");
  for (const mod of artifact.modules) {
    const summary = mod.summary || "(no summary)";
    lines.push(`${mod.path}: ${summary}`);
  }

  return lines.join("\n");
}
