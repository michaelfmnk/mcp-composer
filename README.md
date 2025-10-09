
# MCP Composer

A multi-tenant MCP (Model Context Protocol) server that aggregates and manages multiple MCP servers for different users, enabling secure access through Google OAuth authentication.

## Overview

MCP Composer acts as a centralized proxy that allows multiple users to configure and access their own MCP servers through a single endpoint. Each user authenticates via Google OAuth and only sees their own configured tools and resources, making it ideal for team environments or shared Claude.AI deployments.

## Key Features

- **Multi-tenant Architecture**: Each user maintains their own isolated MCP server configurations
- **Google OAuth Authentication**: Secure authentication flow integrated with Claude.AI
- **Flexible Server Support**: Compatible with both HTTP and stdio-based MCP servers
- **MongoDB Storage**: User configurations and OAuth tokens persisted in MongoDB
- **Tool Isolation**: Security middleware ensures users only access their own tools
- **Docker Ready**: Containerized deployment with docker-compose

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

- Python 3.11+
- MongoDB instance
- Google OAuth credentials ([setup guide](https://console.cloud.google.com/))

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

### Docker Deployment

For production deployment with Docker Compose, see the `swarm` directory configuration.

## Configuration

### User MCP Server Configuration

User configurations are stored in MongoDB with the following structure:

```json
{
  "_id": "user@example.com",
  "mcpServers": {
    "my-server": {
      "url": "https://example.com/mcp" 
    },
    "local-tool": {
      "command": "npx",                  
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_PATHS": "/home/user/documents"
      }
    }
  }
}
```

### Environment Variables

Required:
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `BASE_URL` - Base URL for OAuth callbacks
- `MONGODB_URI` - MongoDB connection string

Optional:
- `MCP_HOST` - Server host address (default: "0.0.0.0")
- `MCP_PORT` - Server port (default: 8000)
- `MCP_TRANSPORT` - Transport protocol: "stdio", "http", "sse", or "streamable-http" (default: "http")
- `MONGODB_DATABASE` - Database name (default: "mcp_composer")

## Usage with Claude.AI

1. Start the MCP Composer server
2. Provide Claude.AI with your MCP Composer endpoint
3. Authenticate with Google OAuth (you might need to refresh the page)
4. Now you should be able to see your configured tools

Each user's tools are isolated and only visible to them after authentication.

## Development

### Project Structure

The codebase uses:
- **Dependency Injection**: All components receive dependencies via constructors
- **Repository Pattern**: Clean separation of data access logic
- **Async/Await**: Fully asynchronous for MongoDB and MCP operations
- **Pydantic**: Type-safe configuration and data models

## Security Considerations

- OAuth tokens are stored in MongoDB
- Tools are filtered per user through middleware
- Each user can only see their own configured MCP servers

**Note**: ⚠️ The current middleware is designed for segregation and development purposes.

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.