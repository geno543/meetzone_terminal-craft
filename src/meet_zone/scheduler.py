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
    """Convert local time to UTC for a specific date"""
    local_dt = datetime.combine(date, local_time)
    local_dt = local_dt.replace(tzinfo=ZoneInfo(tz_name))
    return local_dt.astimezone(ZoneInfo("UTC"))

def is_participant_available(participant: Participant, utc_time: datetime) -> bool:
    """Check if participant is available at a specific UTC time"""
    # Convert UTC time to participant's local time
    local_dt = utc_time.astimezone(ZoneInfo(participant.tz))
    local_time = local_dt.time()
    local_date = local_dt.date()
    
    # Check if within working hours
    if participant.end_time < participant.start_time:
        # Working hours span midnight (e.g., 22:00 to 06:00)
        if not (local_time >= participant.start_time or local_time < participant.end_time):
            return False
    else:
        # Normal working hours (e.g., 09:00 to 17:00)
        if not (participant.start_time <= local_time < participant.end_time):
            return False
    
    # Check busy schedule if it exists
    if hasattr(participant, 'busy_slots') and participant.busy_slots:
        try:
            if participant.is_busy_at(local_time, local_date):
                return False
        except Exception:
            # If busy schedule check fails, assume available
            pass
    
    return True

def get_availability_grid(participants: List[Participant], date: datetime.date, interval_minutes: int = 15) -> Dict[datetime, Set[str]]:
    """Create availability grid for a specific date"""
    grid: Dict[datetime, Set[str]] = {}
    
    # Create 24-hour grid starting from midnight UTC
    day_start = datetime.combine(date, time(0, 0)).replace(tzinfo=ZoneInfo("UTC"))
    
    # Generate time slots for the entire day
    num_slots = (24 * 60) // interval_minutes
    
    print(f"Creating availability grid for {date} with {interval_minutes}-minute intervals")
    print(f"Checking {len(participants)} participants: {[p.name for p in participants]}")
    
    for i in range(num_slots):
        slot_time = day_start + timedelta(minutes=i * interval_minutes)
        available_participants = set()
        
        for participant in participants:
            if is_participant_available(participant, slot_time):
                available_participants.add(participant.name)
        
        # Only add slots where at least one participant is available
        if available_participants:
            grid[slot_time] = available_participants
    
    print(f"Found {len(grid)} time slots with available participants")
    
    # Show sample availability for debugging
    if grid:
        sorted_times = sorted(grid.keys())
        print(f"Sample availability (first 5 slots):")
        for slot_time in sorted_times[:5]:
            available = grid[slot_time]
            print(f"  {slot_time.strftime('%H:%M')} UTC: {', '.join(sorted(available))}")
    
    return grid

