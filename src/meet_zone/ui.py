import re
from dataclasses import dataclass
from datetime import datetime, time, date
from typing import Dict, List, Optional, Set, Tuple

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.widgets import (
    Button, DataTable, Footer, Header, Input, Label,
    Select, Static, TabPane, TabbedContent, TextArea
)
from textual.reactive import reactive
from textual.validation import Validator

from meet_zone.parser import Participant, BusySlot
from meet_zone.scheduler import TimeSlot, find_best_slots, get_participant_busy_summary


class TimeValidator(Validator):
    def validate(self, value: str) -> None:
        if not value:
            return self.success()

        try:
            if ':' in value:
                hours, minutes = map(int, value.split(':'))
            elif value.isdigit():
                hours, minutes = int(value), 0
            else:
                raise ValueError

            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError

            return self.success()
        except ValueError:
            return self.failure("Invalid time format. Use HH:MM (24-hour format)")


class DateValidator(Validator):
    def validate(self, value: str) -> None:
        if not value:
            return self.success()
        
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return self.success()
        except ValueError:
            return self.failure("Invalid date format. Use YYYY-MM-DD")


class MeetZoneApp(App):
    CSS = """
    #content {
        height: auto;
        max-height: 90vh;
        overflow: auto;
        margin: 1;
        padding-bottom: 2;
        background: $surface;
        border: tall $primary;
        width: 100%;
        padding: 1 2;
    }
    .section-title {
        background: $primary;
        color: $text;
        padding: 1;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    .subsection-title {
        background: $primary-darken-1;
        color: $text;
        padding: 0 1;
        margin-top: 1;
        margin-bottom: 1;
        text-style: bold;
    }
    #participants-table {
        height: 10;
        margin-bottom: 1;
        min-height: 5;
        border: solid $primary;
    }
    #busy-schedule-table {
        height: 8;
        margin-bottom: 1;
        min-height: 4;
        border: solid $accent;
    }
    #results-table {
        height: 10;
        margin-bottom: 1;
        min-height: 5;
        border: solid $primary;
    }
    #form-container {
        height: auto;
        max-height: 40vh;
        overflow: auto;
        border: panel $accent;
        padding: 1;
        margin-bottom: 1;
        display: block;
        background: $panel;
    }
    #busy-form-container {
        height: auto;
        max-height: 30vh;
        overflow: auto;
        border: panel $warning;
        padding: 1;
        margin-bottom: 1;
        display: block;
        background: $panel;
    }
    .form-row {
        height: 3;
        margin-bottom: 1;
        align: center middle;
        display: block;
    }
    #main-container {
        height: auto;
        width: 100%;
    }
    .half-width {
        width: 50%;
        height: auto;
    }
    #button-container {
        padding: 1;
        height: auto;
    }
    .form-label {
        width: 15;
        padding-right: 1;
        color: $text;
        text-align: right;
    }
    .form-input {
        width: 25;
        background: $surface-darken-1;
        color: $text;
    }
    .form-button {
        margin-right: 1;
        background: $accent;
        color: $text;
        min-width: 15;
    }
    .busy-button {
        margin-right: 1;
        background: $warning;
        color: $text;
        min-width: 12;
    }
    #settings-container {
        height: auto;
        max-height: 40vh;
        overflow: auto;
        border: panel $accent;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
    }
    #message-container {
        height: 3;
        padding: 0 1;
        margin-top: 1;
        border: solid $warning;
    }
    .error-message {
        color: $error;
        background: $surface-darken-1;
        border: solid $error !important;
        text-style: bold;
    }
    .success-message {
        color: $success;
        background: $surface-darken-1;
        border: solid $success !important;
        text-style: bold;
    }
    .info-message {
        color: $warning;
        background: $surface-darken-1;
        border: solid $warning !important;
    }
    Button {
        background: $accent;
        color: $text;
    }
    Button:hover {
        background: $accent-lighten-1;
    }
    TabbedContent {
        height: auto;
    }
    TabPane {
        height: auto;
        overflow: auto;
    }
    #main-tabs {
        height: 100%;
    }
    #busy-description {
        width: 40;
        height: 3;
    }
    """

    title = "Meet Zone - Meeting Time Finder"

    participants = reactive([])
    min_duration = reactive(30)
    display_full_week = reactive(False)
    top_results = reactive(3)
    status_message = reactive("")
    selected_participant_index = reactive(-1)

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="main-tabs"):
            with TabPane("Participants", id="tab-participants"):
                with Vertical(id="content"):
                    yield Static("Participant Management", classes="section-title")
                    with Horizontal(id="main-container"):
                        with Vertical(id="form-section", classes="half-width"):
                            yield Static("Add New Participant:", classes="subsection-title")
                            with Container(id="form-container"):
                                with Horizontal(classes="form-row"):
                                    yield Label("Name:", classes="form-label")
                                    yield Input(placeholder="Participant name", id="name-field", classes="form-input")
                                with Horizontal(classes="form-row"):
                                    yield Label("Time Zone:", classes="form-label")
                                    yield Select(
                                        [(tz, tz) for tz in self.get_timezones()],
                                        id="timezone-field",
                                        classes="form-input",
                                        value="UTC"
                                    )
                                with Horizontal(classes="form-row"):
                                    yield Label("Start Time:", classes="form-label")
                                    yield Input(placeholder="09:00", id="start-time-field", classes="form-input", validators=[TimeValidator()])
                                with Horizontal(classes="form-row"):
                                    yield Label("End Time:", classes="form-label")
                                    yield Input(placeholder="17:00", id="end-time-field", classes="form-input", validators=[TimeValidator()])
                        with Vertical(id="action-section", classes="half-width"):
                            yield Static("Actions:", classes="subsection-title")
                            with Container(id="button-container"):
                                yield Button("Add Participant", id="btn-add", classes="form-button")
                                yield Button("Remove Selected", id="btn-remove", classes="form-button")
                                yield Button("Clear All", id="btn-clear", classes="form-button")
                    yield Static("Current Participants:", classes="subsection-title")
                    yield DataTable(id="participants-table")
                    with Container(id="message-container"):
                        yield Static(id="message-text")
            
            with TabPane("Busy Schedule", id="tab-busy"):
                with Vertical(id="content"):
                    yield Static("Busy Schedule Management", classes="section-title")
                    yield Static("Add Busy Time for Selected Participant:", classes="subsection-title")
                    with Container(id="busy-form-container"):
                        with Horizontal(classes="form-row"):
                            yield Label("Participant:", classes="form-label")
                            yield Select([], id="busy-participant-select", classes="form-input")
                        with Horizontal(classes="form-row"):
                            yield Label("Start Time:", classes="form-label")
                            yield Input(placeholder="09:00", id="busy-start-field", classes="form-input", validators=[TimeValidator()])
                        with Horizontal(classes="form-row"):
                            yield Label("End Time:", classes="form-label")
                            yield Input(placeholder="10:00", id="busy-end-field", classes="form-input", validators=[TimeValidator()])
                        with Horizontal(classes="form-row"):
                            yield Label("Date (optional):", classes="form-label")
                            yield Input(placeholder="YYYY-MM-DD or leave empty for daily", id="busy-date-field", classes="form-input", validators=[DateValidator()])
                        with Horizontal(classes="form-row"):
                            yield Label("Recurring:", classes="form-label")
                            yield Select([("No", "False"), ("Weekly", "True")], id="busy-recurring-field", classes="form-input", value="False")
                        with Horizontal(classes="form-row"):
                            yield Label("Description:", classes="form-label")
                            yield Input(placeholder="Meeting, lunch, etc.", id="busy-description-field", classes="form-input")
                        with Horizontal(classes="form-row"):
                            yield Button("Add Busy Time", id="btn-add-busy", classes="busy-button")
                            yield Button("Remove Selected", id="btn-remove-busy", classes="busy-button")
                            yield Button("Clear All Busy", id="btn-clear-busy", classes="busy-button")
                    yield Static("Busy Schedule:", classes="subsection-title")
                    yield DataTable(id="busy-schedule-table")
                    with Container(id="message-container"):
                        yield Static(id="busy-message-text")
            
            with TabPane("Meeting Times", id="tab-results"):
                with Vertical(id="content"):
                    yield Static("Meeting Time Finder", classes="section-title")
                    yield Static("Meeting Settings:", classes="subsection-title")
                    with Container(id="settings-container"):
                        with Horizontal(classes="form-row"):
                            yield Label("Min Duration (min):", classes="form-label")
                            yield Input(value="30", id="duration-field", classes="form-input")
                        with Horizontal(classes="form-row"):
                            yield Label("Top Results:", classes="form-label")
                            yield Input(value="3", id="top-results-field", classes="form-input")
                        with Horizontal(classes="form-row"):
                            yield Label("Show Full Week:", classes="form-label")
                            yield Select([("Yes", "True"), ("No", "False")], id="week-toggle", classes="form-input", value="False")
                        with Horizontal(classes="form-row"):
                            yield Label("Prioritize By:", classes="form-label")
                            yield Select([("Participants", "participants"), ("Duration", "duration")], id="priority-field", classes="form-input", value="participants")
                        with Horizontal(classes="form-row"):
                            yield Label("Start Date:", classes="form-label")
                            yield Input(placeholder="YYYY-MM-DD", id="start-date-field", classes="form-input")
                        with Horizontal(classes="form-row"):
                            yield Button("Find Meeting Times", id="btn-find", classes="form-button")
                    yield Static("Meeting Time Results:", classes="subsection-title")
                    yield DataTable(id="results-table")
        yield Footer()

    def on_mount(self) -> None:
        participants_table = self.query_one("#participants-table", DataTable)
        participants_table.add_columns("Name", "Time Zone", "Start Time", "End Time", "Busy Slots")

        busy_table = self.query_one("#busy-schedule-table", DataTable)
        busy_table.add_columns("Participant", "Start Time", "End Time", "Date", "Recurring", "Description")

        results_table = self.query_one("#results-table", DataTable)
        results_table.add_columns(
            "Start (UTC)", "End (UTC)", "Duration", "Count", "Score", "Names"
        )

        date_input = self.query_one("#start-date-field", Input)
        date_input.value = datetime.now().strftime("%Y-%m-%d")

    def get_timezones(self) -> List[str]:
        import pytz
        return pytz.common_timezones

    def parse_time_string(self, value: str) -> Optional[time]:
        if not value:
            return None
        value = value.strip()
        try:
            if ":" in value:
                h, m = map(int, value.split(":"))
            else:
                h, m = int(value), 0
            if 0 <= h < 24 and 0 <= m < 60:
                return time(hour=h, minute=m)
        except (ValueError, TypeError):
            pass
        return None

    def parse_date_string(self, value: str) -> Optional[date]:
        if not value or not value.strip():
            return None
        try:
            return datetime.strptime(value.strip(), '%Y-%m-%d').date()
        except ValueError:
            return None

    def update_participant_select(self) -> None:
        """Update the participant selection dropdown in busy schedule tab"""
        select = self.query_one("#busy-participant-select", Select)
        options = [(p.name, str(i)) for i, p in enumerate(self.participants)]
        select.set_options(options)
        if options:
            select.value = "0"

    def update_busy_schedule_table(self) -> None:
        """Update the busy schedule table with all participants' busy slots"""
        table = self.query_one("#busy-schedule-table", DataTable)
        table.clear()
        
        for participant in self.participants:
            for busy_slot in participant.busy_slots:
                date_str = ""
                if busy_slot.date:
                    if busy_slot.recurring:
                        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        date_str = day_names[busy_slot.date.weekday()]
                    else:
                        date_str = busy_slot.date.strftime('%Y-%m-%d')
                
                table.add_row(
                    participant.name,
                    busy_slot.start_time.strftime('%H:%M'),
                    busy_slot.end_time.strftime('%H:%M'),
                    date_str,
                    "Yes" if busy_slot.recurring else "No",
                    busy_slot.description
                )

    def update_participants_table(self) -> None:
        """Update the participants table including busy schedule summary"""
        table = self.query_one("#participants-table", DataTable)
        table.clear()
        
        for participant in self.participants:
            # Create busy schedule summary
            busy_summary = []
            for busy_slot in participant.busy_slots:
                time_str = f"{busy_slot.start_time.strftime('%H:%M')}-{busy_slot.end_time.strftime('%H:%M')}"
                if busy_slot.date:
                    if busy_slot.recurring:
                        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        time_str += f"@{day_names[busy_slot.date.weekday()]}"
                    else:
                        time_str += f"@{busy_slot.date.strftime('%m-%d')}"
                busy_summary.append(time_str)
            
            busy_str = "; ".join(busy_summary) if busy_summary else "None"
            
            table.add_row(
                participant.name,
                participant.tz,
                participant.start_time.strftime('%H:%M'),
                participant.end_time.strftime('%H:%M'),
                busy_str
            )

    @on(Button.Pressed, "#btn-add, #btn-remove, #btn-clear, #btn-find, #btn-add-busy, #btn-remove-busy, #btn-clear-busy")
    def handle_button(self, event: Button.Pressed) -> None:
        action = event.button.id
        if action == "btn-add":
            self.add_participant()
        elif action == "btn-remove":
            self.remove_participant()
        elif action == "btn-clear":
            self.clear_participants()
        elif action == "btn-find":
            self.calculate_meeting_times()
        elif action == "btn-add-busy":
            self.add_busy_schedule()
        elif action == "btn-remove-busy":
            self.remove_busy_schedule()
        elif action == "btn-clear-busy":
            self.clear_busy_schedules()

    def add_participant(self) -> None:
        name_input = self.query_one("#name-field", Input)
        tz_input = self.query_one("#timezone-field", Select)
        start_input = self.query_one("#start-time-field", Input)
        end_input = self.query_one("#end-time-field", Input)

        name = name_input.value.strip()
        timezone = tz_input.value
        start_str = start_input.value.strip()
        end_str = end_input.value.strip()

        if not name:
            self.update_message("Error: Name is required")
            name_input.focus()
            return
        if not start_str:
            self.update_message("Error: Start time is required")
            start_input.focus()
            return
        if not end_str:
            self.update_message("Error: End time is required")
            end_input.focus()
            return

        start_time = self.parse_time_string(start_str)
        end_time = self.parse_time_string(end_str)

        if not start_time:
            self.update_message(f"Error: Invalid start time '{start_str}'")
            start_input.focus()
            return
        if not end_time:
            self.update_message(f"Error: Invalid end time '{end_str}'")
            end_input.focus()
            return
        if start_time >= end_time:
            self.update_message("Error: End time must follow start time")
            end_input.focus()
            return

        participant = Participant(name=name, tz=timezone, start_time=start_time, end_time=end_time)
        self.participants.append(participant)

        self.update_participants_table()
        self.update_participant_select()

        name_input.value = ""
        start_input.value = ""
        end_input.value = ""
        self.update_message(f"Success: Added '{name}'")
        name_input.focus()

    def remove_participant(self) -> None:
        table = self.query_one("#participants-table", DataTable)
        row_index = table.cursor_row
        if row_index is None or not (0 <= row_index < len(self.participants)):
            self.update_message("Error: Select a participant first")
            return

        coord = table.cursor_coordinate
        if coord:
            row_key, _ = table.coordinate_to_cell_key(coord)
            removed = self.participants.pop(row_index)
            self.update_participants_table()
            self.update_participant_select()
            self.update_busy_schedule_table()
            self.update_message(f"Success: Removed '{removed.name}'")
            if not self.participants:
                self.update_message("All participants removed.")
        else:
            self.update_message("Error: Could not determine selection")

    def clear_participants(self) -> None:
        if not self.participants:
            self.update_message("No participants to clear")
            return
        count = len(self.participants)
        self.participants = []
        self.update_participants_table()
        self.update_participant_select()
        self.update_busy_schedule_table()
        self.update_message(f"Success: Cleared {count} participants")
        self.query_one("#name-field", Input).focus()

    def add_busy_schedule(self) -> None:
        if not self.participants:
            self.update_message("Error: Add participants first", busy=True)
            return

        participant_select = self.query_one("#busy-participant-select", Select)
        start_input = self.query_one("#busy-start-field", Input)
        end_input = self.query_one("#busy-end-field", Input)
        date_input = self.query_one("#busy-date-field", Input)
        recurring_select = self.query_one("#busy-recurring-field", Select)
        description_input = self.query_one("#busy-description-field", Input)

        try:
            participant_index = int(participant_select.value)
            participant = self.participants[participant_index]
        except (ValueError, IndexError):
            self.update_message("Error: Select a valid participant", busy=True)
            return

        start_str = start_input.value.strip()
        end_str = end_input.value.strip()
        date_str = date_input.value.strip()
        recurring = recurring_select.value == "True"
        description = description_input.value.strip()

        if not start_str or not end_str:
            self.update_message("Error: Start and end times are required", busy=True)
            return

        start_time = self.parse_time_string(start_str)
        end_time = self.parse_time_string(end_str)

        if not start_time or not end_time:
            self.update_message("Error: Invalid time format", busy=True)
            return

        if start_time >= end_time:
            self.update_message("Error: End time must be after start time", busy=True)
            return

        busy_date = self.parse_date_string(date_str) if date_str else None

        # Add busy slot to participant
        participant.add_busy_slot(
            start_time=start_time,
            end_time=end_time,
            date=busy_date,
            description=description,
            recurring=recurring
        )

        # Update tables
        self.update_participants_table()
        self.update_busy_schedule_table()

        # Clear form
        start_input.value = ""
        end_input.value = ""
        date_input.value = ""
        description_input.value = ""

        self.update_message(f"Success: Added busy time for {participant.name}", busy=True)

    def remove_busy_schedule(self) -> None:
        table = self.query_one("#busy-schedule-table", DataTable)
        row_index = table.cursor_row
        
        if row_index is None:
            self.update_message("Error: Select a busy schedule entry first", busy=True)
            return

        # Find the corresponding busy slot
        current_row = 0
        for participant in self.participants:
            for i, busy_slot in enumerate(participant.busy_slots):
                if current_row == row_index:
                    # Remove this busy slot
                    participant.busy_slots.pop(i)
                    self.update_participants_table()
                    self.update_busy_schedule_table()
                    self.update_message(f"Success: Removed busy time for {participant.name}", busy=True)
                    return
                current_row += 1

        self.update_message("Error: Could not find busy schedule entry", busy=True)

    def clear_busy_schedules(self) -> None:
        count = 0
        for participant in self.participants:
            count += len(participant.busy_slots)
            participant.busy_slots.clear()

        if count == 0:
            self.update_message("No busy schedules to clear", busy=True)
            return

        self.update_participants_table()
        self.update_busy_schedule_table()
        self.update_message(f"Success: Cleared {count} busy schedule entries", busy=True)

    def calculate_meeting_times(self) -> None:
        if not self.participants:
            self.update_message("Error: Add participants first")
            self.query_one(TabbedContent).active = "tab-participants"
            return

        duration_input = self.query_one("#duration-field", Input)
        top_input = self.query_one("#top-results-field", Input)
        week_input = self.query_one("#week-toggle", Select)
        priority_input = self.query_one("#priority-field", Select)
        date_input = self.query_one("#start-date-field", Input)

        try:
            min_duration = int(duration_input.value)
            top_k = int(top_input.value)
            show_week = week_input.value == "True"
            prioritize_by_participants = priority_input.value == "participants"

            start_date = None
            if date_input.value.strip():
                start_date = datetime.strptime(date_input.value.strip(), "%Y-%m-%d").date()

            self.min_duration = min_duration
            self.top_results = top_k
            self.display_full_week = show_week
        except ValueError:
            self.update_message("Error: Duration and Top Results must be numbers")
            return

        self.update_message("Processing meeting slots (considering busy schedules)...")
        try:
            slots = find_best_slots(
                participants=self.participants,
                min_duration=self.min_duration,
                show_week=self.display_full_week,
                top_k=self.top_results,
                start_date=start_date,
                prioritize_participants=prioritize_by_participants
            )
        except Exception as e:
            self.update_message(f"Error: {e}")
            return

        results_table = self.query_one("#results-table", DataTable)
        results_table.clear()

        if not slots:
            self.update_message("No slots found. Check busy schedules and try adjusting parameters.")
            return

        for slot in slots:
            duration_minutes = slot.get_duration_minutes()
            names = ", ".join(sorted(slot.participant_names))
            score_pct = int(slot.score * 100)
            results_table.add_row(
                slot.start_time.strftime("%Y-%m-%d %H:%M"),
                slot.end_time.strftime("%Y-%m-%d %H:%M"),
                f"{duration_minutes} min",
                f"{slot.participant_count}/{len(self.participants)}",
                f"{score_pct}%",
                names
            )

        self.query_one(TabbedContent).active = "tab-results"
        self.update_message(f"Success: Found {len(slots)} options (busy schedules considered)")
        results_table.focus()

    def watch_status_message(self, message: str) -> None:
        message_widget = self.query_one("#message-text", Static)
        container = self.query_one("#message-container", Container)
        message_widget.update(message)
        container.remove_class("error-message")
        container.remove_class("success-message")
        container.remove_class("info-message")

        if message.startswith("Error:"):
            container.add_class("error-message")
        elif message.startswith("Success:"):
            container.add_class("success-message")
        else:
            container.add_class("info-message")

    def update_message(self, text: str, busy: bool = False) -> None:
        """Update status message, optionally for busy schedule tab"""
        if busy:
            # Update busy schedule message
            try:
                message_widget = self.query_one("#busy-message-text", Static)
                message_widget.update(text)
            except:
                # Fallback to main message
                self.status_message = text
        else:
            self.status_message = text


