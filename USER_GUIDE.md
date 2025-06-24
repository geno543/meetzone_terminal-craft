# Meet-Zone User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Managing Participants](#managing-participants)
3. [🆕 Managing Busy Schedules](#managing-busy-schedules)
4. [Finding Meeting Times](#finding-meeting-times)
5. [Understanding Results](#understanding-results)
6. [Tips and Best Practices](#tips-and-best-practices)
7. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

1. Download the appropriate executable for your operating system from the [Releases page](https://github.com/yourusername/meet-zone/releases)
2. Make the file executable (macOS/Linux only):
   ```bash
   chmod +x meet-zone-macos-1.0.2
   ```
3. Run the application:
   ```bash
   # Windows
   .\meet-zone-windows-1.0.2.exe
   
   # macOS
   ./meet-zone-macos-1.0.2
   
   # Linux
   ./meet-zone-linux-1.0.2
   ```

### First Launch

When you first launch Meet-Zone, you'll see a tabbed interface with three main sections:
- **Participants**: Manage team members and their availability
- **🆕 Busy Schedule**: Manage when participants are unavailable
- **Meeting Times**: Configure search parameters and view results

## Managing Participants

### Adding Participants

1. Go to the **Participants** tab
2. Fill in the participant details:
   - **Name**: The person's name or identifier
   - **Time Zone**: Select from the comprehensive timezone list
   - **Start Time**: When they typically start work (24-hour format, e.g., 09:00)
   - **End Time**: When they typically end work (24-hour format, e.g., 17:00)
3. Click **Add Participant**

### Importing from CSV

You can also load participants from a CSV file with busy schedules:

```bash
# Command line usage
./meet-zone-macos-1.0.2 roster.csv
```

**Enhanced CSV format with busy schedules:**
```csv
name,timezone,start_time,end_time,busy_schedule
Alice,America/New_York,09:00,17:00,10:00-11:00@Mon:Team standup;14:00-15:00:Daily review
Bob,Europe/London,08:30,16:30,09:00-10:00@2024-01-15:Doctor appointment;13:00-14:00@Fri:Team lunch
Charlie,Asia/Tokyo,10:00,18:00,11:00-12:00:Lunch break;16:00-17:00@Wed:Client call
```

### Managing Participants

- **Remove Selected**: Click on a participant in the table, then click "Remove Selected"
- **Clear All**: Remove all participants at once
- **View Busy Summary**: The participants table now shows a summary of each person's busy schedules

## 🆕 Managing Busy Schedules

### Adding Busy Times

1. Go to the **Busy Schedule** tab
2. Select a participant from the dropdown
3. Fill in the busy time details:
   - **Start Time**: When the busy period starts (e.g., 10:00)
   - **End Time**: When the busy period ends (e.g., 11:00)
   - **Date**: Optional - leave empty for daily recurring, or specify:
     - Specific date: `2024-01-15`
     - Day of week: `Mon`, `Tuesday`, etc.
   - **Recurring**: Choose "Weekly" for recurring busy times
   - **Description**: Optional description (e.g., "Team standup", "Lunch break")
4. Click **Add Busy Time**

### Busy Schedule Types

#### Daily Recurring
- **When to use**: Regular daily activities (lunch, daily standup)
- **Setup**: Leave date field empty
- **Example**: Lunch break from 12:00-13:00 every day

#### Weekly Recurring  
- **When to use**: Weekly meetings, regular appointments
- **Setup**: Enter day name (Mon, Tuesday, etc.) and set Recurring to "Weekly"
- **Example**: Team standup every Monday 10:00-11:00

#### Specific Date
- **When to use**: One-time appointments, vacations, holidays
- **Setup**: Enter specific date (YYYY-MM-DD) and set Recurring to "No"
- **Example**: Doctor appointment on 2024-01-15 from 14:00-15:00

### Busy Schedule Format in CSV

When using CSV files, the busy schedule field supports these formats:

```csv
# Daily recurring (applies every day)
Alice,America/New_York,09:00,17:00,12:00-13:00:Lunch

# Weekly recurring (every Monday)
Bob,Europe/London,08:30,16:30,10:00-11:00@Mon:Team standup

# Specific date
Charlie,Asia/Tokyo,10:00,18:00,14:00-15:00@2024-01-15:Doctor appointment

# Multiple busy times (separated by semicolons)
Diana,Australia/Sydney,08:00,16:00,12:00-13:00:Lunch;10:00-11:00@Mon:Standup;15:00-16:00@Fri:Review

# Day names supported
Eva,Europe/Berlin,09:30,17:30,09:00-10:00@Monday:All-hands;14:00-15:00@Wed:Client call
```

### Managing Busy Schedules

- **View All**: The busy schedule table shows all participants' busy times
- **Remove Selected**: Click on a busy schedule entry and click "Remove Selected"
- **Clear All Busy**: Remove all busy schedules for all participants

## Finding Meeting Times

### Basic Configuration

1. Go to the **Meeting Times** tab
2. Configure your search parameters:
   - **Min Duration**: Minimum meeting length in minutes (default: 30)
   - **Top Results**: How many options to show (default: 3)
   - **Show Full Week**: Search entire week vs. just today
   - **Prioritize By**: Focus on maximizing participants or meeting duration
   - **Start Date**: When to begin the search (default: today)

3. Click **Find Meeting Times**

### How Busy Schedules Affect Results

The algorithm now considers busy schedules when finding meeting times:

1. **Availability Check**: Ensures participants are within working hours
2. **Busy Schedule Filter**: Excludes participants who are busy during potential meeting times
3. **Optimal Matching**: Finds times when the maximum number of people are both available and not busy
4. **Smart Scoring**: Prefers times with fewer conflicts and better participation

### Advanced Options

#### Prioritization Strategies

- **Participants**: Prioritizes slots with more people available (considers busy schedules)
- **Duration**: Prioritizes longer available time slots (avoiding busy periods)

#### Time Range Options

- **Today Only**: Find slots for today only
- **Full Week**: Search across the next 7 days for more options (better for global teams)

## Understanding Results

### Result Columns

- **Start (UTC)**: Meeting start time in UTC
- **End (UTC)**: Meeting end time in UTC  
- **Duration**: How long the meeting slot is
- **Count**: Number of participants available (excludes those who are busy)
- **Score**: Quality score as a percentage (higher is better)
- **Names**: List of available participants (busy participants are automatically excluded)

### Interpreting Scores with Busy Schedules

The enhanced scoring system considers:
- **Participant availability**: More people available = higher score
- **Busy schedule conflicts**: Fewer conflicts = higher score
- **Meeting duration**: Longer slots = higher score (up to a point)
- **Time of day preference**: Business hours (9 AM - 5 PM UTC) = higher score
- **Day preference**: Earlier days in the week = slightly higher score

A score of 80%+ indicates an excellent meeting slot with minimal conflicts.

## Tips and Best Practices

### Setting Up Busy Schedules

1. **Start with regular patterns**: Add daily lunch breaks and weekly meetings first
2. **Be consistent**: Use the same time format and descriptions
3. **Plan ahead**: Add known conflicts like vacations or important appointments
4. **Use descriptions**: Help identify what the busy time is for
5. **Regular updates**: Keep busy schedules current for best results

### Getting Better Results

1. **Add comprehensive busy schedules**: More accurate data = better meeting times
2. **Use realistic working hours**: Don't extend hours beyond what's practical
3. **Consider time zones carefully**: Double-check timezone selections
4. **Try different prioritization**: Switch between "participants" and "duration" modes
5. **Use full week search**: Gives more flexibility, especially with busy schedules

### Working with Global Teams

1. **Account for local busy times**: Lunch breaks vary by culture and timezone
2. **Consider recurring meetings**: Set up weekly team meetings as busy times
3. **Plan for holidays**: Add country-specific holidays as busy dates
4. **Rotate meeting times**: Fair for all time zones over time
5. **Use specific dates for conflicts**: Vacations, conferences, etc.

### CSV File Tips

1. **Test busy schedule format**: Start with simple examples
2. **Use semicolons for multiple slots**: `10:00-11:00@Mon:Standup;14:00-15:00:Review`
3. **Be specific with dates**: Use YYYY-MM-DD format
4. **Consistent descriptions**: Help identify recurring patterns
5. **Validate before importing**: Check format with small test files

## Troubleshooting

### Common Issues

#### "No slots found" (with busy schedules)
- **Cause**: Too many busy schedule conflicts
- **Solutions**: 
  - Review busy schedules for accuracy
  - Try longer time range (full week)
  - Reduce minimum duration
  - Check if working hours overlap after busy times are excluded

#### Busy schedule not working
- **Check format**: Ensure proper time format (HH:MM-HH:MM)
- **Verify dates**: Use YYYY-MM-DD for specific dates
- **Day names**: Use Mon, Tue, Wed, Thu, Fri, Sat, Sun
- **Semicolon separation**: Multiple busy times need semicolons

#### Incorrect busy time exclusions
- **Time zone issues**: Busy times are in participant's local timezone
- **Date boundaries**: Check if busy times cross midnight
- **Recurring logic**: Weekly recurring uses day of week, not specific dates

#### CSV import with busy schedules fails
- **Check columns**: Must have exactly 5 columns including busy_schedule
- **Format validation**: Test busy schedule format separately
- **Encoding issues**: Save CSV as UTF-8
- **Empty busy schedules**: Use empty string, not spaces

### Performance with Busy Schedules

- **Complex schedules**: Many busy slots may slow calculations
- **Full week searches**: Take longer with busy schedule checking
- **Large teams**: 20+ participants with busy schedules need more processing time

### Getting Help

1. **Check debug logs**: `meet-zone-debug.log` contains detailed information
2. **Test busy schedule format**: Use the UI to validate before CSV import
3. **Run from command line**: Shows real-time error messages
4. **Open an issue**: Report bugs on GitHub with:
   - Your operating system
   - Sample CSV with busy schedules (anonymized)
   - Contents of debug log
   - Steps to reproduce the problem

## Command Line Usage

Meet-Zone supports command-line usage with busy schedule-enabled CSV files:

```bash
# Basic usage with CSV file (including busy schedules)
./meet-zone roster.csv

# Find longer meetings (useful when many people have busy schedules)
./meet-zone roster.csv --duration 60

# Search full week (better results with busy schedules)
./meet-zone roster.csv --week

# Prioritize by participants (good when busy schedules limit availability)
./meet-zone roster.csv --prioritize participants

# Combine options for complex scheduling
./meet-zone roster.csv --duration 45 --top 10 --week --prioritize participants
```

## Example Scenarios

### Scenario 1: Global Team with Regular Meetings
```csv
name,timezone,start_time,end_time,busy_schedule
Alice,America/New_York,09:00,17:00,10:00-11:00@Mon:All-hands;12:00-13:00:Lunch
Bob,Europe/London,08:30,16:30,09:00-10:00@Mon:All-hands;13:00-14:00:Lunch
Charlie,Asia/Tokyo,10:00,18:00,18:00-19:00@Mon:All-hands;12:00-13:00:Lunch
```

### Scenario 2: Team with Varied Schedules
```csv
name,timezone,start_time,end_time,busy_schedule
Dev1,America/Los_Angeles,10:00,18:00,14:00-15:00@Tue:Sprint planning;12:00-13:00:Lunch
Dev2,Europe/Berlin,09:00,17:00,10:00-11:00@Tue:Sprint planning;12:30-13:30:Lunch
PM,Australia/Sydney,08:00,16:00,22:00-23:00@Mon:Sprint planning;12:00-13:00:Lunch
```

---

For more information, see the [README.md](README.md) or visit the [GitHub repository](https://github.com/yourusername/meet-zone).