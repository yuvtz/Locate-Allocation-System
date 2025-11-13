from fastapi import FastAPI
from typing import Dict
import uvicorn
import random

app = FastAPI()


@app.post("/request_locates")
def request_locates_endpoint(requested: Dict[str, int]) -> Dict[str, int]:
    """
    Simulates an external server with variable approval rates.
    It randomly approves between 0% to 200% of the requested amount.
    This helps test the client's logic for both scarcity and over-supply.
    """
    print(f"Server received request: {requested}")

    approved = {}
    for symbol, amount in requested.items():
        # Random approval rate between 0 (0%) and 2 (200%)
        approval_rate = random.uniform(0, 2)
        approved_amount = int(amount * approval_rate)

        # Debug print to see what ratio was chosen
        print(f"  > Processing {symbol}: Rate {approval_rate:.2f} | Requested {amount} -> Approved {approved_amount}")

        approved[symbol] = approved_amount

    print(f"Server sending response: {approved}")
    return approved


if __name__ == "__main__":
    print("Randomized Server started on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)