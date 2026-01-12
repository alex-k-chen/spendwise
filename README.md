# spendwise

A lightweight self-hosted expense tracker built with Flask and SQLite.

## Features

- Add, view, and delete expenses
- Categorize spending (Food, Transport, Housing, etc.)
- Monthly summary with per-category breakdown
- CSV export
- REST API for programmatic access
- No external database required -- just SQLite

## Getting Started

```bash
# clone and set up
git clone https://github.com/YOURUSERNAME/spendwise.git
cd spendwise
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run
python app.py
```

Open http://localhost:5000

## API

```bash
# add expense
curl -X POST http://localhost:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 12.50, "description": "Lunch", "category_id": 1, "date": "2025-01-15"}'

# list expenses
curl http://localhost:5000/api/expenses?month=2025-01

# monthly summary
curl http://localhost:5000/api/summary/2025-01
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## License

MIT
