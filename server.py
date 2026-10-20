import os
import time
import sqlite3
import logging
import asyncio
from uuid import uuid4
from datetime import datetime, timezone
from threading import Lock
from contextlib import contextmanager

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bank.db")
LOG_PATH = os.path.join(BASE_DIR, "bank.log")
MAX_CLIENTS = max(1, int(os.getenv("MAX_CLIENTS", "10")))

app = FastAPI(title="Yasin Banking Server")
db_lock = Lock()
request_semaphore = asyncio.Semaphore(MAX_CLIENTS)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


class TransactionRequest(BaseModel):
    action: str
    account: str
    amount: float | None = Field(default=None, gt=0)


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account TEXT PRIMARY KEY,
                balance REAL NOT NULL CHECK (balance >= 0)
            )
        """)
        connection.execute("""
            INSERT OR IGNORE INTO accounts (account, balance)
            VALUES ('A1001', 1000), ('A1002', 500)
        """)


@app.on_event("startup")
def startup():
    initialize_database()
    logging.info("server_started max_clients=%s", MAX_CLIENTS)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id

    start = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    action = "unknown"
    account = "unknown"
    status_code = 500
    result = "error"

    if path == "/":
        action = "home"
    elif path == "/health":
        action = "health"
    elif path == "/transaction":
        action = "invalid_request"
    elif path.startswith("/balance/"):
        action = "balance"
        account = path.removeprefix("/balance/")

    request.state.action = action
    request.state.account = account

    try:
        async with request_semaphore:
            response = await call_next(request)

        status_code = response.status_code
        result = "success" if status_code < 400 else "error"
        return response

    except Exception:
        logging.exception("request_exception request_id=%s", request_id)
        raise

    finally:
        elapsed_ms = round(
            (time.perf_counter() - start) * 1000, 2
        )

        logging.info(
            "request_id=%s client_ip=%s timestamp=%s "
            "method=%s path=%s action=%s account=%s "
            "status_code=%s result=%s latency_ms=%s",
            request_id,
            client_ip,
            timestamp,
            request.method,
            path,
            getattr(request.state, "action", action),
            getattr(request.state, "account", account),
            status_code,
            result,
            elapsed_ms,
        )


@app.get("/")
def home():
    return {"message": "Banking server is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/balance/{account}")
def balance(account: str):
    with db_lock:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT balance FROM accounts WHERE account = ?",
                (account,),
            ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return {
        "status": "success",
        "account": account,
        "balance": row["balance"],
    }


@app.post("/transaction")
def transaction(data: TransactionRequest, request: Request):
    request.state.action = data.action
    request.state.account = data.account

    if data.action not in ("deposit", "withdraw"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported operation",
        )

    if data.amount is None:
        raise HTTPException(
            status_code=400,
            detail="Amount is required",
        )

    with db_lock:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")

            row = connection.execute(
                "SELECT balance FROM accounts WHERE account = ?",
                (data.account,),
            ).fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Account not found",
                )

            balance_now = row["balance"]

            if (
                data.action == "withdraw"
                and balance_now < data.amount
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient funds",
                )

            if data.action == "deposit":
                new_balance = balance_now + data.amount
            else:
                new_balance = balance_now - data.amount

            connection.execute(
                "UPDATE accounts SET balance = ? WHERE account = ?",
                (new_balance, data.account),
            )

    return {
        "status": "success",
        "account": data.account,
        "action": data.action,
        "balance": new_balance,
    }
