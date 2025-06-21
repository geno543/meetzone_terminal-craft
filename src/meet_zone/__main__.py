import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from meet_zone.parser import parse_roster, Participant
from meet_zone.scheduler import find_best_slots, TimeSlot
from meet_zone.ui import display_results, MeetZoneApp


def parse_args():
	parser = argparse.ArgumentParser(description="Find optimal meeting times across time zones")
	parser.add_argument("roster_file", type=Path, nargs='?', help="Path to CSV roster file (optional)")
	parser.add_argument("--duration", type=int, default=30, help="Minimum meeting duration in minutes")
	parser.add_argument("--top", type=int, default=3, help="Number of top slots to display")
	parser.add_argument("--week", action="store_true", help="Show full week instead of just today")
	parser.add_argument("--prioritize", choices=['participants', 'duration'], default='participants',
				   help="Whether to prioritize maximizing participants or meeting duration")
	parser.add_argument("--date", type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
				   help="Start date for search (format: YYYY-MM-DD, default: today)")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	
	try:
		participants: List[Participant] = []
		best_slots: Optional[List[TimeSlot]] = None
		

		prioritize_participants = args.prioritize == 'participants'
		
		
		if args.roster_file:
			participants = parse_roster(args.roster_file)
			best_slots = find_best_slots(
				participants=participants,
				min_duration=args.duration,
				show_week=args.week,
				top_k=args.top,
				start_date=args.date,
				prioritize_participants=prioritize_participants
			)
		

		app = display_results(
			slots=best_slots,
			participants=participants,
			min_duration=args.duration,
			show_week=args.week,
			prioritize_participants=prioritize_participants,
			start_date=args.date
		)
		app.run()
		return 0
	except Exception as e:
		print(f"Error: {e}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())