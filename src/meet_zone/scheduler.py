import datetime
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Set
from zoneinfo import ZoneInfo

from meet_zone.parser import Participant

@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime
    participant_count: int
    participant_names: Set[str]
    score: float = 0.0
    day_offset: int = 0

    def get_duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def overlaps_with(self, other: 'TimeSlot') -> bool:
        return self.start_time < other.end_time and self.end_time > other.start_time

def convert_to_utc(local_time: time, tz_name: str, date: datetime.date) -> datetime:
    local_dt = datetime.combine(date, local_time)
    local_dt = local_dt.replace(tzinfo=ZoneInfo(tz_name))
    return local_dt.astimezone(ZoneInfo("UTC"))

def is_participant_available(participant: Participant, utc_time: datetime, date: datetime.date) -> bool:
    """Check if participant is available at a specific UTC time, considering busy schedule"""
    
    # Convert UTC time to participant's local time
    local_dt = utc_time.astimezone(ZoneInfo(participant.tz))
    local_time = local_dt.time()
    local_date = local_dt.date()
    
    # Check if within working hours
    if participant.end_time < participant.start_time:
        # Working hours span midnight
        if not (local_time >= participant.start_time or local_time < participant.end_time):
            return False
    else:
        # Normal working hours
        if not (participant.start_time <= local_time < participant.end_time):
            return False
    
    # Check if busy at this time (only if participant has busy slots)
    if hasattr(participant, 'busy_slots') and participant.busy_slots:
        if participant.is_busy_at(local_time, local_date):
            return False
    
    return True

def get_availability_grid(participants: List[Participant], date: datetime.date, interval_minutes: int = 15) -> Dict[datetime, Set[str]]:
    """Create availability grid considering busy schedules"""
    grid: Dict[datetime, Set[str]] = {}
    
    # Create 24-hour grid starting from midnight UTC
    day_start = datetime.combine(date, time(0, 0)).replace(tzinfo=ZoneInfo("UTC"))
    
    # Generate time slots for the entire day
    num_slots = (24 * 60) // interval_minutes
    time_slots = [day_start + timedelta(minutes=i * interval_minutes) for i in range(num_slots)]
    
    # Check each participant's availability for each time slot
    for slot_time in time_slots:
        available_participants = set()
        
        for participant in participants:
            if is_participant_available(participant, slot_time, date):
                available_participants.add(participant.name)
        
        # Only add slots where at least one participant is available
        if available_participants:
            grid[slot_time] = available_participants
    
    print(f"Availability grid for {date}: {len(grid)} slots with available participants")
    return grid

