"use strict";
/**
 * Parses .codecrunch XML artifact files into typed data structures.
 * Uses a lightweight regex-based approach (no external XML deps).
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseArtifact = parseArtifact;
function getTextContent(xml, tagName) {
    const re = new RegExp(`<${tagName}[^>]*>([\\s\\S]*?)</${tagName}>`, "i");
    const m = xml.match(re);
    return m ? m[1].trim() : "";
}
function getAttribute(xml, attr) {
    const re = new RegExp(`${attr}=["']([^"']*)["']`, "i");
    const m = xml.match(re);
    return m ? m[1] : "";
}
/**
 * Parse .codecrunch XML content into a typed artifact.
 */
function parseArtifact(xmlContent) {
    const rootMatch = xmlContent.match(/<codecrunch[^>]*>([\s\S]*?)<\/codecrunch>/i);
    const rootXml = rootMatch ? rootMatch[1] : xmlContent;
    const version = getAttribute(xmlContent, "version") || "0.1";
    const repo = getAttribute(xmlContent, "repo") || "";
    // Metadata
    const metadata = {
        filesCount: 0,
        generatedAt: "",
    };
    const metaMatch = rootXml.match(/<metadata>([\s\S]*?)<\/metadata>/i);
    if (metaMatch) {
        const metaXml = metaMatch[1];
        const fc = getTextContent(metaXml, "files_count");
        if (fc)
            metadata.filesCount = parseInt(fc, 10) || 0;
        metadata.generatedAt = getTextContent(metaXml, "generated_at");
    }
    // Dependency graph
    const nodes = [];
    const edges = [];
    const dgMatch = rootXml.match(/<dependency_graph>([\s\S]*?)<\/dependency_graph>/i);
    if (dgMatch) {
        const dgXml = dgMatch[1];
        const nodeRegex = /<node\s+name=["']([^"']*)["'](?:\s+type=["']([^"']*)["'])?[^>]*>([\s\S]*?)<\/node>/gi;
        let nodeMatch;
        while ((nodeMatch = nodeRegex.exec(dgXml)) !== null) {
            const name = nodeMatch[1];
            const type = nodeMatch[2] || undefined;
            const nodeBody = nodeMatch[3];
            const dependsOn = [];
            const depRegex = /<dep>([\s\S]*?)<\/dep>/gi;
            let depMatch;
            while ((depMatch = depRegex.exec(nodeBody)) !== null) {
                const dep = depMatch[1].trim();
                if (dep) {
                    dependsOn.push(dep);
                    edges.push({ from: name, to: dep });
                }
            }
            nodes.push({ name, type, dependsOn });
        }
    }
    // Modules
    const modules = [];
    const modulesMatch = rootXml.match(/<modules>([\s\S]*?)<\/modules>/i);
    if (modulesMatch) {
        const modulesXml = modulesMatch[1];
        const modRegex = /<module\s+path=["']([^"']*)["'][^>]*>([\s\S]*?)<\/module>/gi;
        let modMatch;
        while ((modMatch = modRegex.exec(modulesXml)) !== null) {
            const path = modMatch[1];
            const modBody = modMatch[2];
            const classes = [];
            const functions = [];
            const imports = [];
            let summary = "";
            const classRegex = /<class>([\s\S]*?)<\/class>/gi;
            let cMatch;
            while ((cMatch = classRegex.exec(modBody)) !== null) {
                const c = cMatch[1].trim();
                if (c)
                    classes.push(c);
            }
            const fnRegex = /<function>([\s\S]*?)<\/function>/gi;
            let fnMatch;
            while ((fnMatch = fnRegex.exec(modBody)) !== null) {
                const fn = fnMatch[1].trim();
                if (fn)
                    functions.push(fn);
            }
            const impRegex = /<import>([\s\S]*?)<\/import>/gi;
            let impMatch;
            while ((impMatch = impRegex.exec(modBody)) !== null) {
                const imp = impMatch[1].trim();
                if (imp)
                    imports.push(imp);
            }
            const summaryMatch = modBody.match(/<summary>([\s\S]*?)<\/summary>/i);
            if (summaryMatch && summaryMatch[1]) {
                summary = summaryMatch[1].trim();
            }
            modules.push({ path, classes, functions, imports, summary });
        }
    }
    return {
        version,
        repo,
        metadata,
        dependencyGraph: { nodes, edges },
        modules,
    };
}
//# sourceMappingURL=artifactParser.js.map