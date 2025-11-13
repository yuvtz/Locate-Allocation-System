# Locate Allocation System

A robust stock-locate allocation system simulating a real-world trading environment.
The system aggregates client locate requests, queries an external approval server, and distributes approved locates proportionally while prioritizing round lots (blocks of 100) for optimal trading efficiency.

## Features

### Client–Server Architecture
Simulates interaction with an external liquidity provider (mock broker). The server introduces volatility by **randomizing approval rates (0%–200%)**, forcing the client to handle both scarcity and over-supply scenarios.

### Smart Allocation Algorithm
A multi-pass algorithm designed for fairness and efficiency:
1.  **Guardrails:** Caps allocations at the requested amount (prevents server over-supply).
2.  **Round-Lot Prioritization:** Maximizes 100-share chunks based on mathematical proximity to the next block.
3.  **Fair Dust Distribution:** Distributes remaining shares (<100) to clients with the highest "deprivation" (largest gap between fair share and actual allocation).

### Robust Error Handling
- **Zero-Division Protection:** Handles empty or zero-sum requests safely.
- **Input Validation:** Gracefully processes CSV data.
- **Latency Simulation:** Handles server response delays realistically.

## Project Structure

```
.
├── server.py              # Mock API (FastAPI) simulating broker inventory & volatility
├── client.py              # Main Engine: Aggregation, API communication, & Allocation Logic
├── tests.py               # Unit tests covering edge cases
├── requests.csv           # Input data (client requests)
└── requirements.txt       # Project dependencies
```

## File Descriptions

- **server.py**
  A FastAPI server simulating a liquidity provider. It randomly approves between **50% and 120%** of requested amounts to test the client's "Guardrail" logic and scarcity handling.

- **client.py**
  The core application logic:
  - Aggregates raw requests by symbol.
  - Queries the server using HTTP POST.
  - Executes the **`distribute_logic`** algorithm.
  - Exports the final distribution to `approved_locates.csv`.

- **tests.py**
  Comprehensive `unittest` suite verifying:
  - **Chunk Optimization:** Ensuring 100-blocks are prioritized.
  - **Fairness:** Verifying tie-breaking logic.
  - **Edge Cases:** Handling zero requests, micro-requests (<100), and massive over-approvals.

## Setup & Installation

### 1. Prerequisites
- Python 3.7+

### 2. Install Dependencies
```bash
pip install -r requirements.txt


```
## How to Run
The system operates in a Client-Server model. You need two terminal windows.

### Step 1: Start the Server
Open the first terminal and run:

```bash
python server.py
``` 
Output: Randomized Server started on http://127.0.0.1:8000

### Step 2: Run the Client
Open a second terminal and run:

```bash
python client.py
``` 
The client will read requests.csv, query the server, and print the process logs.

### Step 3: View Results
Open the newly created file approved_locates.csv to see the final allocation.

## Running Tests
```bash
python tests.py
```

## Summary
This project demonstrates:

- *Algorithmic Trading Logic:* Balancing math fairness with business constraints (Round Lots).

- *System Resilience:* Handling unpredictable external APIs (randomized approvals).

- *Clean Architecture:* Separation of concerns between data, logic, and networking. 
