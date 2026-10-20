
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVER_URL = "http://192.168.56.101:8000"
ACCOUNT = "A1001"
AMOUNT = 10
REQUEST_COUNT = 10


def send_request(path, data=None):
    body = None
    headers = {}

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        SERVER_URL + path,
        data=body,
        headers=headers,
        method="POST" if data is not None else "GET"
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def deposit(number):
    result = send_request("/transaction", {
        "action": "deposit",
        "account": ACCOUNT,
        "amount": AMOUNT
    })
    return number, result


def main():
    before = send_request(f"/balance/{ACCOUNT}")["balance"]
    successes = 0
    errors = []

    with ThreadPoolExecutor(max_workers=REQUEST_COUNT) as executor:
        futures = [
            executor.submit(deposit, number)
            for number in range(1, REQUEST_COUNT + 1)
        ]

        for future in as_completed(futures):
            try:
                number, result = future.result()
                successes += 1
                print(f"Request {number}: {result['status']}")
            except Exception as error:
                errors.append(str(error))

    after = send_request(f"/balance/{ACCOUNT}")["balance"]
    expected = before + successes * AMOUNT

    print("\nRequests sent:", REQUEST_COUNT)
    print("Successful deposits:", successes)
    print("Errors:", len(errors))
    print("Balance before:", before)
    print("Balance after:", after)
    print("Expected balance:", expected)
    print("Balance check:", "PASS" if abs(after - expected) < 0.001 else "FAIL")

    for error in errors:
        print("Error:", error)


if __name__ == "__main__":
    main()
