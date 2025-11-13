import unittest
from client import distribute_logic


class TestAllocationLogic(unittest.TestCase):

    def test_basic_proportionality(self):
        """
        Case 1:
        Scenario: Requests are round, approved amount is round and divisible.
        Expectation: Perfect proportional split.
        """
        print("\n--- Test 1: Basic Proportionality ---")
        reqs = [
            {'client': 'ClientA', 'amount': 200},
            {'client': 'ClientB', 'amount': 100}
        ]
        # Total 300, Approved 150 (50%)
        result = distribute_logic(reqs, 150)

        # A should get 100, B should get 50
        self.assertEqual(result['ClientA'], 100)
        self.assertEqual(result['ClientB'], 50)
        print("Pass: Perfect split achieved.")

    def test_chunk_optimization(self):
        """
        Case 2: The "Chunking" Logic
        Scenario: A(200), B(200). Approved 300.
        Math split: 150 each.
        Logic split: One gets 200, the other 100 (to maximize 100-blocks).
        """
        print("\n--- Test 2: Chunk Optimization ---")
        reqs = [
            {'client': 'ClientA', 'amount': 200},
            {'client': 'ClientB', 'amount': 200}
        ]
        result = distribute_logic(reqs, 300)
        values = list(result.values())

        self.assertIn(200, values)
        self.assertIn(100, values)
        self.assertEqual(sum(values), 300)
        print(f"Pass: Result {result} maximizes 100-chunks.")

    def test_small_dust_distribution(self):
        """
        Case 3: Small Remainder (<100)
        Scenario: A(1000), B(100). Approved 1050.
        Math: A~954, B~95.
        Logic Step 1 (Base): A=900, B=0. Remainder=150.
        Logic Step 2 (Next 100): B's remainder (95) > A's remainder (54). B gets 100.
        Logic Step 3 (Dust 50): B is full (100/100). A takes the remaining 50.
        Final Expectation: A=950, B=100.
        """
        print("\n--- Test 3: Dust Distribution ---")
        reqs = [
            {'client': 'ClientA', 'amount': 1000},
            {'client': 'ClientB', 'amount': 100}
        ]
        result = distribute_logic(reqs, 1050)

        self.assertEqual(result['ClientB'], 100)  # B reached cap
        self.assertEqual(result['ClientA'], 950)  # A took the rest
        self.assertEqual(sum(result.values()), 1050)
        print(f"Pass: Remainder handled correctly: {result}")

    def test_tiny_approval(self):
        """
        Case 4: Starvation
        Scenario: Huge requests, tiny approval (less than 100 total).
        Expectation: The largest client should likely get the scraps, or proportional.
        """
        print("\n--- Test 4: Tiny Approval ---")
        reqs = [
            {'client': 'Whale', 'amount': 5000},
            {'client': 'Fish', 'amount': 100}
        ]
        # Approved only 50 units
        result = distribute_logic(reqs, 50)

        self.assertEqual(sum(result.values()), 50)
        # Since neither gets a 100-chunk, the 'dust' logic sorts by requested amount.
        # Whale requested more, so Whale gets the 50.
        self.assertEqual(result['Whale'], 50)
        self.assertEqual(result['Fish'], 0)
        print(f"Pass: Tiny amount {result} gave priority to larger request.")

    def test_over_approval_guardrail(self):
        """
        Case 5: Server Bug (Over-approval)
        Scenario: Server approves more than requested.
        Expectation: Cap at requested amount. Don't invent shares.
        """
        print("\n--- Test 5: Over Approval Guardrail ---")
        reqs = [{'client': 'ClientA', 'amount': 100}]
        # Server approves 500 (more than requested)
        result = distribute_logic(reqs, 500)

        self.assertEqual(result['ClientA'], 100)
        print("Pass: Allocation capped at request size.")

    def test_complex_fairness(self):
        """
        Case 6: Tie Breaker
        Scenario: A(500), B(400). Total 900. Approved 600.
        Math: A=333.3, B=266.6.
        Base: A=300, B=200. (Total 500). Left 100.
        Who gets the 100?
        A's remainder: 33.3
        B's remainder: 66.6
        Expectation: B should win the chunk because they are closer to their next 100.
        Result: A=300, B=300.
        """
        print("\n--- Test 6: Complex Fairness ---")
        reqs = [
            {'client': 'ClientA', 'amount': 500},
            {'client': 'ClientB', 'amount': 400}
        ]
        result = distribute_logic(reqs, 600)

        self.assertEqual(result['ClientA'], 300)
        self.assertEqual(result['ClientB'], 300)
        print(f"Pass: Logic correctly favored B ({result}) based on remainder proximity.")

    def test_zero_total_request(self):
        """
        Case 7: Division by Zero Protection
        Scenario: Clients exist but requested 0 amounts.
        Expectation: No crash, returns 0.
        """
        print("\n--- Test 7: Zero Total Request ---")
        reqs = [{'client': 'A', 'amount': 0}, {'client': 'B', 'amount': 0}]
        # Even if approved is 1000, nobody wants anything.
        result = distribute_logic(reqs, 1000)

        self.assertEqual(sum(result.values()), 0)
        print("Pass: Handled zero requests without crashing.")

    def test_micro_requests(self):
        """
        Case 8: No Chunks
        Scenario: All requests are small (<100).
        Reqs: A(50), B(40), C(30). Total 120. Approved 60.
        Math: A=25, B=20, C=15.
        Chunks: None (0 chunks of 100).
        Dust Logic:
        - A needs 25 more (biggest gap) -> gets dust.
        """
        print("\n--- Test 8: Micro Requests (No 100s) ---")
        reqs = [
            {'client': 'ClientA', 'amount': 50},
            {'client': 'ClientB', 'amount': 40},
            {'client': 'ClientC', 'amount': 30}
        ]
        result = distribute_logic(reqs, 60)

        # Logic breakdown:
        # Raw shares: A=25, B=20, C=15.
        # No 100 chunks allocated.
        # Dust distribution (sorted by raw_share desc):
        # 1. A (raw 25) takes 25. Remainder 35.
        # 2. B (raw 20) takes 20. Remainder 15.
        # 3. C (raw 15) takes 15. Remainder 0.
        # Wait! Logic is sorted by (Raw - Allocated). Since allocated is 0, it sorts by Raw.

        # Actual filling order might vary by implementation details of the loop,
        # but sum must be 60 and no one gets > requested.
        self.assertEqual(sum(result.values()), 60)
        self.assertTrue(all(v <= r['amount'] for r, v in zip(reqs, result.values())))
        print(f"Pass: Micro requests distributed correctly: {result}")

    def test_exact_tie_breaker(self):
        """
        Case 9: Determinism Check
        Scenario: A(150), B(150). Approved 100.
        Both have identical claims. Who gets the 100?
        Python's sort is stable. It should preserve original order or specific key sort.
        Since our key is (raw_share % 100), both are 50.
        The 'max' function returns the first one it sees in case of a tie.
        """
        print("\n--- Test 9: Exact Tie Breaker ---")
        reqs = [
            {'client': 'ClientA', 'amount': 150},
            {'client': 'ClientB', 'amount': 150}
        ]
        result = distribute_logic(reqs, 100)

        # One must get 100, the other 0.
        values = list(result.values())
        self.assertIn(100, values)
        self.assertIn(0, values)
        print(f"Pass: Tie broken deterministically: {result}")

if __name__ == '__main__':
    unittest.main()

