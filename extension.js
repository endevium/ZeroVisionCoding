// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
const vscode = require('vscode');
const SERVER = 'http://127.0.0.1:8000';
const { spawn } = require('child_process');

let _registeredOnce = false;
let output;
let runningChild = null;
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

let lastPythonPath = null;

async function sendActiveEditorSnapshot() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const doc = editor.document;

    if (doc.languageId === 'python' && !doc.isUntitled) {
        lastPythonPath = doc.uri.fsPath;
    }

    const sel = editor.selection;

    await postJson(`${SERVER}/vscode/editor`, {
        uri: String(doc.uri),
        language: doc.languageId,
        text: doc.getText(),
        version: doc.version,
        path: doc.uri.fsPath,

        // NEW: context
        cursor: { line: sel.active.line, character: sel.active.character },
        selection: {
            anchor: { line: sel.anchor.line, character: sel.anchor.character },
            active: { line: sel.active.line, character: sel.active.character },
            isReversed: sel.isReversed,
        },
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

async function registerExtension() {
    try {
        const res = await fetch(`${SERVER}/vscode/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'zero-vision-coding', version: '0.0.1' })
        });

        if (!res.ok) {
            _registeredOnce = false;
            output.appendLine(`VS Code registration failed: HTTP ${res.status}`);
            return false;
        }

        if (!_registeredOnce) {
            output.appendLine('VS Code successfully registered');
            _registeredOnce = true;
        }

        return true;
    } catch (e) {
        _registeredOnce = false;
        output.appendLine(`VS Code registration error: ${e?.message ?? String(e)}`);
        return false;
    }
}

function createRunActivePythonTask() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return null;

    const file = editor.document.uri.fsPath;
    const exec = new vscode.ShellExecution(`py "${file}"`);

    const task = new vscode.Task(
        { type: 'zeroVision', task: 'runActivePython' },
        vscode.TaskScope.Workspace,
        'ZeroVision: Run Active Python File',
        'Zero Vision Coding',
        exec,
        []
    );

    task.presentationOptions = {
        reveal: vscode.TaskRevealKind.Always,
        panel: vscode.TaskPanelKind.Dedicated,
        clear: true,
        focus: false,
    };

    return task;
}

async function postCommandResult(id, ok, message = '', data = {}) {
    try {
        await postJson(`${SERVER}/vscode/command-result`, { id, ok, message, data });
    } catch {
        // ignore
    }
}

async function fetchNextCommand() {
    try {
        const res = await fetch(`${SERVER}/vscode/next-command`);

        if (res.status === 204) return null;

        if (!res.ok) {
            // This is the bug visibility you need
            output.appendLine(`[poll] next-command failed: HTTP ${res.status}`);
            return null;
        }

        const data = await res.json();
        output.appendLine(`[poll] got command: ${JSON.stringify(data)}`);
        return data;
    } catch (e) {
        output.appendLine(`[poll] next-command error: ${e?.message ?? String(e)}`);
        return null;
    }
}

async function handleCommand(cmd) {
    const id = cmd?.id;
    const type = cmd?.type;
    const payload = cmd?.payload || {};

    if (!id || !type) return;

    try {
        output.appendLine(`[cmd] received id=${id} type=${type} payload=${JSON.stringify(payload)}`);

        if (type === 'run_program') {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                output.appendLine('[cmd] run_program failed: no active editor');
                vscode.window.showErrorMessage('Zero Vision Coding: No active editor to run.');
                await postCommandResult(id, false, 'No active editor to run');
                return;
            }

            const doc = editor.document;
            output.appendLine(`[cmd] active doc: ${doc.uri.toString()} lang=${doc.languageId} isUntitled=${doc.isUntitled}`);

            if (doc.isUntitled) {
                vscode.window.showErrorMessage('Zero Vision Coding: Please save the file before running.');
                await postCommandResult(id, false, 'Active file is untitled; save it first');
                return;
            }

            try {
                await doc.save();
            } catch {
                output.appendLine('[cmd] warning: doc.save() failed');
            }

            // Use captured runner so stdout/stderr are posted to the server
            runPythonCaptured(doc.uri.fsPath);

            await postCommandResult(id, true, 'Running with captured output');
            return;
        }

        if (type === 'stop_program') {
            if (!runningChild) {
                await postCommandResult(id, false, 'No running program');
                return;
            }
            try {
                runningChild.kill();
                runningChild = null;
                await terminalFinish(137);
                await postCommandResult(id, true, 'Stopped program');
            } catch (e) {
                await postCommandResult(id, false, e?.message ?? String(e));
            }
            return;
        }

        if (type === 'move_to_line') {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                await postCommandResult(id, false, 'No active editor');
                return;
            }

            const maxLine = Math.max(0, editor.document.lineCount - 1);
            const requested = (Number(payload.line) || 1) - 1;
            const line = Math.min(Math.max(0, requested), maxLine);

            const pos = new vscode.Position(line, 0);
            editor.selection = new vscode.Selection(pos, pos);
            editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);

            await postCommandResult(id, true, `Moved to line ${line + 1}`);
            return;
        }

        if (type === 'save_file') {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                await postCommandResult(id, false, 'No active editor');
                return;
            }
            await editor.document.save();
            await postCommandResult(id, true, 'File saved');
            return;
        }

        if (type === 'find') {
            const query = String(payload.query || '').trim();
            if (!query) {
                await postCommandResult(id, false, 'Missing query');
                return;
            }
            await vscode.commands.executeCommand('actions.find');
            await vscode.commands.executeCommand('editor.actions.findWithArgs', { searchString: query });
            await postCommandResult(id, true, `Searching for ${query}`);
            return;
        }

        if (type === 'scroll') {
            const direction = String(payload.direction || 'down');
            const lines = Math.max(1, Number(payload.lines) || 10);

            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                await postCommandResult(id, false, 'No active editor');
                return;
            }

            await vscode.commands.executeCommand(
                direction === 'up' ? 'scrollLineUp' : 'scrollLineDown'
            );

            // repeat for more lines
            for (let i = 1; i < lines; i++) {
                await vscode.commands.executeCommand(direction === 'up' ? 'scrollLineUp' : 'scrollLineDown');
            }

            await postCommandResult(id, true, `Scrolled ${direction} ${lines} lines`);
            return;
        }

        if (type === 'goto_function') {
            const name = String(payload.name || '').trim();
            if (!name) {
                await postCommandResult(id, false, 'Missing function name');
                return;
            }

            await vscode.commands.executeCommand('actions.find');
            await vscode.commands.executeCommand('editor.actions.findWithArgs', { searchString: `def ${name}` });
            await vscode.commands.executeCommand('editor.action.nextMatchFindAction');

            await postCommandResult(id, true, `Going to function ${name}`);
            return;
        }

        await postCommandResult(id, false, `Unknown command type: ${type}`);
    } catch (e) {
        output.appendLine(`[cmd] error: ${e?.stack ?? (e?.message ?? String(e))}`);
        await postCommandResult(id, false, e?.message ?? String(e));
    }
}

function activate(context) {
    output = vscode.window.createOutputChannel('Zero Vision Coding');
    output.appendLine('Activated: zero-vision-coding');
    output.show(true);

    let stopped = false;
    context.subscriptions.push({ dispose: () => { stopped = true; } });

    // Keep trying to register with the server (backoff)
    (async () => {
        let delayMs = 500;
        const okDelayMs = 2000;
        const maxDelayMs = 10000;

        while (!stopped) {
            try {
                const ok = await registerExtension();
                if (ok) delayMs = okDelayMs;
                else delayMs = Math.min(maxDelayMs, Math.max(500, Math.floor(delayMs * 1.6)));
            } catch (e) {
                output.appendLine(`VS Code registration error: ${e?.message ?? String(e)}`);
                delayMs = Math.min(maxDelayMs, Math.max(500, Math.floor(delayMs * 1.6)));
            }

            await sleep(delayMs);
        }
    })();

    // Debounced editor snapshot sender
    const debouncedSend = createDebouncer(250, async () => {
        try {
            await sendActiveEditorSnapshot();
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

    // Existing helloWorld command
    const helloWorld = vscode.commands.registerCommand('zero-vision-coding.helloWorld', function () {
        output.appendLine('Command executed: zero-vision-coding.helloWorld');
        output.show(true);
        vscode.window.showInformationMessage('Hello World from Zero Vision Coding!');
    });
    context.subscriptions.push(helloWorld);

    // Task provider (optional but fine to keep)
    const provider = vscode.tasks.registerTaskProvider('zeroVision', {
        provideTasks: () => {
            const t = createRunActivePythonTask();
            return t ? [t] : [];
        },
        resolveTask: (task) => task,
    });
    context.subscriptions.push(provider);

    // Command: runProgram (Task)
    const runProgramCmd = vscode.commands.registerCommand('zero-vision-coding.runProgram', async () => {
        const task = createRunActivePythonTask();
        if (!task) {
            vscode.window.showErrorMessage('No active editor to run.');
            return;
        }
        await vscode.tasks.executeTask(task);
    });
    context.subscriptions.push(runProgramCmd);

    // Poll server for commands and execute them
    (async () => {
        output.appendLine('Command polling started');
        while (!stopped) {
            const cmd = await fetchNextCommand();
            if (cmd) await handleCommand(cmd);
            await sleep(300);
        }
    })();
}







async function terminalReset(command) {
    try { await postJson(`${SERVER}/terminal/reset`, { command }); } catch {}
}
async function terminalAppend(stdout, stderr) {
    try { await postJson(`${SERVER}/terminal/append`, { stdout, stderr }); } catch {}
}
async function terminalFinish(exitCode) {
    try { await postJson(`${SERVER}/terminal/finish`, { exit_code: exitCode }); } catch {}
}

function runPythonCaptured(filePath) {
    const writeEmitter = new vscode.EventEmitter();
    const closeEmitter = new vscode.EventEmitter();

    const pty = {
        onDidWrite: writeEmitter.event,
        onDidClose: closeEmitter.event,
        open: async () => {
            const cmdLine = `py "${filePath}"\r\n`;
            writeEmitter.fire(`Zero Vision Coding runner\r\n> ${cmdLine}\r\n`);
            await terminalReset(`py "${filePath}"`);

            const child = spawn('py', [filePath], { cwd: require('path').dirname(filePath) });

            child.stdout.on('data', (buf) => {
                const s = buf.toString('utf8');
                writeEmitter.fire(s.replace(/\n/g, '\r\n'));
                terminalAppend(s, '');
            });

            child.stderr.on('data', (buf) => {
                const s = buf.toString('utf8');
                writeEmitter.fire(s.replace(/\n/g, '\r\n'));
                terminalAppend('', s);
            });

            child.on('close', (code) => {
                writeEmitter.fire(`\r\n[process exited with code ${code ?? 0}]\r\n`);
                terminalFinish(code ?? 0);
            });
        },
        close: () => {
            // If terminal is closed manually, stop the running program
            try {
                if (runningChild) {
                    runningChild.kill();
                    runningChild = null;
                }
            } catch {}
        },
    };

    const term = vscode.window.createTerminal({ name: 'ZeroVision Run', pty });
    term.show(true);
}

// This method is called when your extension is deactivated
function deactivate() {}

module.exports = {
	activate,
	deactivate
}
