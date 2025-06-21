# Meet-Zone

[![Tests](https://github.com/geno543/timezone_terminal-craft/actions/workflows/tests.yml/badge.svg)](https://github.com/geno543/timezone_terminal-craft/actions/workflows/tests.yml)
[![Lint](https://github.com/geno543/timezone_terminal-craft/actions/workflows/lint.yml/badge.svg)](https://github.com/geno543/timezone_terminal-craft/actions/workflows/lint.yml)
[![Documentation](https://github.com/geno543/timezone_terminal-craft/actions/workflows/docs.yml/badge.svg)](https://github.com/geno543/timezone_terminal-craft/actions/workflows/docs.yml)

Meet-Zone is a tool for managing meetings across multiple time zones. It helps you schedule meetings that work for participants around the world.
## Features

- Display meeting times across multiple time zones
- Manage participant rosters with their respective time zones
- Command-line interface for quick access
- Text-based user interface (TUI) for interactive use
- Export meeting schedules to various formats

## Quick Start

### Installation

```bash
pip install meet-zone
```

Or download the pre-built executable for your platform from the [Releases](https://github.com/geno543/timezone_terminal-craft/releases) page.

### Basic Usage

```bash
# Show meeting time in multiple time zones
meet-zone --time "2023-11-15 14:00" --timezone "America/New_York"

# Use the interactive TUI
meet-zone --interactive

# Load a roster of participants
meet-zone --roster path/to/roster.csv --time "2023-11-15 14:00" --timezone "America/New_York"
```

## Documentation

For more detailed information, check out the following sections:

- [Installation](installation.md) - Detailed installation instructions
- [Usage](usage.md) - How to use Meet-Zone
- [Configuration](configuration.md) - Configuration options
- [API Reference](reference/) - API documentation for developers

## Contributing

Contributions are welcome! Please see our [Contributing Guide](contributing.md) for more information.

## License

Meet-Zone is licensed under the MIT License. See the LICENSE file for details.