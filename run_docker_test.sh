#!/bin/bash

# Script to test the compiler backend API in a standalone Docker container

echo "Building Docker image for compiler backend..."
docker build -t compiler-backend:latest .

echo "Running Docker container for API server..."
docker run -d --rm -p 5000:5000 --name compiler-backend-api compiler-backend:latest python src/api.py

echo "Waiting for API server to start..."
sleep 5

echo "Testing API connectivity with a simple Pascal program..."
curl -X POST http://localhost:5000/compile \
  -H "Content-Type: application/json" \
  -d '{"program": "program Test; var x: integer; begin x := 5; end."}' \
  | jq .

echo "Stopping Docker container..."
docker stop compiler-backend-api

echo "Test completed."
