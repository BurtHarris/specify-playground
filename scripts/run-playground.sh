#!/bin/bash

# This script sets up the environment and runs the playground tests.

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Install dependencies
pnpm install

# Run the playground tests
pnpm test

# Optionally, run any additional setup or commands needed for the playground
echo "Playground environment is set up and tests have been executed."