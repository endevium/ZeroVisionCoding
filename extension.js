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

async function register(output) {
    try {
        const res = await fetch('http://127.0.0.1:8000/vscode/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json'},
            body: JSON.stringify({ name: 'zero-vision-coding', version: '0.0.1'})
        })

        if (!res.ok) {
            output.appendLine(`VS Code registration failed: HTTP ${res.status}`)
            return;
        }

        output.appendLine('VS Code successfully registered')
    } catch (e) {
        output.appendLine(`VS Code registration error: ${e?.message ?? String(e)}`)
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
                await register(output);
                output.appendLine('VS Code successfully registered');
                delayMs = okDelayMs;
            } catch (e) {
                output.appendLine(`VS Code registration error: ${e?.message ?? String(e)}`);
                delayMs = Math.min(maxDelayMs, Math.max(500, Math.floor(delayMs * 1.6)));
            }

            await sleep(delayMs);
        }
    })();
    
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
