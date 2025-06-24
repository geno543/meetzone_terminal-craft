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
    if participant.busy_slots and participant.is_busy_at(local_time, local_date):
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
    
    # Initialize all time slots
    for slot_time in time_slots:
        grid[slot_time] = set()
    
    # Check each participant's availability for each time slot
    for participant in participants:
        for slot_time in time_slots:
            if is_participant_available(participant, slot_time, date):
                grid[slot_time].add(participant.name)
    
    # Return all slots (including empty ones for debugging)
    # But filter out completely empty slots for efficiency
    return {k: v for k, v in grid.items() if len(v) > 0}

def find_continuous_slots(grid: Dict[datetime, Set[str]], min_duration_minutes: int, interval_minutes: int = 15) -> List[TimeSlot]:
    """Find continuous time slots where participants are available"""
    slots: List[TimeSlot] = []
    sorted_times = sorted(grid.keys())
    
    if not sorted_times:
        return slots
    
    min_intervals = max(1, min_duration_minutes // interval_minutes)
    
    # Find all possible continuous slots
    for i in range(len(sorted_times)):
        start_time = sorted_times[i]
        current_participants = grid[start_time].copy()
        
        if not current_participants:
            continue
        
        # Extend the slot as long as possible
        j = i
        while j < len(sorted_times):
            current_time = sorted_times[j]
            
            # Check for time continuity (no gaps larger than interval)
            if j > i:
                time_gap = (current_time - sorted_times[j-1]).total_seconds() / 60
                if time_gap > interval_minutes * 1.5:  # Allow small gaps
                    break
            
            # Update participants (intersection - only those available throughout)
            slot_participants = grid[current_time]
            current_participants &= slot_participants
            
            if not current_participants:
                break
            
            # If we meet minimum duration, create a slot
            duration_intervals = j - i + 1
            if duration_intervals >= min_intervals:
                slot_end_time = current_time + timedelta(minutes=interval_minutes)
                
                # Create the time slot
                new_slot = TimeSlot(
                    start_time=start_time,
                    end_time=slot_end_time,
                    participant_count=len(current_participants),
                    participant_names=current_participants.copy()
                )
                slots.append(new_slot)
            
            j += 1
    
    # Remove duplicate/overlapping slots with same participants
    unique_slots = []
    for slot in slots:
        is_duplicate = False
        for existing in unique_slots:
            # Check if this is essentially the same slot (same participants, overlapping time)
            if (slot.participant_names == existing.participant_names and
                slot.start_time <= existing.end_time and
                slot.end_time >= existing.start_time):
                # Keep the longer one
                if slot.get_duration_minutes() > existing.get_duration_minutes():
                    unique_slots.remove(existing)
                    unique_slots.append(slot)
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_slots.append(slot)
    
    # Sort by duration (longest first)
    unique_slots.sort(key=lambda x: x.get_duration_minutes(), reverse=True)
    return unique_slots

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
    
    for i, date in enumerate(dates_to_check):
        try:
            grid = get_availability_grid(participants, date, interval_minutes)
            
            # Debug: print grid info
            if not grid:
                print(f"No availability found for {date}")
                continue
            
            slots = find_continuous_slots(grid, min_duration, interval_minutes)
            
            # Add day offset for scoring
            for slot in slots:
                slot.day_offset = i
            
            all_slots.extend(slots)
            
        except Exception as e:
            print(f"Error processing date {date}: {e}")
            continue
    
    if not all_slots:
        # Try with more lenient parameters
        print("No slots found with current parameters, trying with reduced requirements...")
        
        # Try with shorter minimum duration
        for i, date in enumerate(dates_to_check):
            try:
                grid = get_availability_grid(participants, date, interval_minutes)
                if grid:
                    # Try with half the minimum duration
                    shorter_slots = find_continuous_slots(grid, max(15, min_duration // 2), interval_minutes)
                    for slot in shorter_slots:
                        slot.day_offset = i
                    all_slots.extend(shorter_slots)
            except Exception as e:
                continue
    
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
            # More lenient overlap detection
            overlap_start = max(slot.start_time, unique_slot.start_time)
            overlap_end = min(slot.end_time, unique_slot.end_time)
            overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
            
            # If there's significant overlap and similar participants
            if (overlap_minutes > 15 and 
                len(slot.participant_names & unique_slot.participant_names) >= min(len(slot.participant_names), len(unique_slot.participant_names)) * 0.8):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_slots.append(slot)
            
            # Stop if we have enough results
            if 0 < top_k <= len(unique_slots):
                break
    
    return unique_slots if top_k <= 0 else unique_slots[:top_k]

def get_participant_busy_summary(participant: Participant, date: datetime.date) -> List[str]:
    """Get a summary of participant's busy slots for a specific date"""
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