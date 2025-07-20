#!/usr/bin/env python3
"""
HTTP server entry point for the blockchain vulnerability analyzer.
"""

import asyncio
import argparse
from .http_server import start_server

async def main():
    parser = argparse.ArgumentParser(description="Blockchain Vulnerability Analyzer HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    print(f"Starting Blockchain Vulnerability Analyzer HTTP Server on {args.host}:{args.port}")
    await start_server(host=args.host, port=args.port)

if __name__ == "__main__":
    asyncio.run(main())