def find_continuous_slots(grid: Dict[datetime, Set[str]], min_duration_minutes: int, interval_minutes: int = 15) -> List[TimeSlot]:
    """Find continuous time slots where participants are available"""
    slots: List[TimeSlot] = []
    sorted_times = sorted(grid.keys())
    
    if not sorted_times:
        print("No available time slots in grid")
        return slots
    
    min_intervals = max(1, min_duration_minutes // interval_minutes)
    print(f"Looking for continuous slots of at least {min_intervals} intervals ({min_duration_minutes} minutes)")
    
    # Simple approach: find all continuous blocks
    i = 0
    while i < len(sorted_times):
        start_time = sorted_times[i]
        current_participants = grid[start_time].copy()
        
        if not current_participants:
            i += 1
            continue
        
        # Extend the slot as far as possible
        j = i
        while j < len(sorted_times):
            current_time = sorted_times[j]
            
            # Check if this time slot has overlapping participants
            slot_participants = grid[current_time]
            common_participants = current_participants & slot_participants
            
            if not common_participants:
                break
            
            # Check if times are continuous
            if j > i:
                expected_time = sorted_times[j-1] + timedelta(minutes=interval_minutes)
                if current_time != expected_time:
                    break
            
            current_participants = common_participants
            j += 1
        
        # Check if we have a valid slot
        duration_intervals = j - i
        if duration_intervals >= min_intervals and current_participants:
            end_time = sorted_times[j-1] + timedelta(minutes=interval_minutes)
            
            slot = TimeSlot(
                start_time=start_time,
                end_time=end_time,
                participant_count=len(current_participants),
                participant_names=current_participants.copy()
            )
            
            slots.append(slot)
            print(f"Found slot: {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')} "
                  f"with {len(current_participants)} participants: {', '.join(sorted(current_participants))}")
        
        i += 1
    
    print(f"Found {len(slots)} continuous slots")
    return slots

def find_best_slots(
    participants: List[Participant],
    min_duration: int,
    show_week: bool = False,
    top_k: int = 3,
    start_date: Optional[datetime.date] = None,
    prioritize_participants: bool = True
) -> List[TimeSlot]:
    """Find best meeting slots"""
    
    print(f"\n=== FINDING MEETING SLOTS ===")
    print(f"Participants: {len(participants)}")
    print(f"Min duration: {min_duration} minutes")
    print(f"Show week: {show_week}")
    print(f"Top results: {top_k}")
    print(f"Prioritize participants: {prioritize_participants}")
    
    if not participants:
        print("No participants provided")
        return []
    
    today = start_date or datetime.now().date()
    all_slots = []
    interval_minutes = 15
    
    # Determine dates to check
    dates_to_check = []
    if show_week:
        dates_to_check = [today + timedelta(days=i) for i in range(7)]
    else:
        dates_to_check = [today]
    
    print(f"Checking dates: {[d.strftime('%Y-%m-%d') for d in dates_to_check]}")
    
    # Process each date
    for i, date in enumerate(dates_to_check):
        print(f"\n--- Processing {date} ---")
        
        try:
            # Show participant working hours for this date
            print("Participant working hours (in their local timezone):")
            for participant in participants:
                print(f"  {participant.name} ({participant.tz}): {participant.start_time.strftime('%H:%M')}-{participant.end_time.strftime('%H:%M')}")
                
                # Show UTC equivalent
                start_utc = convert_to_utc(participant.start_time, participant.tz, date)
                end_utc = convert_to_utc(participant.end_time, participant.tz, date)
                print(f"    UTC equivalent: {start_utc.strftime('%H:%M')}-{end_utc.strftime('%H:%M')}")
            
            # Get availability grid
            grid = get_availability_grid(participants, date, interval_minutes)
            
            if not grid:
                print(f"No availability found for {date}")
                continue
            
            # Find continuous slots
            slots = find_continuous_slots(grid, min_duration, interval_minutes)
            
            # Add day offset for scoring
            for slot in slots:
                slot.day_offset = i
            
            all_slots.extend(slots)
            print(f"Added {len(slots)} slots for {date}")
            
        except Exception as e:
            print(f"Error processing {date}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n=== TOTAL SLOTS FOUND: {len(all_slots)} ===")
    
    if not all_slots:
        print("No meeting slots found. Trying fallback strategies...")
        
        # Fallback 1: Try with shorter duration
        print("Trying with 15-minute minimum duration...")
        for i, date in enumerate(dates_to_check):
            try:
                grid = get_availability_grid(participants, date, interval_minutes)
                if grid:
                    shorter_slots = find_continuous_slots(grid, 15, interval_minutes)
                    for slot in shorter_slots:
                        slot.day_offset = i
                    all_slots.extend(shorter_slots)
                    print(f"Fallback found {len(shorter_slots)} slots for {date}")
            except Exception as e:
                print(f"Fallback error for {date}: {e}")
        
        if not all_slots:
            print("Still no slots found. This suggests no overlapping availability.")
            return []
    
    # Calculate scores
    max_participants = len(participants)
    
    for slot in all_slots:
        # Participant score (0-1)
        participant_score = slot.participant_count / max_participants
        
        # Duration score (0-1, capped at 4 hours)
        duration_hours = (slot.end_time - slot.start_time).total_seconds() / 3600
        duration_score = min(duration_hours / 4.0, 1.0)
        
        # Day preference score (today is best)
        day_score = 1.0 - (getattr(slot, 'day_offset', 0) / 7.0)
        
        # Time of day score (prefer business hours)
        hour = slot.start_time.hour
        if 9 <= hour <= 17:
            time_score = 1.0
        elif 8 <= hour <= 18:
            time_score = 0.8
        else:
            time_score = 0.6
        
        # Calculate final score
        if prioritize_participants:
            slot.score = (participant_score * 0.5) + (duration_score * 0.2) + (day_score * 0.2) + (time_score * 0.1)
        else:
            slot.score = (duration_score * 0.5) + (participant_score * 0.2) + (day_score * 0.2) + (time_score * 0.1)
    
    # Sort by score (highest first)
    all_slots.sort(key=lambda x: x.score, reverse=True)
    
    # Remove duplicates and overlapping slots
    unique_slots = []
    for slot in all_slots:
        is_duplicate = False
        for unique_slot in unique_slots:
            # Check for significant overlap with same participants
            overlap_start = max(slot.start_time, unique_slot.start_time)
            overlap_end = min(slot.end_time, unique_slot.end_time)
            overlap_minutes = max(0, (overlap_end - overlap_start).total_seconds() / 60)
            
            if (overlap_minutes > 15 and slot.participant_names == unique_slot.participant_names):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_slots.append(slot)
            if 0 < top_k <= len(unique_slots):
                break
    
    print(f"\n=== FINAL RESULTS: {len(unique_slots)} unique slots ===")
    for i, slot in enumerate(unique_slots, 1):
        print(f"{i}. {slot.start_time.strftime('%Y-%m-%d %H:%M')}-{slot.end_time.strftime('%H:%M')} UTC")
        print(f"   Participants ({slot.participant_count}): {', '.join(sorted(slot.participant_names))}")
        print(f"   Score: {slot.score:.1%}")
    
    return unique_slots if top_k <= 0 else unique_slots[:top_k]

def get_participant_busy_summary(participant: Participant, date: datetime.date) -> List[str]:
    """Get a summary of participant's busy slots for a specific date"""
    if not hasattr(participant, 'busy_slots') or not participant.busy_slots:
        return []
    
    try:
        busy_slots = participant.get_busy_slots_for_date(date)
        summary = []
        
        for slot in busy_slots:
            time_str = f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
            if slot.description:
                summary.append(f"{time_str} ({slot.description})")
            else:
                summary.append(time_str)
        
        return summary
    except Exception:
        return []