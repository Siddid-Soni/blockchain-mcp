#!/usr/bin/env python3
"""
Main entry point for the blockchain vulnerability analyzer MCP server.
This allows the package to be run with `python -m blockchain_vuln_analyzer`.
"""

from .server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())