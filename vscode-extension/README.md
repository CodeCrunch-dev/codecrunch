# CodeCrunch VS Code Extension

Injects whole-codebase context from `.codecrunch` artifacts into AI coding assistants.

## What it does

- **Auto-loads** `.codecrunch` files when you open a workspace
- **Status bar** shows whether an artifact is loaded and how many modules it contains
- **Commands** let you reload, inspect, and copy the context for use in AI chats

## Installation (run from source)

1. Install dependencies:
   ```bash
   cd vscode-extension
   npm install
   ```

2. Compile:
   ```bash
   npm run compile
   ```

3. Run the extension:
   - Press `F5` in VS Code to launch the Extension Development Host
   - Or package and install: `vsce package` then install the `.vsix` file

## How to use

1. **Generate a .codecrunch artifact** using the CodeCrunch CLI:
   ```bash
   python -m codecrunch sample_repo
   ```
   This creates `sample_repo.codecrunch` in the current directory.

2. **Open the project** in VS Code (the folder containing the `.codecrunch` file).

3. **Extension auto-loads** when the workspace contains a `*.codecrunch` file. The status bar shows: `CodeCrunch: ✓ loaded (5 modules)`.

4. **Commands** (Command Palette: `Ctrl+Shift+P` / `Cmd+Shift+P`):
   - **CodeCrunch: Load Artifact** — Manually re-scan for `.codecrunch` files
   - **CodeCrunch: Show Status** — Show artifact details (files, edges, token count)
   - **CodeCrunch: Copy Context to Clipboard** — Copy a formatted context block to paste into any AI chat

5. **Paste the context** into Cursor, Copilot, or any AI assistant to give it codebase-wide context before asking questions.
