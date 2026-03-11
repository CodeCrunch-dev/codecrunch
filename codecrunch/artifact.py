"""Module for representing code artifacts and their metadata."""

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


def build_artifact(repo_data: dict, dependency_graph: dict, patterns: list[dict] | None = None) -> str:
    """
    Build a structured XML string from repo_data and dependency_graph.

    Returns the .codecrunch artifact as an XML string.
    """
    repo_path = repo_data["repo_path"]
    repo_name = os.path.basename(repo_path.rstrip(os.sep))
    files = repo_data["files"]
    graph = dependency_graph

    # Build edges lookup: node -> list of nodes it depends on
    outgoing = {node: [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        outgoing[edge["from"]].append(edge["to"])

    root = ET.Element("codecrunch", version="0.1", repo=repo_name)

    # Metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "files_count").text = str(repo_data["files_found"])
    ET.SubElement(metadata, "generated_at").text = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Dependency graph
    dg = ET.SubElement(root, "dependency_graph")
    for node_name in sorted(graph["nodes"]):
        node_type = "leaf" if not outgoing[node_name] else None
        attrs = {"name": node_name}
        if node_type:
            attrs["type"] = node_type
        node_elem = ET.SubElement(dg, "node", attrs)
        depends_on = ET.SubElement(node_elem, "depends_on")
        for dep in sorted(outgoing[node_name]):
            ET.SubElement(depends_on, "dep").text = dep

    # Patterns (Phase 2)
    if patterns:
        patterns_elem = ET.SubElement(root, "patterns")
        for p in patterns:
            cluster_elem = ET.SubElement(
                patterns_elem,
                "cluster",
                {
                    "id": str(p.get("id", "")),
                    "representative": str(p.get("representative", "")),
                    "threshold": str(p.get("threshold", "")),
                    "fingerprint": str(p.get("fingerprint", "")),
                },
            )
            members_elem = ET.SubElement(cluster_elem, "members")
            for m in p.get("members", []) or []:
                ET.SubElement(members_elem, "member").text = str(m)

    # Build path -> file_info lookup (use normalized relative path)
    path_to_file = {}
    for f in files:
        rel = os.path.relpath(f["filepath"], repo_path).replace(os.sep, "/")
        path_to_file[rel] = f

    # Modules
    modules_elem = ET.SubElement(root, "modules")
    for node_name in sorted(graph["nodes"]):
        file_info = path_to_file.get(node_name, {})
        module_elem = ET.SubElement(modules_elem, "module", path=node_name)

        classes_elem = ET.SubElement(module_elem, "classes")
        for c in file_info.get("classes", []):
            ET.SubElement(classes_elem, "class").text = c

        functions_elem = ET.SubElement(module_elem, "functions")
        for fn in file_info.get("functions", []):
            ET.SubElement(functions_elem, "function").text = fn

        imports_elem = ET.SubElement(module_elem, "imports")
        for imp in file_info.get("imports", []):
            ET.SubElement(imports_elem, "import").text = imp

        ET.SubElement(module_elem, "summary").text = "PLACEHOLDER - will be filled by LLM summarizer in Phase 2"

    # Serialize to string with declaration
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str


def save_artifact(xml_string: str, output_path: str) -> None:
    """Write the XML string to a file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_string)


def load_artifact(filepath: str) -> dict:
    """
    Parse a .codecrunch XML file into a dict.

    Returns dict with keys: metadata, dependency_graph, modules.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    metadata = {}
    meta_elem = root.find("metadata")
    if meta_elem is not None:
        fc = meta_elem.find("files_count")
        if fc is not None and fc.text:
            metadata["files_count"] = int(fc.text)
        ga = meta_elem.find("generated_at")
        if ga is not None and ga.text:
            metadata["generated_at"] = ga.text

    dependency_graph = {"nodes": [], "edges": []}
    dg_elem = root.find("dependency_graph")
    if dg_elem is not None:
        for node_elem in dg_elem.findall("node"):
            name = node_elem.get("name")
            if name:
                dependency_graph["nodes"].append(name)
            depends_on = node_elem.find("depends_on")
            if depends_on is not None:
                for dep_elem in depends_on.findall("dep"):
                    if dep_elem.text and name:
                        dependency_graph["edges"].append(
                            {"from": name, "to": dep_elem.text}
                        )

    modules = []
    modules_elem = root.find("modules")
    if modules_elem is not None:
        for mod_elem in modules_elem.findall("module"):
            path = mod_elem.get("path", "")
            mod_data = {"path": path, "classes": [], "functions": [], "imports": [], "summary": ""}
            classes_elem = mod_elem.find("classes")
            if classes_elem is not None:
                for c in classes_elem.findall("class"):
                    if c.text:
                        mod_data["classes"].append(c.text)
            functions_elem = mod_elem.find("functions")
            if functions_elem is not None:
                for fn in functions_elem.findall("function"):
                    if fn.text:
                        mod_data["functions"].append(fn.text)
            imports_elem = mod_elem.find("imports")
            if imports_elem is not None:
                for imp in imports_elem.findall("import"):
                    if imp.text:
                        mod_data["imports"].append(imp.text)
            summary_elem = mod_elem.find("summary")
            if summary_elem is not None and summary_elem.text:
                mod_data["summary"] = summary_elem.text
            modules.append(mod_data)

    return {
        "metadata": metadata,
        "dependency_graph": dependency_graph,
        "modules": modules,
    }