def display_results(
    slots: Optional[List[TimeSlot]] = None,
    participants: Optional[List[Participant]] = None,
    min_duration: int = 30,
    show_week: bool = False,
    prioritize_participants: bool = True,
    start_date: Optional[date] = None
) -> MeetZoneApp:
    app = MeetZoneApp()
    if participants:
        app.participants = participants
    app.min_duration = min_duration
    app.display_full_week = show_week

    if slots:
        def load_results():
            # Update participant table and select
            app.update_participants_table()
            app.update_participant_select()
            app.update_busy_schedule_table()
            
            priority = app.query_one("#priority-field", Select)
            priority.value = "participants" if prioritize_participants else "duration"
            if start_date:
                date_input = app.query_one("#start-date-field", Input)
                date_input.value = start_date.strftime("%Y-%m-%d")

            results = app.query_one("#results-table", DataTable)
            for slot in slots:
                duration_minutes = slot.get_duration_minutes()
                names = ", ".join(sorted(slot.participant_names))
                score_pct = int(slot.score * 100)
                results.add_row(
                    slot.start_time.strftime("%Y-%m-%d %H:%M"),
                    slot.end_time.strftime("%Y-%m-%d %H:%M"),
                    f"{duration_minutes} min",
                    f"{slot.participant_count}/{len(app.participants)}",
                    f"{score_pct}%",
                    names
                )
            app.query_one(TabbedContent).active = "tab-results"

        app.call_after_refresh(load_results)

    return app


if __name__ == "__main__":
    MeetZoneApp().run()