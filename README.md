# terminal-progress-bar

> One progress, two interfaces: terminal for you, MCP for the AI.

Shared terminal progress bars for parallel scripts and processes. Track multiple jobs from different terminals or scripts and watch them update in real time.

## Install

```bash
uv tool install -e .
```

Or from a clone of this repository:

```bash
git clone https://github.com/you/terminal-progress-bar.git
cd terminal-progress-bar
uv tool install -e .
```

Editable install (`-e`) keeps `tpb` linked to the source tree, so local changes take effect without reinstalling.

## Usage

Run `tpb --help` for an overview, or `tpb <command> --help` for command details
(e.g. `tpb create --help`).

### Create a progress bar

```bash
tpb create backup-db 0 100 "Database backup"
```

### Update progress

```bash
tpb backup-db 35        # set absolute value
tpb backup-db +5        # increment
tpb backup-db -2        # decrement
tpb message backup-db "Importing users table"
```

### Finish or fail

```bash
tpb done backup-db "completed in 2m"
tpb error backup-db "connection timeout"
```

### List, status, remove

```bash
tpb                     # visual progress bars (Rich)
tpb list                # plain text: slug, current, max, status, label
tpb status backup-db    # machine-readable plain text output for one bar
tpb rm backup-db        # remove a bar
```

### Monitor in real time

```bash
tpb monitor
```

The monitor redraws the screen when any progress bar changes. Bars stay visible until removed with `tpb rm`.

## Storage

Each progress bar is stored as a separate JSON file:

```
~/.config/terminal-progress-bar/<slug>.json
```

Example:

```json
{
  "slug": "backup-db",
  "label": "Database backup",
  "current": 35,
  "max": 100,
  "status": "active",
  "status_text": "",
  "created_at": "2026-07-30T12:00:00Z",
  "updated_at": "2026-07-30T12:05:00Z"
}
```

Bars are listed in creation order (`created_at`).

## List output

`tpb list` prints one tab-separated line per bar:

```text
import-data	25	100	active	Import data
backup-db	100	100	done	Database backup
```

Columns: `slug`, `current`, `max`, `status`, `label`, and `status_text` (only when set).

## Status output

`tpb status <slug>` prints plain `key: value` lines for scripting and AI agents:

```text
slug: backup-db
label: Database backup
current: 35
max: 100
status: active
status_text:
created_at: 2026-07-30T12:00:00Z
updated_at: 2026-07-30T12:05:00Z
```

## MCP Server

The package includes an MCP server (`tpb-mcp`) for AI clients to manage progress bars programmatically over stdio.

### Run

After install:

```bash
tpb-mcp
```

From a clone without global install:

```bash
uv run tpb-mcp
```

### Client configuration

Example MCP client config:

```json
{
  "mcpServers": {
    "terminal-progress-bar": {
      "command": "tpb-mcp",
      "args": []
    }
  }
}
```

From the repository:

```json
{
  "mcpServers": {
    "terminal-progress-bar": {
      "command": "uv",
      "args": ["run", "tpb-mcp"],
      "cwd": "/path/to/terminal-progress-bar"
    }
  }
}
```

### Tools

| Tool | Description |
|------|-------------|
| `tpb_create` | Create a progress bar |
| `tpb_update` | Set absolute progress value |
| `tpb_increment` | Increment or decrement progress |
| `tpb_message` | Set status message below the bar |
| `tpb_done` | Mark as completed |
| `tpb_error` | Mark as failed |
| `tpb_remove` | Remove a progress bar |
| `tpb_list` | List all bars (structured JSON) |
| `tpb_get` | Get one bar by slug |

Example flow: `tpb_create` → `tpb_update` / `tpb_increment` → `tpb_message` → `tpb_done`.

Tools return structured JSON (bar fields as dict). The human `tpb monitor` view updates automatically when bars change on disk.

## Development

```bash
uv sync --group dev
uv run pytest
```

## License

MIT
