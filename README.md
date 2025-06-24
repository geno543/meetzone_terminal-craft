# Meet-Zone

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A professional terminal application for identifying optimal meeting times across multiple time zones with **busy schedule management**. Meet-Zone streamlines the scheduling process for distributed teams with an intuitive interface built on the Textual framework.

## Overview

Meet-Zone solves the challenge of coordinating meetings across global teams by:

- Analyzing participant availability across different time zones
- **Managing busy schedules and unavailable times for each participant**
- Identifying optimal meeting slots that maximize attendance while avoiding conflicts
- Providing a clear, ranked list of potential meeting times
- Supporting both command-line and interactive interfaces

## ✨ New Features

### 🗓️ Busy Schedule Management
- **Add busy time slots** for each participant (meetings, lunch, appointments, etc.)
- **Recurring schedules** (e.g., "every Monday 10:00-11:00 for team standup")
- **Specific date conflicts** (e.g., "December 25th unavailable")
- **Daily recurring slots** (e.g., "lunch break 12:00-13:00 every day")
- **Automatic conflict detection** - the algorithm excludes busy participants from meeting slots

### 📊 Enhanced Algorithm
- **Smarter availability calculation** that considers both working hours and busy schedules
- **Time-of-day scoring** that prefers business hours (9 AM - 5 PM UTC)
- **Improved conflict resolution** with better participant matching
- **More accurate results** with comprehensive availability analysis

## Installation

### From Releases

