# Trading Project Backend Quick Start

## One-time setup

From the project root:

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
```

## Every time you reopen VS Code

1. Open Command Palette: Cmd+Shift+P
2. Run: Python: Select Interpreter
3. Choose: `${workspaceFolder}/.venv/bin/python`
4. Open a new terminal

Optional in terminal:

```bash
source /Users/shi/Desktop/Y2S2/Trading_project/.venv/bin/activate
```

## Run scripts

From the `backend` folder:

```bash
python scheduler.py
```

For one-time backfill:

```bash
python backfill.py
```

## Update dependencies

If you install a new package, update requirements:

```bash
pip freeze > requirements.txt
```
