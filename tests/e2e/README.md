# Browser tests

Run from the project root with your virtual environment activated:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-e2e.txt
export PLAYWRIGHT_BROWSERS_PATH=0
python -m playwright install chromium
python -m pytest tests/e2e/ -q
```

Each test uses a temporary SQLite database and starts its own local server.

## Coverage

- Add an expense through the form; verify its date, amount, and category after reload.
- Delete a specific expense; verify it stays absent after reload and another expense remains.
- Open Summary through navigation; use the month picker to switch from January to February and verify the displayed total changes.
- Click Export CSV; verify the downloaded filename, one exported expense, its amount, and preservation of a comma-containing description.