The easiest way to install Meet-Zone is to download the pre-built executable for your platform from the [Releases page](https://github.com/yourusername/meet-zone/releases).

1. Download the appropriate file for your operating system:
   - Windows: `meet-zone-windows.exe`
   - macOS: `meet-zone-macos`
   - Linux: `meet-zone-linux`

2. Verify the file integrity using the provided SHA256 checksum:
   ```bash
   # Windows (PowerShell)
   Get-FileHash -Algorithm SHA256 meet-zone-windows.exe | Format-List
   
   # macOS/Linux
   shasum -a 256 meet-zone-macos  # or meet-zone-linux
   ```

3. Make the file executable (macOS/Linux only):
   ```bash
   chmod +x meet-zone-macos  # or meet-zone-linux
   ```

4. Run the application:
   ```bash
   # Windows
   .\meet-zone-windows.exe
   
   # macOS/Linux
   ./meet-zone-macos  # or ./meet-zone-linux
   ```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/meet-zone.git
cd meet-zone

# Install the package in development mode
python -m pip install -e .
```

## Requirements

- Python 3.10+
- Dependencies:
  - textual >= 0.38.1
  - pytz >= 2023.3
  - zoneinfo (for Python < 3.9)

## Usage

### Command Line Interface

```bash
# Launch with empty UI (add participants manually)
python -m meet_zone

# Load participants from CSV file (with busy schedules)
python -m meet_zone roster.csv

# Specify minimum meeting duration
python -m meet_zone roster.csv --duration 45

# Display top N meeting slots
python -m meet_zone roster.csv --top 5

# Show options for the entire week
python -m meet_zone roster.csv --week

# Prioritize by duration instead of participant count
python -m meet_zone roster.csv --prioritize duration

# Specify start date for search
python -m meet_zone roster.csv --date 2023-12-01
```

### CSV Format with Busy Schedules

Participant data can now include busy schedule information:

```csv
name,timezone,start_time,end_time,busy_schedule
Alice,America/New_York,09:00,17:00,10:00-11:00@Mon:Team standup;14:00-15:00:Daily review
Bob,Europe/London,08:30,16:30,09:00-10:00@2024-01-15:Doctor appointment;13:00-14:00@Fri:Team lunch
Charlie,Asia/Tokyo,10:00,18:00,11:00-12:00:Lunch break;16:00-17:00@Wed:Client call
```

#### Busy Schedule Format

The busy schedule field supports multiple formats:

- **Daily recurring**: `09:00-10:00` (applies every day)
- **Specific date**: `09:00-10:00@2024-01-15` (only on that date)
- **Weekly recurring**: `09:00-10:00@Mon` (every Monday)
- **With description**: `09:00-10:00@Mon:Team standup`
- **Multiple slots**: `09:00-10:00;14:00-15:00` (separated by semicolons)

#### Day Names for Recurring Schedules
- `Mon`, `Monday` - Monday
- `Tue`, `Tuesday` - Tuesday  
- `Wed`, `Wednesday` - Wednesday
- `Thu`, `Thursday` - Thursday
- `Fri`, `Friday` - Friday
- `Sat`, `Saturday` - Saturday
- `Sun`, `Sunday` - Sunday

## Application Interface

The application provides a tabbed interface with three main sections:

### 1. Participants Management
- Add participants with name, timezone, and working hours
- View all participants in a tabular format with busy schedule summaries
- Remove selected participants or clear all entries

### 2. 🆕 Busy Schedule Management
- **Select participants** from dropdown to manage their busy times
- **Add busy slots** with start/end times, optional dates, and descriptions
- **Set recurring schedules** (weekly) or specific date conflicts
- **View comprehensive busy schedule table** for all participants
- **Remove or clear** busy schedule entries

### 3. Meeting Time Finder
- Configure meeting parameters:
  - Minimum duration
  - Number of results to display
  - Date range (today or full week)
  - Prioritization strategy (participants vs. duration)
- View results with detailed information:
  - Start and end times (UTC)
  - Meeting duration
  - Participant count and percentage
  - List of available participants
  - **Busy schedules are automatically considered**

## How Busy Schedules Work

### Algorithm Integration
1. **Availability Check**: For each time slot, the algorithm checks if participants are within their working hours
2. **Busy Schedule Filter**: It then excludes participants who have busy slots during that time
3. **Smart Matching**: Only participants who are both available (working hours) and not busy are included in meeting slots
4. **Conflict Resolution**: The algorithm automatically finds times when the maximum number of people are free

### Time Zone Handling
- Busy schedules are specified in the participant's local time zone
- The algorithm converts everything to UTC for comparison
- Results show UTC times but consider local busy schedules

### Example Scenario
```
Alice (New York): Working 9:00-17:00, Busy 10:00-11:00 (Team standup)
Bob (London): Working 8:30-16:30, Busy 13:00-14:00 (Lunch)
Charlie (Tokyo): Working 10:00-18:00, Busy 11:00-12:00 (Lunch)

The algorithm will find meeting times when:
- All participants are in their working hours
- None of them have conflicting busy schedules
- Maximum participation is achieved
```

## Architecture

Meet-Zone is built with a modular architecture:

- `parser.py`: Handles CSV parsing, participant data structures, and busy schedule parsing
- `scheduler.py`: Implements the core scheduling algorithm with busy schedule integration
- `ui.py`: Provides the Textual-based user interface with busy schedule management
- `__main__.py`: Entry point with command-line argument handling

## Building from Source

To build the executable from source:

1. Install PyInstaller and other build dependencies:
   ```bash
   python -m pip install pyinstaller cairosvg pillow
   ```

2. Build the executable:
   ```bash
   # Windows
   pyinstaller --name="meet-zone-windows" --onefile --windowed --icon=icon.ico --add-data="roster.csv;." --hidden-import=zoneinfo.tzpath src/meet_zone/__main__.py
   
   # macOS
   pyinstaller --name="meet-zone-macos" --onefile --windowed --icon=icon.png --add-data="roster.csv:." --hidden-import=zoneinfo.tzpath src/meet_zone/__main__.py
   
   # Linux
   pyinstaller --name="meet-zone-linux" --onefile --windowed --icon=icon.png --add-data="roster.csv:." --hidden-import=zoneinfo.tzpath src/meet_zone/__main__.py
   ```

## Tips for Using Busy Schedules

### Best Practices
1. **Be Specific**: Add descriptions to busy slots (e.g., "Client call", "Lunch break")
2. **Use Recurring Schedules**: Set up weekly recurring meetings to avoid conflicts
3. **Plan Ahead**: Add known conflicts (vacations, appointments) with specific dates
4. **Regular Updates**: Keep busy schedules current for best results

### Common Patterns
- **Daily lunch**: `12:00-13:00:Lunch break`
- **Weekly meetings**: `10:00-11:00@Mon:Team standup`
- **Specific appointments**: `14:00-15:00@2024-01-15:Doctor appointment`
- **Multiple conflicts**: `09:00-10:00@Mon:Standup;15:00-16:00@Fri:Retrospective`

## Versioning

This project follows [Semantic Versioning](https://semver.org/). For the versions available, see the [tags on this repository](https://github.com/yourusername/meet-zone/tags).

## Changelog

See the [CHANGELOG.md](CHANGELOG.md) file for details on version history and changes.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Project Link: [https://github.com/yourusername/meet-zone](https://github.com/yourusername/meet-zone)