A client-server banking application built with Python, FastAPI, and SQLite.

## Features
- Check account balances, deposit, and withdraw funds.
- Handle concurrent client requests.
- Protect shared account data using locks and database transactions.
- Validate requests and handle errors.
- Log requests.
- Test concurrent deposits and withdrawals.

## Requirements
- Python 3
- Dependencies listed in `requirements.txt`

## Run the Server

```bash
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Set the maximum number of simultaneous requests using `MAX_CLIENTS` (default: 10).

## Run the Client

```bash
python3 client.py
```

## Run Concurrency Tests

```bash
python3 concurrency_test.py
python3 withdrawal_test.py
```

## Technologies
- Python
- FastAPI
- Uvicorn
- SQLite
- Pydantic