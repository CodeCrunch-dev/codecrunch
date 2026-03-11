"""Parse source files using tree-sitter and extract lightweight structure."""

from __future__ import annotations

import os
import re

import tree_sitter
import tree_sitter_python

PARSER_EXTRACTOR_VERSION = "phase2-0.1"


def _detect_language(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".py":
        return "python"
    if ext in {".js", ".jsx"}:
        return "javascript"
    if ext == ".ts":
        return "typescript"
    if ext == ".tsx":
        return "tsx"
    return "unknown"


def _build_language(language: str) -> tree_sitter.Language | None:
    if language == "python":
        return tree_sitter.Language(tree_sitter_python.language())
    if language == "javascript":
        import tree_sitter_javascript

        return tree_sitter.Language(tree_sitter_javascript.language())
    if language in {"typescript", "tsx"}:
        import tree_sitter_typescript

        if language == "tsx":
            return tree_sitter.Language(tree_sitter_typescript.language_tsx())
        return tree_sitter.Language(tree_sitter_typescript.language_typescript())
    return None


_PARSERS: dict[str, tree_sitter.Parser] = {}


def _get_parser(language: str) -> tree_sitter.Parser | None:
    parser = _PARSERS.get(language)
    if parser is not None:
        return parser
    lang = _build_language(language)
    if lang is None:
        return None
    parser = tree_sitter.Parser(lang)
    _PARSERS[language] = parser
    return parser


def parse_file(filepath: str) -> tree_sitter.Node:
    """
    Backwards-compatible API for Phase 1 tests: parse a Python file and return the root node.

    For multi-language parsing, use parse_file_with_language().
    """
    language, root_node, _source = parse_file_with_language(filepath)
    if language != "python":
        raise ValueError(f"parse_file() only supports Python; got {language} for {filepath}")
    return root_node


def parse_file_with_language(filepath: str) -> tuple[str, tree_sitter.Node, bytes]:
    """Parse a file and return (language, root_node, source_bytes)."""
    with open(filepath, "r", encoding="utf-8") as f:
        source_str = f.read()
    source_bytes = source_str.encode("utf-8")

    language = _detect_language(filepath)
    parser = _get_parser(language)
    if parser is None:
        raise ValueError(f"Unsupported language for parsing: {filepath}")
    tree = parser.parse(source_bytes)
    return language, tree.root_node, source_bytes


def _node_text(node: tree_sitter.Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace").strip()


def _walk_python(node: tree_sitter.Node, source: bytes, result: dict) -> None:
    if node.type == "function_definition":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["functions"].append(_node_text(name_node, source))
    elif node.type == "class_definition":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["classes"].append(_node_text(name_node, source))
    elif node.type in {"import_statement", "import_from_statement"}:
        result["imports"].append(_node_text(node, source))

    for child in node.children:
        _walk_python(child, source, result)


_RE_REQUIRE = re.compile(r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)""")


def _try_extract_require_from_text(text: str) -> str | None:
    match = _RE_REQUIRE.search(text)
    if not match:
        return None
    return match.group(1)


def _walk_jsts(node: tree_sitter.Node, source: bytes, result: dict) -> None:
    # We keep this best-effort and lightweight: statement text for imports/exports,
    # plus named declarations for common signature-ish nodes.
    if node.type == "import_statement":
        result["imports"].append(_node_text(node, source))
    elif node.type == "export_statement":
        result["exports"].append(_node_text(node, source))
    elif node.type in {"function_declaration", "generator_function_declaration"}:
        name_node = node.child_by_field_name("name")
        if name_node:
            result["functions"].append(_node_text(name_node, source))
    elif node.type == "class_declaration":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["classes"].append(_node_text(name_node, source))
    elif node.type == "interface_declaration":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["interfaces"].append(_node_text(name_node, source))
    elif node.type == "type_alias_declaration":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["types"].append(_node_text(name_node, source))
    elif node.type == "enum_declaration":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["enums"].append(_node_text(name_node, source))
    elif node.type == "call_expression":
        # Pick up require('...') even if nested.
        text = _node_text(node, source)
        spec = _try_extract_require_from_text(text)
        if spec:
            result["imports"].append(f"require:{spec}")

    for child in node.children:
        _walk_jsts(child, source, result)


def extract_structure(filepath: str) -> dict:
    """
    Parse a file and return a dict with at least:
    - filepath: str
    - language: str
    - functions: list[str]
    - classes: list[str]
    - imports: list[str]

    For JS/TS, also includes:
    - exports: list[str]
    - interfaces: list[str]
    - types: list[str]
    - enums: list[str]
    """
    language, root_node, source_bytes = parse_file_with_language(filepath)

    result: dict = {
        "filepath": filepath,
        "language": language,
        "functions": [],
        "classes": [],
        "imports": [],
        "extractor_version": PARSER_EXTRACTOR_VERSION,
    }

    if language in {"javascript", "typescript", "tsx"}:
        result.update(
            {
                "exports": [],
                "interfaces": [],
                "types": [],
                "enums": [],
            }
        )

    if root_node:
        if language == "python":
            _walk_python(root_node, source_bytes, result)
        elif language in {"javascript", "typescript", "tsx"}:
            _walk_jsts(root_node, source_bytes, result)
        else:
            # Unsupported language should already have been rejected, but keep safe.
            pass

    return result
