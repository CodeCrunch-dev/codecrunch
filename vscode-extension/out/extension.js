"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const artifactParser_1 = require("./artifactParser");
const contextProvider_1 = require("./contextProvider");
let statusBarItem;
let cachedArtifact = null;
async function findArtifactFiles(workspaceFolders) {
    const uris = [];
    for (const folder of workspaceFolders) {
        const pattern = new vscode.RelativePattern(folder, "**/*.codecrunch");
        const files = await vscode.workspace.findFiles(pattern);
        uris.push(...files);
    }
    return uris;
}
async function loadArtifactFromFile(uri) {
    try {
        const data = await vscode.workspace.fs.readFile(uri);
        const content = Buffer.from(data).toString("utf-8");
        return (0, artifactParser_1.parseArtifact)(content);
    }
    catch {
        return null;
    }
}
async function loadAndCacheArtifact() {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
        cachedArtifact = null;
        return null;
    }
    const files = await findArtifactFiles(folders);
    if (files.length === 0) {
        cachedArtifact = null;
        return null;
    }
    // Use the first .codecrunch file found
    const artifact = await loadArtifactFromFile(files[0]);
    cachedArtifact = artifact;
    return artifact;
}
function updateStatusBar(artifact) {
    if (artifact) {
        statusBarItem.text = `CodeCrunch: ✓ loaded (${artifact.modules.length} modules)`;
        statusBarItem.tooltip = `Repository: ${artifact.repo}\n${artifact.metadata.filesCount} files, ${artifact.dependencyGraph.edges.length} edges`;
    }
    else {
        statusBarItem.text = "CodeCrunch: No artifact found";
        statusBarItem.tooltip = "No .codecrunch file found in workspace";
    }
    statusBarItem.show();
}
function activate(context) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    context.subscriptions.push(statusBarItem);
    // Initial load
    loadAndCacheArtifact().then(updateStatusBar);
    // Command: Load Artifact
    context.subscriptions.push(vscode.commands.registerCommand("codecrunch.loadArtifact", async () => {
        const artifact = await loadAndCacheArtifact();
        updateStatusBar(artifact);
        if (artifact) {
            vscode.window.showInformationMessage(`CodeCrunch: Loaded artifact (${artifact.modules.length} modules)`);
        }
        else {
            vscode.window.showWarningMessage("CodeCrunch: No .codecrunch file found in workspace");
        }
    }));
    // Command: Show Status
    context.subscriptions.push(vscode.commands.registerCommand("codecrunch.showStatus", async () => {
        const artifact = cachedArtifact ?? (await loadAndCacheArtifact());
        updateStatusBar(artifact);
        if (artifact) {
            const msg = [
                `Repository: ${artifact.repo}`,
                `Files: ${artifact.metadata.filesCount}`,
                `Edges: ${artifact.dependencyGraph.edges.length}`,
                `Generated: ${artifact.metadata.generatedAt}`,
            ].join("\n");
            vscode.window.showInformationMessage(msg, { modal: false });
        }
        else {
            vscode.window.showWarningMessage("CodeCrunch: No artifact loaded. Run 'CodeCrunch: Load Artifact' first.");
        }
    }));
    // Command: Copy Context to Clipboard
    context.subscriptions.push(vscode.commands.registerCommand("codecrunch.copyContext", async () => {
        const artifact = cachedArtifact ?? (await loadAndCacheArtifact());
        if (!artifact) {
            vscode.window.showWarningMessage("CodeCrunch: No artifact loaded. Run 'CodeCrunch: Load Artifact' first.");
            return;
        }
        const contextBlock = (0, contextProvider_1.formatContext)(artifact);
        await vscode.env.clipboard.writeText(contextBlock);
        vscode.window.showInformationMessage("CodeCrunch: Context copied to clipboard. Paste into your AI chat.");
    }));
}
function deactivate() {
    statusBarItem.dispose();
}
//# sourceMappingURL=extension.js.map