import unittest
import requests
import json

class TestFrontendBackendConnectivity(unittest.TestCase):
    def setUp(self):
        self.base_url = 'http://localhost:5000/compile'
        self.headers = {'Content-Type': 'application/json'}

    def test_valid_expression(self):
        """Test sending a valid arithmetic expression and receiving a proper response."""
        expression = '1 + 2 * 3'
        payload = json.dumps({'expression': expression})
        try:
            response = requests.post(self.base_url, headers=self.headers, data=payload)
            self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")
            data = response.json()
            self.assertIn('ast', data, "Response does not contain 'ast' key")
            self.assertIn('intermediate', data, "Response does not contain 'intermediate' key")
            self.assertIn('optimized', data, "Response does not contain 'optimized' key")
            self.assertIn('target', data, "Response does not contain 'target' key")
            print("Test 1: Valid expression connectivity - PASS")
        except requests.exceptions.ConnectionError:
            self.fail("Connection to backend failed. Ensure the API server is running on localhost:5000")

    def test_invalid_expression(self):
        """Test sending an invalid expression and receiving an error response."""
        expression = 'invalid + expression'
        payload = json.dumps({'expression': expression})
        try:
            response = requests.post(self.base_url, headers=self.headers, data=payload)
            self.assertEqual(response.status_code, 400, f"Expected status code 400, got {response.status_code}")
            data = response.json()
            self.assertIn('error', data, "Response does not contain 'error' key")
            print("Test 2: Invalid expression error handling - PASS")
        except requests.exceptions.ConnectionError:
            self.fail("Connection to backend failed. Ensure the API server is running on localhost:5000")

    def test_empty_expression(self):
        """Test sending an empty expression and receiving an error response."""
        expression = ''
        payload = json.dumps({'expression': expression})
        try:
            response = requests.post(self.base_url, headers=self.headers, data=payload)
            self.assertEqual(response.status_code, 400, f"Expected status code 400, got {response.status_code}")
            data = response.json()
            self.assertIn('error', data, "Response does not contain 'error' key")
            print("Test 3: Empty expression error handling - PASS")
        except requests.exceptions.ConnectionError:
            self.fail("Connection to backend failed. Ensure the API server is running on localhost:5000")

if __name__ == '__main__':
    unittest.main()
