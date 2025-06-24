# Changelog

All notable changes to the Meet-Zone project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Busy Schedule Management**: Participants can now specify when they are unavailable
  - Add busy time slots with start/end times, optional dates, and descriptions
  - Support for recurring weekly busy slots (e.g., "every Monday")
  - Support for specific date busy slots (e.g., "December 25th")
  - Support for daily recurring busy slots (applies every day)
- **Enhanced CSV Format**: Extended CSV format to include busy schedule information
  - Format: `name,timezone,start_time,end_time,busy_schedule`
  - Busy schedule format: `HH:MM-HH:MM[@date/day][:description]`
  - Multiple busy slots separated by semicolons
- **Improved Algorithm**: Meeting time finder now considers busy schedules when calculating availability
  - Participants marked as busy are excluded from meeting slots during those times
  - More accurate availability calculations
  - Better conflict detection and resolution
- **New UI Tab**: Added dedicated "Busy Schedule" tab for managing participant availability
  - Add/remove/clear busy time slots
  - View all busy schedules in a comprehensive table
  - Select participants from dropdown for easy management
- **Enhanced Participant Display**: Participants table now shows busy schedule summary
- **Better Time Scoring**: Algorithm now considers time of day preferences (business hours get higher scores)

### Changed
- **Improved Scheduling Algorithm**: Now accounts for busy schedules in availability calculations
- **Enhanced UI Layout**: Added third tab for busy schedule management
- **Better Error Handling**: More descriptive error messages for busy schedule conflicts
- **Improved CSV Parsing**: Extended parser to handle busy schedule information

### Fixed
- **Availability Calculation**: Fixed edge cases in time zone conversion with busy schedules
- **UI Responsiveness**: Better handling of participant selection and table updates

## [v1.0.2] - 2025-01-27

### Added
- Comprehensive error handling and debug logging for executable troubleshooting
- Enhanced executable startup diagnostics with detailed error reporting
- Debug log file creation (`meet-zone-debug.log`) for troubleshooting
- Error dialog display using tkinter for better user feedback
- System information logging (Python version, platform, executable status)
- Critical import testing with detailed error messages

### Fixed
- Fixed PyInstaller build configuration to include all required Textual modules
- Added comprehensive hidden imports for textual.widgets.tab_pane and related modules
- Fixed "No module named 'textual.widgets.tab_pane'" error in executables
- Enhanced build process with --collect-all=textual flag for complete module inclusion
- Fixed Windows PowerShell compatibility issues with PyInstaller command line arguments
- Added missing tkinter and logging imports for error handling

### Changed
- Improved PyInstaller configuration with explicit Textual module imports
- Enhanced build reliability across all platforms (Windows, macOS, Linux)
- Consolidated Windows PyInstaller command to single line for PowerShell compatibility
- Enhanced main entry point with comprehensive exception handling
- Improved error reporting with both console output and GUI dialogs

## [v1.0.1] - 2025-01-27

### Added
- Enhanced terminal-based UI with improved tabbed interface
- Better error handling and validation for user inputs
- Improved time zone selection with comprehensive timezone list
- Enhanced meeting slot scoring algorithm with configurable prioritization
- Better visual feedback with color-coded status messages

### Changed
- Improved UI layout with better responsive design
- Enhanced participant management with clearer form validation
- Better meeting time calculation with more accurate availability detection
- Improved error messages and user feedback

### Fixed
- Fixed time parsing validation issues
- Improved participant removal functionality
- Better handling of edge cases in meeting slot calculation
- Fixed UI responsiveness issues

## [v1.0.0] - 2024-12-01

### Added
- Initial release of Meet-Zone
- Terminal-based UI using Textual framework
- CSV roster import functionality
- Time zone conversion and meeting time calculation
- Meeting slot scoring based on participant availability
- Support for prioritizing by participant count or meeting duration
- Weekly view for planning meetings across multiple days

### Changed

### Fixed

### Removed