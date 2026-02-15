#!/bin/bash

# ArXiv MCP Server Setup Script
# This script sets up the development environment for the ArXiv MCP server

echo "Setting up ArXiv MCP Server environment..."

# Check if Python 3.10+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -e .

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set your API keys:"
echo "   export OPENAI_API_KEY='your-openai-key'"
echo "   export ANTHROPIC_API_KEY='your-anthropic-key'"
echo "3. Test the server: arxiv-mcp"
echo ""
