#!/bin/bash

# Script to test the compiler system using Docker Compose

echo "Starting Docker Compose services..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 10

echo "Testing API connectivity with a simple Pascal program via Docker Compose setup..."
curl -X POST http://localhost:5000/compile \
  -H "Content-Type: application/json" \
  -d '{"program": "program Test; var x: integer; begin x := 5; end."}' \
  | jq .

echo "Stopping Docker Compose services..."
docker-compose down

echo "Test completed."
