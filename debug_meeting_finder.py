#!/usr/bin/env python3
"""
Debug script to test meeting time finding functionality
"""

import sys
from datetime import datetime, date
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from meet_zone.parser import parse_roster, Participant
from meet_zone.scheduler import find_best_slots, debug_availability, get_availability_grid

def test_meeting_finder():
    """Test the meeting finder with current roster"""
    print("Testing Meeting Time Finder")
    print("=" * 40)
    
    try:
        # Load participants from roster
        roster_file = Path("roster.csv")
        if not roster_file.exists():
            print("Error: roster.csv not found")
            return
        
        participants = parse_roster(roster_file)
        print(f"Loaded {len(participants)} participants:")
        
        for p in participants:
            print(f"  - {p.name} ({p.tz}): {p.start_time}-{p.end_time}")
            if p.busy_slots:
                print(f"    Busy slots: {len(p.busy_slots)}")
                for busy in p.busy_slots:
                    date_info = ""
                    if busy.date:
                        if busy.recurring:
                            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                            date_info = f" @{days[busy.date.weekday()]}"
                        else:
                            date_info = f" @{busy.date}"
                    desc = f" ({busy.description})" if busy.description else ""
                    print(f"      {busy.start_time}-{busy.end_time}{date_info}{desc}")
        
        print("\n" + "=" * 40)
        
        # Test availability for today
        today = datetime.now().date()
        print(f"Testing availability for {today}")
        
        # Get debug info
        debug_info = debug_availability(participants, today)
        print("\nDebug Information:")
        for p_info in debug_info['participants']:
            print(f"\n{p_info['name']} ({p_info['timezone']}):")
            print(f"  Working hours: {p_info['working_hours']}")
            print(f"  Busy slots: {len(p_info['busy_slots'])}")
            for busy in p_info['busy_slots']:
                print(f"    - {busy['time']} {busy['description']}")
            print(f"  Available hours: {', '.join(p_info['available_hours'][:10])}...")
        
        # Test availability grid
        print(f"\nTesting availability grid...")
        grid = get_availability_grid(participants, today)
        print(f"Found {len(grid)} time slots with available participants")
        
        if grid:
            # Show first few slots
            sorted_times = sorted(grid.keys())
            print("Sample availability slots:")
            for i, slot_time in enumerate(sorted_times[:10]):
                available = grid[slot_time]
                print(f"  {slot_time.strftime('%H:%M')} UTC: {', '.join(available)}")
        
        # Test meeting slot finding
        print(f"\nFinding meeting slots...")
        slots = find_best_slots(
            participants=participants,
            min_duration=30,
            show_week=False,
            top_k=5,
            start_date=today,
            prioritize_participants=True
        )
        
        print(f"Found {len(slots)} meeting slots:")
        for i, slot in enumerate(slots, 1):
            print(f"  {i}. {slot.start_time.strftime('%Y-%m-%d %H:%M')} - {slot.end_time.strftime('%H:%M')} UTC")
            print(f"     Duration: {slot.get_duration_minutes()} min")
            print(f"     Participants: {', '.join(sorted(slot.participant_names))}")
            print(f"     Score: {slot.score:.1%}")
        
        if not slots:
            print("\n⚠️  No meeting slots found!")
            print("Possible reasons:")
            print("1. Busy schedules conflict with all available times")
            print("2. No overlapping working hours")
            print("3. Minimum duration too long")
            
            # Test with longer duration range
            print("\nTrying with full week...")
            week_slots = find_best_slots(
                participants=participants,
                min_duration=30,
                show_week=True,
                top_k=5,
                start_date=today,
                prioritize_participants=True
            )
            print(f"Week search found {len(week_slots)} slots")
            
            # Test with shorter duration
            print("\nTrying with 15-minute minimum...")
            short_slots = find_best_slots(
                participants=participants,
                min_duration=15,
                show_week=False,
                top_k=5,
                start_date=today,
                prioritize_participants=True
            )
            print(f"Short duration search found {len(short_slots)} slots")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_without_busy_schedules():
    """Test with participants without busy schedules"""
    print("\n" + "=" * 40)
    print("Testing WITHOUT busy schedules")
    print("=" * 40)
    
    from meet_zone.parser import Participant
    from datetime import time
    
    # Create simple participants without busy schedules
    participants = [
        Participant("Alice", "America/New_York", time(9, 0), time(17, 0)),
        Participant("Bob", "Europe/London", time(8, 30), time(16, 30)),
        Participant("Charlie", "Asia/Tokyo", time(10, 0), time(18, 0)),
    ]
    
    print(f"Created {len(participants)} simple participants")
    
    today = datetime.now().date()
    slots = find_best_slots(
        participants=participants,
        min_duration=30,
        show_week=False,
        top_k=5,
        start_date=today,
        prioritize_participants=True
    )
    
    print(f"Found {len(slots)} meeting slots without busy schedules:")
    for i, slot in enumerate(slots, 1):
        print(f"  {i}. {slot.start_time.strftime('%Y-%m-%d %H:%M')} - {slot.end_time.strftime('%H:%M')} UTC")
        print(f"     Participants: {', '.join(sorted(slot.participant_names))}")

if __name__ == "__main__":
    test_meeting_finder()
    test_without_busy_schedules()