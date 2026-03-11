"""AST structural hashing and clustering for repeated-pattern detection."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from codecrunch.parser import parse_file_with_language


def _hash_str(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _subtree_hash(node, *, depth: int) -> str:
    """
    Hash only the node.type tree shape up to a fixed depth.

    This intentionally ignores identifier names and literals.
    """
    if depth <= 0:
        return _hash_str(node.type)
    child_hashes = []
    for child in node.children:
        child_hashes.append(_subtree_hash(child, depth=depth - 1))
    payload = node.type + "(" + ",".join(child_hashes) + ")"
    return _hash_str(payload)


def fingerprint_file(filepath: str, *, depth: int = 4, max_nodes: int = 5000) -> set[str]:
    """
    Return a set of subtree hashes for the file.

    max_nodes is a safety valve to avoid pathological traversal on huge files.
    """
    _language, root, _source = parse_file_with_language(filepath)
    if root is None:
        return set()

    fingerprints: set[str] = set()
    stack = [root]
    visited = 0
    while stack and visited < max_nodes:
        node = stack.pop()
        visited += 1
        fingerprints.add(_subtree_hash(node, depth=depth))
        stack.extend(node.children)
    return fingerprints


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass(frozen=True)
class PatternCluster:
    cluster_id: str
    representative: str
    members: list[str]
    similarity_threshold: float
    fingerprint_hash: str


def cluster_repo(
    repo_data: dict,
    *,
    depth: int = 4,
    threshold: float = 0.85,
) -> list[PatternCluster]:
    """
    Greedy clustering over file fingerprints.

    Returns clusters with 2+ members only (singletons are ignored).
    """
    repo_path = repo_data["repo_path"]
    files = repo_data["files"]

    rel_paths: list[str] = []
    for f in files:
        full_path = f["filepath"]
        rel = os.path.relpath(full_path, repo_path).replace(os.sep, "/")
        rel_paths.append(rel)

    # Compute fingerprints once.
    fp_by_rel: dict[str, set[str]] = {}
    for f in files:
        full_path = f["filepath"]
        rel = os.path.relpath(full_path, repo_path).replace(os.sep, "/")
        fp_by_rel[rel] = fingerprint_file(full_path, depth=depth)

    assigned: set[str] = set()
    clusters: list[PatternCluster] = []
    cluster_idx = 1

    for rep in sorted(rel_paths):
        if rep in assigned:
            continue
        rep_fp = fp_by_rel.get(rep, set())
        members = [rep]
        assigned.add(rep)

        for other in sorted(rel_paths):
            if other in assigned:
                continue
            sim = jaccard(rep_fp, fp_by_rel.get(other, set()))
            if sim >= threshold:
                assigned.add(other)
                members.append(other)

        if len(members) >= 2:
            # Stable cluster identifier derived from representative + member list.
            cluster_id = f"cluster_{cluster_idx}"
            fingerprint_hash = _hash_str(rep + "|" + "|".join(sorted(members)))
            clusters.append(
                PatternCluster(
                    cluster_id=cluster_id,
                    representative=rep,
                    members=sorted(members),
                    similarity_threshold=threshold,
                    fingerprint_hash=fingerprint_hash,
                )
            )
            cluster_idx += 1
        else:
            # Singleton: unassign so it doesn't block membership in a later cluster.
            assigned.remove(rep)

    return clusters

