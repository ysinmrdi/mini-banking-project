
import json
import urllib.request
import urllib.error

SERVER_URL = "http://192.168.56.101:8000"


def send_request(path, method="GET", data=None):
    url = f"{SERVER_URL}{path}"
    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(json.dumps(result, indent=2))
    except urllib.error.HTTPError as error:
        print("Request failed:", error.code)
        print(error.read().decode("utf-8"))
    except urllib.error.URLError as error:
        print("Connection error:", error.reason)


def main():
    print("Yasin Banking Client")
    print("1. Check balance")
    print("2. Deposit")
    print("3. Withdraw")

    choice = input("Choose an option: ").strip()
    account = input("Account number: ").strip()

    if choice == "1":
        send_request(f"/balance/{account}")

    elif choice in ("2", "3"):
        try:
            amount = float(input("Amount: "))
            if amount <= 0:
                print("Amount must be greater than zero.")
                return
        except ValueError:
            print("Please enter a valid number.")
            return

        action = "deposit" if choice == "2" else "withdraw"

        send_request(
            "/transaction",
            method="POST",
            data={
                "action": action,
                "account": account,
                "amount": amount
            }
        )

    else:
        print("Invalid option.")


if __name__ == "__main__":
    main()
