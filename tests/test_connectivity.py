import unittest
import requests
import subprocess
import time
import os

class TestConnectivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the API server before running tests."""
        cls.api_process = subprocess.Popen(['python', 'src/api.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)  # Give the server time to start

    @classmethod
    def tearDownClass(cls):
        """Stop the API server after tests."""
        cls.api_process.terminate()
        cls.api_process.wait()

    def test_frontend_backend_connectivity(self):
        """Test sending a simple Pascal program from frontend to backend and receiving compiler outputs."""
        program = """
program Test;
var
  x: integer;
begin
  x := 5;
end.
"""
        response = requests.post('http://localhost:5000/compile', json={'program': program})
        self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")
        data = response.json()
        self.assertIn('tokens', data, "Response should contain 'tokens' field")
        self.assertIn('symbolTable', data, "Response should contain 'symbolTable' field")
        self.assertIn('intermediate', data, "Response should contain 'intermediate' field")
        self.assertNotIn('error', data, "Response should not contain an 'error' field")

    def test_invalid_program(self):
        """Test sending an invalid Pascal program and receiving an error response."""
        program = "invalid program code"
        response = requests.post('http://localhost:5000/compile', json={'program': program})
        self.assertEqual(response.status_code, 400, f"Expected status code 400, got {response.status_code}")
        data = response.json()
        self.assertIn('error', data, "Response should contain an 'error' field")

    def test_empty_program(self):
        """Test sending an empty program and receiving an error response."""
        program = ""
        response = requests.post('http://localhost:5000/compile', json={'program': program})
        self.assertEqual(response.status_code, 400, f"Expected status code 400, got {response.status_code}")
        data = response.json()
        self.assertIn('error', data, "Response should contain an 'error' field")

if __name__ == '__main__':
    unittest.main()
