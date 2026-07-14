# GIMP MCP - Claude Desktop + Cursor Setup Guide

## Claude Desktop Setup

1. Install GIMP MCP server:
```bash
npm install -g gimp-mcp
# or
pip install gimp-mcp
```

2. Add to Claude Desktop config (`~/.config/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "gimp-mcp": {
      "command": "npx",
      "args": ["gimp-mcp"]
    }
  }
}
```

3. Restart Claude Desktop

## Cursor Setup

1. Open Cursor Settings → Features → MCP Servers
2. Click "Add new MCP Server"
3. Fill in:
   - Name: `gimp-mcp`
   - Type: `command`
   - Command: `npx gimp-mcp`
4. Click Save

## Verification

Ask Claude/Cursor: "Can you connect to GIMP?"
If it responds with the GIMP version, you're all set.

## Troubleshooting

- Ensure GIMP is running before connecting
- Check that `npx gimp-mcp` works in terminal first
- Restart the IDE after adding the MCP config
