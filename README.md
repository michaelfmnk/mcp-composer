
# MCP Composer

A multi-tenant MCP (Model Context Protocol) server that aggregates and manages multiple MCP servers for different users, enabling secure access through Google OAuth authentication.

## Overview

MCP Composer acts as a centralized proxy that allows multiple users to configure and access their own MCP servers through a single endpoint. Each user authenticates via Google OAuth and only sees their own configured tools and resources.

## Key Features

- **Multi-tenant Architecture**: Each user has their own isolated MCP server configurations
- **Google OAuth Authentication**: OAuth 2.1 flow integrated with Claude.AI
- **Flexible Server Support**: Compatible with both HTTP and stdio-based MCP servers
- **MongoDB**: User configurations and OAuth tokens are stored in MongoDB
- **MCP Isolation**: Security middleware makes sure that users can access only their own MCPs

## Use Cases

- Share a single MCP endpoint across multiple team members with Claude.AI
- Maintain separate tool configurations per user while using a common infrastructure
- Secure access to private MCP with Google OAuth

## Architecture

The project follows a clean architecture with dependency injection and no global state:

```text
src/mcp_composer/
    auth/          # OAuth providers and security middleware
    database/      # MongoDB client and repositories
    server/        # MCP server management and proxy clients
    app.py         # Main application with dependency injection
    config.py      # Environment-based configuration
    models.py      # Pydantic data models
    main.py        # Application entry point
```

Key components:
- **McpComposerApp**: Manages application lifecycle and dependency injection
- **MCPServerManager**: Orchestrates server creation and user configuration loading
- **SecurityFilterMiddleware**: Filters tools based on authenticated user
- **CustomProxyClient**: Tracks tool ownership for multi-tenant isolation

## Quick Start

### Prerequisites

- Python 3.14+
- MongoDB instance
- Google OAuth credentials ([setup guide](https://console.cloud.google.com/)) - in case using Google OAuth

### Local Development

1. Clone the repository:
```bash
git clone git@github.com:michaelfmnk/mcp-composer.git
cd mcp-composer
```

2. Create a `.env` file with required configuration:
```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
BASE_URL=http://localhost:8000
MONGODB_URI=mongodb://localhost:27017
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_TRANSPORT=http
```

3. Install dependencies and run:
```bash
uv sync
uv run mcp-composer
```

The server will start on `http://localhost:8000`.

#### Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
services:
  mcp-composer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - BASE_URL=http://localhost:8000
      - MONGODB_URI=mongodb://mongodb:27017
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
      - MCP_TRANSPORT=http
      - MONGODB_DATABASE=mcp_composer
      - AUTH_PROVIDER=google  # or "none" to disable auth
      - MCP_COMPOSITION_MODE=live  # or "static"
    depends_on:
      - mongodb
    networks:
      - mcp-network

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - mcp-network

volumes:
  mongodb_data:

networks:
  mcp-network:
```

#### Building the Docker Image

```bash
# Build the image
docker build -t mcp-composer .

# Run manually (requires MongoDB running separately)
docker run -p 8000:8000 \
  -e GOOGLE_CLIENT_ID=your_client_id \
  -e GOOGLE_CLIENT_SECRET=your_client_secret \
  -e BASE_URL=http://localhost:8000 \
  -e MONGODB_URI=mongodb://host.docker.internal:27017 \
  mcp-composer
```

## Configuration

### User MCP Server Configuration

User configurations are stored in MongoDB with the following structure:

```json
{
  "_id": "user@example.com",
  "mcpServers": {
    "http-server": {
      "url": "https://example.com/mcp"
    },
    "stdio-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_PATHS": "/home/user/documents"
      }
    }
  },
  "prompts": [
    {
      "name": "/custom-prompt",
      "message": "Your prompt content here",
      "title": "Custom Prompt",
      "description": "Description of what this prompt provides",
      "enabled": true
    }
  ]
}
```

**MCP Server Configuration Options:**
- **HTTP-based servers**: Use `url` field pointing to the MCP server endpoint
- **stdio-based servers**: Use `command`, `args`, and optional `env` fields
- **Prompts**: Optional array of custom prompts to attach to the user's MCP servers

### Environment Variables

Required:
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `BASE_URL` - Base URL for OAuth callbacks
- `MONGODB_URI` - MongoDB connection string

Optional:
- `AUTH_PROVIDER` - Authentication provider: "google" or "none" (default: "google")
- `MCP_HOST` - Server host address (default: "0.0.0.0")
- `MCP_PORT` - Server port (default: 8000)
- `MCP_TRANSPORT` - Transport protocol: "stdio", "http", "sse", or "streamable-http" (default: "http")
- `MONGODB_DATABASE` - Database name (default: "mcp_composer")
- `MCP_COMPOSITION_MODE` - Composition mode: "live" or "static" (default: "live")
  - `live`: Uses `mcp.mount()` for dynamic mounting, preserves full proxy behavior
  - `static`: Uses `mcp.import_server()` for static import, better for performance

## Usage

### With Claude.AI

1. Start the MCP Composer server (locally or via Docker)
2. Add your MCP Composer endpoint to Claude.AI's MCP settings
3. Authenticate with Google OAuth when prompted (you might need to refresh the page)
4. Your configured tools, prompts, and resources will now be available in Claude.AI

Each user's tools are isolated and only visible to them after authentication.

### Managing User Configurations

User configurations are stored in MongoDB. You can add or update configurations directly in the database:

```bash
# Connect to MongoDB
mongosh mongodb://localhost:27017/mcp_composer

# Insert or update a user configuration
db.mcp_configs.updateOne(
  { "_id": "user@example.com" },
  {
    "$set": {
      "mcpServers": {
        "my-server": {
          "url": "https://example.com/mcp"
        }
      }
    }
  },
  { upsert: true }
)

# View all configurations
db.mcp_configs.find().pretty()
```

## Security Considerations

- OAuth tokens are stored in MongoDB (in `mcp_clients` collection)
- Tools, prompts, and resources are filtered per user through `SecurityFilterMiddleware`
- Each user can only see their own configured MCP servers based on JWT email claim
- Custom prompts are user-specific and filtered alongside tools

**Important**: ⚠️ The current middleware implementation is designed for tool segregation and development purposes. For production use, consider:
- Implementing additional security layers (rate limiting, request validation, etc.)
- Using encrypted connections for MongoDB
- Securing the OAuth callback endpoint
- Implementing proper logging and monitoring
- Setting up HTTPS/TLS for the MCP endpoint

## Development

### Project Structure

```
src/mcp_composer/
├── auth/
│   ├── middleware.py       # SecurityFilterMiddleware for tool filtering
│   └── providers.py        # Google OAuth provider configuration
├── database/
│   ├── client.py           # MongoDB client wrapper
│   ├── repository.py       # User configuration repository
│   ├── clients_repository.py # OAuth client data repository
│   └── storage.py          # Storage adapter for FastMCP
├── server/
│   ├── manager.py          # MCP server lifecycle management
│   └── proxy_client.py     # Custom proxy client with owner tracking
├── app.py                  # Main application class
├── config.py               # Configuration models
├── models.py               # Pydantic data models
└── main.py                 # Entry point
```

### Adding Features

When extending MCP Composer:
- Follow the dependency injection pattern - no global state
- Use repositories for all database access
- Add new middleware by extending `Middleware` from FastMCP
- Keep authentication and authorization separate
- Update `UserMCPConfig` model for new configuration options

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.