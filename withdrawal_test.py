
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVER_URL = "http://192.168.56.101:8000"
ACCOUNT = "A1001"
AMOUNT = 100
REQUEST_COUNT = 15


def get_balance():
    request = urllib.request.Request(
        f"{SERVER_URL}/balance/{ACCOUNT}"
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result["balance"]


def withdraw(number):
    data = json.dumps({
        "action": "withdraw",
        "account": ACCOUNT,
        "amount": AMOUNT
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{SERVER_URL}/transaction",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return number, True, result
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        return number, False, body
    except Exception as error:
        return number, False, str(error)


def main():
    before = get_balance()
    successes = 0
    failures = 0

    print("Balance before:", before)
    print("Sending concurrent withdrawals...")

    with ThreadPoolExecutor(max_workers=REQUEST_COUNT) as executor:
        futures = [
            executor.submit(withdraw, i)
            for i in range(1, REQUEST_COUNT + 1)
        ]

        for future in as_completed(futures):
            number, success, result = future.result()

            if success:
                successes += 1
                print(f"Request {number}: SUCCESS")
            else:
                failures += 1
                print(f"Request {number}: FAILED - {result}")

    after = get_balance()
    expected = before - successes * AMOUNT

    print("\nRequests sent:", REQUEST_COUNT)
    print("Successful withdrawals:", successes)
    print("Failed withdrawals:", failures)
    print("Balance before:", before)
    print("Balance after:", after)
    print("Expected balance:", expected)
    print("Balance check:", "PASS" if abs(after - expected) < 0.001 else "FAIL")
    print("Non-negative balance:", "PASS" if after >= 0 else "FAIL")


if __name__ == "__main__":
    main()