def find_continuous_slots(grid: Dict[datetime, Set[str]], min_duration_minutes: int, interval_minutes: int = 15) -> List[TimeSlot]:
    """Find continuous time slots where participants are available"""
    slots: List[TimeSlot] = []
    sorted_times = sorted(grid.keys())
    
    if not sorted_times:
        print("No available time slots in grid")
        return slots
    
    min_intervals = max(1, min_duration_minutes // interval_minutes)
    print(f"Looking for slots of at least {min_intervals} intervals ({min_duration_minutes} minutes)")
    
    # Find all possible continuous slots
    for i in range(len(sorted_times)):
        start_time = sorted_times[i]
        
        # Try different durations starting from this time
        for j in range(i, len(sorted_times)):
            end_index = j
            
            # Check if times are continuous
            is_continuous = True
            for k in range(i, end_index):
                expected_next = sorted_times[k] + timedelta(minutes=interval_minutes)
                if k + 1 < len(sorted_times) and sorted_times[k + 1] != expected_next:
                    is_continuous = False
                    break
            
            if not is_continuous and end_index > i:
                break
            
            # Calculate duration
            duration_intervals = end_index - i + 1
            
            if duration_intervals >= min_intervals:
                # Find participants available for the entire duration
                available_participants = grid[sorted_times[i]].copy()
                
                for k in range(i + 1, end_index + 1):
                    available_participants &= grid[sorted_times[k]]
                
                if available_participants:
                    slot_end_time = sorted_times[end_index] + timedelta(minutes=interval_minutes)
                    
                    new_slot = TimeSlot(
                        start_time=start_time,
                        end_time=slot_end_time,
                        participant_count=len(available_participants),
                        participant_names=available_participants.copy()
                    )
                    
                    # Check for duplicates
                    is_duplicate = False
                    for existing_slot in slots:
                        if (existing_slot.start_time == new_slot.start_time and 
                            existing_slot.end_time == new_slot.end_time and
                            existing_slot.participant_names == new_slot.participant_names):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        slots.append(new_slot)
                        print(f"Found slot: {new_slot.start_time.strftime('%H:%M')}-{new_slot.end_time.strftime('%H:%M')} with {len(available_participants)} participants")
    
    # Sort by participant count (descending), then by duration (descending)
    slots.sort(key=lambda x: (x.participant_count, x.get_duration_minutes()), reverse=True)
    
    print(f"Found {len(slots)} total continuous slots")
    return slots

def find_best_slots(
    participants: List[Participant],
    min_duration: int,
    show_week: bool = False,
    top_k: int = 3,
    start_date: Optional[datetime.date] = None,
    prioritize_participants: bool = True
) -> List[TimeSlot]:
    """Find best meeting slots considering busy schedules"""
    if not participants:
        print("No participants provided")
        return []
    
    today = start_date or datetime.now().date()
    all_slots = []
    interval_minutes = 15
    
    # Generate slots for the specified date range
    dates_to_check = []
    if show_week:
        dates_to_check = [today + timedelta(days=i) for i in range(7)]
    else:
        dates_to_check = [today]
    
    print(f"Checking {len(dates_to_check)} dates: {[d.strftime('%Y-%m-%d') for d in dates_to_check]}")
    print(f"Participants: {[p.name for p in participants]}")
    
    for i, date in enumerate(dates_to_check):
        try:
            print(f"\nProcessing {date}...")
            
            # Debug: Show participant working hours in UTC for this date
            print("Participant availability (in UTC):")
            for participant in participants:
                start_utc = convert_to_utc(participant.start_time, participant.tz, date)
                end_utc = convert_to_utc(participant.end_time, participant.tz, date)
                busy_info = ""
                if hasattr(participant, 'busy_slots') and participant.busy_slots:
                    busy_count = len([bs for bs in participant.busy_slots 
                                    if bs.date is None or 
                                    (bs.recurring and bs.date.weekday() == date.weekday()) or
                                    (not bs.recurring and bs.date == date)])
                    busy_info = f" ({busy_count} busy slots)"
                print(f"  {participant.name}: {start_utc.strftime('%H:%M')}-{end_utc.strftime('%H:%M')} UTC{busy_info}")
            
            grid = get_availability_grid(participants, date, interval_minutes)
            
            if not grid:
                print(f"  No availability found for {date}")
                continue
            
            # Show sample availability
            sorted_times = sorted(grid.keys())
            print(f"  Available time range: {sorted_times[0].strftime('%H:%M')} to {sorted_times[-1].strftime('%H:%M')} UTC")
            
            # Show first few slots for debugging
            print("  Sample availability:")
            for slot_time in sorted_times[:5]:
                available = grid[slot_time]
                print(f"    {slot_time.strftime('%H:%M')}: {', '.join(sorted(available))}")
            
            slots = find_continuous_slots(grid, min_duration, interval_minutes)
            print(f"  Found {len(slots)} continuous slots for {date}")
            
            # Add day offset for scoring
            for slot in slots:
                slot.day_offset = i
            
            all_slots.extend(slots)
            
        except Exception as e:
            print(f"Error processing date {date}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\nTotal slots found across all dates: {len(all_slots)}")
    
    if not all_slots:
        print("No slots found with current parameters. Trying fallback strategies...")
        
        # Fallback 1: Try with shorter minimum duration
        print("Trying with 15-minute minimum duration...")
        for i, date in enumerate(dates_to_check):
            try:
                grid = get_availability_grid(participants, date, interval_minutes)
                if grid:
                    shorter_slots = find_continuous_slots(grid, 15, interval_minutes)
                    for slot in shorter_slots:
                        slot.day_offset = i
                    all_slots.extend(shorter_slots)
                    print(f"  Found {len(shorter_slots)} slots with 15-min duration for {date}")
            except Exception as e:
                print(f"  Error with fallback for {date}: {e}")
                continue
        
        # Fallback 2: Show any availability at all
        if not all_slots:
            print("Still no slots. Checking basic availability...")
            for date in dates_to_check:
                grid = get_availability_grid(participants, date, interval_minutes)
                if grid:
                    print(f"  {date}: {len(grid)} time slots have some availability")
                    # Show all available times
                    for time_slot in sorted(grid.keys()):
                        available = grid[time_slot]
                        print(f"    {time_slot.strftime('%H:%M')}: {', '.join(sorted(available))}")
                else:
                    print(f"  {date}: No availability at all")
    
    if not all_slots:
        print("No meeting slots could be found.")
        return []
    
    # Calculate scores for each slot
    max_participants = len(participants)
    
    for slot in all_slots:
        # Participant score (0-1)
        participant_score = slot.participant_count / max_participants
        
        # Duration score (0-1, capped at 4 hours)
        duration_hours = (slot.end_time - slot.start_time).total_seconds() / 3600
        duration_score = min(duration_hours / 4.0, 1.0)
        
        # Day preference score (today is best, decreases over time)
        day_score = 1.0 - (getattr(slot, 'day_offset', 0) / 7.0)
        
        # Time of day score (prefer business hours, 9 AM - 5 PM UTC gets highest score)
        hour = slot.start_time.hour
        if 9 <= hour <= 17:
            time_score = 1.0
        elif 8 <= hour <= 18:
            time_score = 0.8
        elif 7 <= hour <= 19:
            time_score = 0.6
        else:
            time_score = 0.4
        
        # Calculate final score based on prioritization
        if prioritize_participants:
            slot.score = (participant_score * 0.5) + (duration_score * 0.2) + (day_score * 0.2) + (time_score * 0.1)
        else:
            slot.score = (duration_score * 0.5) + (participant_score * 0.2) + (day_score * 0.2) + (time_score * 0.1)
    
    # Sort by score (highest first)
    all_slots.sort(key=lambda x: x.score, reverse=True)
    
    # Remove overlapping slots with same participants (keep the best one)
    unique_slots = []
    for slot in all_slots:
        # Check if this slot significantly overlaps with any existing unique slot
        is_duplicate = False
        for unique_slot in unique_slots:
            # Check for overlap and similar participants
            overlap_start = max(slot.start_time, unique_slot.start_time)
            overlap_end = min(slot.end_time, unique_slot.end_time)
            overlap_minutes = max(0, (overlap_end - overlap_start).total_seconds() / 60)
            
            # If there's significant overlap and very similar participants
            if (overlap_minutes > 15 and 
                slot.participant_names == unique_slot.participant_names):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_slots.append(slot)
            
            # Stop if we have enough results
            if 0 < top_k <= len(unique_slots):
                break
    
    print(f"Returning {len(unique_slots)} unique slots")
    for i, slot in enumerate(unique_slots):
        print(f"  {i+1}. {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')} UTC: {', '.join(sorted(slot.participant_names))} (score: {slot.score:.1%})")
    
    return unique_slots if top_k <= 0 else unique_slots[:top_k]

def get_participant_busy_summary(participant: Participant, date: datetime.date) -> List[str]:
    """Get a summary of participant's busy slots for a specific date"""
    if not hasattr(participant, 'busy_slots') or not participant.busy_slots:
        return []
    
    busy_slots = participant.get_busy_slots_for_date(date)
    summary = []
    
    for slot in busy_slots:
        time_str = f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
        if slot.description:
            summary.append(f"{time_str} ({slot.description})")
        else:
            summary.append(time_str)
    
    return summary

def analyze_availability_conflicts(participants: List[Participant], date: datetime.date) -> Dict[str, List[str]]:
    """Analyze and return availability conflicts for each participant"""
    conflicts = {}
    
    for participant in participants:
        participant_conflicts = []
        
        # Check for busy slots that conflict with working hours
        if hasattr(participant, 'busy_slots') and participant.busy_slots:
            busy_slots = participant.get_busy_slots_for_date(date)
            
            for busy_slot in busy_slots:
                # Check if busy slot overlaps with working hours
                if (busy_slot.start_time < participant.end_time and 
                    busy_slot.end_time > participant.start_time):
                    
                    conflict_desc = f"Busy {busy_slot.start_time.strftime('%H:%M')}-{busy_slot.end_time.strftime('%H:%M')}"
                    if busy_slot.description:
                        conflict_desc += f" ({busy_slot.description})"
                    
                    participant_conflicts.append(conflict_desc)
        
        if participant_conflicts:
            conflicts[participant.name] = participant_conflicts
    
    return conflicts

def debug_availability(participants: List[Participant], date: datetime.date) -> Dict:
    """Debug function to analyze why no meeting times are found"""
    debug_info = {
        'date': date.strftime('%Y-%m-%d'),
        'participants': [],
        'availability_summary': {}
    }
    
    for participant in participants:
        participant_info = {
            'name': participant.name,
            'timezone': participant.tz,
            'working_hours': f"{participant.start_time.strftime('%H:%M')}-{participant.end_time.strftime('%H:%M')}",
            'busy_slots': [],
            'available_hours': []
        }
        
        # Get busy slots for this date
        if hasattr(participant, 'busy_slots') and participant.busy_slots:
            busy_slots = participant.get_busy_slots_for_date(date)
            for busy_slot in busy_slots:
                participant_info['busy_slots'].append({
                    'time': f"{busy_slot.start_time.strftime('%H:%M')}-{busy_slot.end_time.strftime('%H:%M')}",
                    'description': busy_slot.description,
                    'recurring': busy_slot.recurring
                })
        
        # Check availability for each hour
        for hour in range(24):
            test_time = datetime.combine(date, time(hour, 0)).replace(tzinfo=ZoneInfo("UTC"))
            if is_participant_available(participant, test_time, date):
                participant_info['available_hours'].append(f"{hour:02d}:00")
        
        debug_info['participants'].append(participant_info)
    
    return debug_info