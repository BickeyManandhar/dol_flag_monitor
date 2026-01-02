#!/bin/bash

# Build script for FLAG Monitor Lambda deployment
# This creates the Lambda function zip and dependencies layer

set -e

echo "=========================================="
echo "Building FLAG Monitor Lambda Package"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

echo -e "${BLUE}Step 1: Creating Lambda function zip...${NC}"

# Create temporary directory for Lambda function
rm -rf build
mkdir -p build/lambda

# Copy Lambda function code
cp ../flag_monitor/lambda_function.py build/lambda/

# Create zip file for Lambda function
cd build/lambda
zip -q ../../lambda_function.zip lambda_function.py
cd ../..

echo -e "${GREEN}✓ Lambda function package created: lambda_function.zip${NC}"

echo -e "${BLUE}Step 2: Creating Lambda Layer with dependencies...${NC}"

# Create directory for layer
mkdir -p build/layer/python

# Install dependencies into layer directory
pip install -q \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    -t build/layer/python \
    --upgrade

# Create layer zip
cd build/layer
zip -qr ../../lambda_layer.zip python
cd ../..

echo -e "${GREEN}✓ Lambda layer package created: lambda_layer.zip${NC}"

# Cleanup
rm -rf build

echo ""
echo "=========================================="
echo -e "${GREEN}Build Complete!${NC}"
echo "=========================================="
echo ""
echo "Created files:"
echo "  - lambda_function.zip (Lambda function code)"
echo "  - lambda_layer.zip (Dependencies: requests, beautifulsoup4)"
echo ""
echo "Next steps:"
echo "  1. Configure terraform.tfvars with your email"
echo "  2. Run: terraform init"
echo "  3. Run: terraform plan"
echo "  4. Run: terraform apply"
echo ""
