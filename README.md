# terminal-progress-bar

Shared terminal progress bars for parallel scripts and processes. Track multiple jobs from different terminals or scripts and watch them update in real time.

## Install

```bash
uv tool install .
```

Or from a clone of this repository:

```bash
git clone https://github.com/you/terminal-progress-bar.git
cd terminal-progress-bar
uv tool install .
```

## Usage

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

## Development

```bash
uv sync --group dev
uv run pytest
```

## License

MIT
