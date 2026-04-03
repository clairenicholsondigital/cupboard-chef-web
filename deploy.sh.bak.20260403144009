#!/bin/bash
set -e

echo "Starting deploy..."
cd /var/www/food-frontend || exit

echo "Pulling latest changes..."
git pull origin main

echo "Validating compose..."
docker compose -f infra/docker-compose.yml config >/dev/null

echo "Stopping old containers..."
docker compose -f infra/docker-compose.yml down

echo "Starting updated containers..."
docker compose -f infra/docker-compose.yml up -d --build

echo "Cleaning unused images..."
docker image prune -f

echo "Deploy complete"
