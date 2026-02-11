// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
const vscode = require('vscode');
let output;
// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed

/**
 * @param {vscode.ExtensionContext} context
 */

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function postJson(url, body) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

async function sendActiveEditorSnapshot() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const doc = editor.document;

    await postJson('http://127.0.0.1:8000/vscode/editor', {
        uri: String(doc.uri),
        language: doc.languageId,
        text: doc.getText(),
    });
}

function createDebouncer(delayMs, fn) {
    let timer = undefined;
    let running = false;
    let queued = false;

    return async () => {
        queued = true;
        if (timer) clearTimeout(timer);

        timer = setTimeout(async () => {
            if (running) return;
            running = true;

            try {
                if (queued) {
                    queued = false;
                    await fn();
                }
            } finally {
                running = false;
            }
        }, delayMs);
    };
}

async function register(output) {
    try {
        const res = await fetch('http://127.0.0.1:8000/vscode/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json'},
            body: JSON.stringify({ name: 'zero-vision-coding', version: '0.0.1'})
        });

        if (!res.ok) {
            output.appendLine(`VS Code registration failed: HTTP ${res.status}`);
            return false;
        }

        output.appendLine('VS Code successfully registered');
        return true;
    } catch (e) {
        output.appendLine(`VS Code registration error: ${e?.message ?? String(e)}`);
        return false;
    }
}

function activate(context) {
    output = vscode.window.createOutputChannel('Zero Vision Coding');
    output.appendLine('Activated: zero-vision-coding');
    output.show(true);

    let stopped = false;
    context.subscriptions.push({ dispose: () => { stopped = true; } });

    (async () => {
        let delayMs = 500;  
        const okDelayMs = 2000;
        const maxDelayMs = 10000;

        while (!stopped) {
            try {
                const ok = await register(output);
                if (ok) {
                    delayMs = okDelayMs;
                } else {
                    delayMs = Math.min(maxDelayMs, Math.max(500, Math.floor(delayMs * 1.6)));
                }
            } catch (e) {
                output.appendLine(`VS Code registration error: ${e?.message ?? String(e)}`);
                delayMs = Math.min(maxDelayMs, Math.max(500, Math.floor(delayMs * 1.6)));
            }

            await sleep(delayMs);
        }
    })();

    const debouncedSend = createDebouncer(250, async () => {
        try {
            await sendActiveEditorSnapshot();
            // output.appendLine('Sent editor snapshot'); // enable if needed
        } catch (e) {
            output.appendLine(`Failed to send editor snapshot: ${e?.message ?? String(e)}`);
        }
    });

    // Send once on activation
    debouncedSend();

    // Send when typing in the active document
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument((e) => {
        const active = vscode.window.activeTextEditor?.document;
        if (!active) return;
        if (e.document !== active) return;
        debouncedSend();
    }));

    // Send when switching editors
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(() => {
        debouncedSend();
    }));
    
    const disposable = vscode.commands.registerCommand('zero-vision-coding.helloWorld', function () {
        output.appendLine('Command executed: zero-vision-coding.helloWorld');
        output.show(true);
        vscode.window.showInformationMessage('Hello World from Zero Vision Coding!');
    });

    context.subscriptions.push(output, disposable);
}

// This method is called when your extension is deactivated
function deactivate() {}

module.exports = {
	activate,
	deactivate
}
