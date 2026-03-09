"""Parse Python files using tree-sitter and extract structure."""

import tree_sitter
import tree_sitter_python


parser = tree_sitter.Parser(
    tree_sitter.Language(tree_sitter_python.language())
)


def parse_file(filepath: str) -> tree_sitter.Node:
    """Read a Python file and return the tree-sitter AST root node."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tree = parser.parse(source.encode("utf-8"))
    return tree.root_node


def _walk_node(node: tree_sitter.Node, source: bytes, result: dict) -> None:
    """Recursively walk the AST and collect functions, classes, and imports."""
    if node.type == "function_definition":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["functions"].append(source[name_node.start_byte : name_node.end_byte].decode("utf-8"))
    elif node.type == "class_definition":
        name_node = node.child_by_field_name("name")
        if name_node:
            result["classes"].append(source[name_node.start_byte : name_node.end_byte].decode("utf-8"))
    elif node.type == "import_statement":
        import_text = source[node.start_byte : node.end_byte].decode("utf-8").strip()
        result["imports"].append(import_text)
    elif node.type == "import_from_statement":
        import_text = source[node.start_byte : node.end_byte].decode("utf-8").strip()
        result["imports"].append(import_text)

    for child in node.children:
        _walk_node(child, source, result)


def extract_structure(filepath: str) -> dict:
    """
    Parse a file and return a dict with:
    - filepath: str
    - functions: list of function names
    - classes: list of class names
    - imports: list of import strings
    """
    with open(filepath, "r", encoding="utf-8") as f:
        source_str = f.read()
    source_bytes = source_str.encode("utf-8")
    tree = parser.parse(source_bytes)

    result = {
        "filepath": filepath,
        "functions": [],
        "classes": [],
        "imports": [],
    }

    if tree.root_node:
        _walk_node(tree.root_node, source_bytes, result)

    return result
