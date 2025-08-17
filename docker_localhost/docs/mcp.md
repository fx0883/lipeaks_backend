npx @agentdeskai/browser-tools-server@latest


npx @agentdeskai/browser-tools-mcp







{
  "mcpServers": {
    "browser-tools": {
      "command": "c:\\Windows\\System32\\cmd.exe",
      "args": [
        "cmd /c npx -y @agentdeskai/browser-tools-mcp@latest"
      ],
      "enabled": true
    },
    "mysql": {
      "command": "npx",
      "args": [
        "-y",
        "@benborla29/mcp-server-mysql"
      ],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASS": "123456",
        "MYSQL_DB": "multi_tenant_db",
        "ALLOW_INSERT_OPERATION": "true",
        "ALLOW_UPDATE_OPERATION": "true",
        "ALLOW_DELETE_OPERATION": "true",
        "ALLOW_DDL_OPERATION": "true"
      }
    },
    "context7": {
      "url": "https://mcp.context7.com/mcp"
    },
    "browsermcp": {
      "command": "npx",
      "args": [
        "@browsermcp/mcp@latest"
      ]
    }
  }
}

