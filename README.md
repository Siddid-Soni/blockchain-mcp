## Running with Docker

You can run the Blockchain Vulnerability Analyzer MCP Server in a fully containerized environment using Docker and Docker Compose. This setup ensures all required analysis tools and dependencies are installed in the correct versions, as specified in the provided Dockerfile.

### Requirements

- **Docker** and **Docker Compose** installed on your system
- No additional environment variables are required by default
- No ports are exposed, as the MCP server communicates over stdio (not a network port)

### Build and Run

1. **Build the Docker image and start the service:**

```bash
docker compose up --build
```

This will:
- Build the image using Python 3.10-slim as the base
- Install all required system dependencies and analysis tools (Mythril, Slither, Manticore, SmartCheck, Echidna, Maian, solc, etc.)
- Set up the Python environment and install all Python dependencies
- Run the MCP server as the container's entrypoint

2. **Service Details:**
- The service is named `python-mcp-server` in the compose file
- No ports are exposed or mapped, as the server runs over stdio
- No persistent volumes or external services are required

3. **Configuration:**
- No environment variables are required by default
- If you need to pass a `.env` file, uncomment the `env_file` line in the `docker-compose.yml`
- For debugging or advanced usage, refer to the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) section above

4. **Stopping the Service:**

```bash
docker compose down
```

---

This Docker setup provides a reproducible environment for running the MCP server and all its analysis tools, with no manual installation required. For development or advanced configuration, you can modify the Dockerfile or compose file as needed.