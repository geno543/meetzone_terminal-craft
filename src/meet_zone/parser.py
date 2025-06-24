import csv
from dataclasses import dataclass, field
from datetime import time, datetime, date
from pathlib import Path
from typing import List, Set, Tuple, Optional


@dataclass
class BusySlot:
	"""Represents a busy time slot for a participant"""
	start_time: time
	end_time: time
	date: Optional[date] = None  # If None, applies to all days
	description: str = ""
	recurring: bool = False  # If True, repeats weekly


@dataclass
class Participant:
	name: str
	tz: str
	start_time: time
	end_time: time
	busy_slots: List[BusySlot] = field(default_factory=list)
	
	def add_busy_slot(self, start_time: time, end_time: time, 
					  date: Optional[date] = None, description: str = "", 
					  recurring: bool = False) -> None:
		"""Add a busy time slot for this participant"""
		busy_slot = BusySlot(
			start_time=start_time,
			end_time=end_time,
			date=date,
			description=description,
			recurring=recurring
		)
		self.busy_slots.append(busy_slot)
	
	def is_busy_at(self, check_time: time, check_date: date) -> bool:
		"""Check if participant is busy at a specific time and date"""
		for busy_slot in self.busy_slots:
			# Check if the busy slot applies to this date
			if busy_slot.date is not None:
				if busy_slot.recurring:
					# For recurring slots, check if it's the same day of week
					if check_date.weekday() != busy_slot.date.weekday():
						continue
				else:
					# For specific date slots, must match exactly
					if check_date != busy_slot.date:
						continue
			
			# Check if the time falls within the busy slot
			if busy_slot.start_time <= check_time < busy_slot.end_time:
				return True
		
		return False
	
	def get_busy_slots_for_date(self, check_date: date) -> List[BusySlot]:
		"""Get all busy slots that apply to a specific date"""
		applicable_slots = []
		
		for busy_slot in self.busy_slots:
			if busy_slot.date is None:
				# Applies to all days
				applicable_slots.append(busy_slot)
			elif busy_slot.recurring:
				# Recurring weekly - check day of week
				if check_date.weekday() == busy_slot.date.weekday():
					applicable_slots.append(busy_slot)
			else:
				# Specific date
				if check_date == busy_slot.date:
					applicable_slots.append(busy_slot)
		
		return applicable_slots


def parse_time(time_str: str) -> time:
	"""Parse time string in HH:MM format"""
	hours, minutes = map(int, time_str.split(':'))
	return time(hour=hours, minute=minutes)


def parse_date(date_str: str) -> Optional[date]:
	"""Parse date string in YYYY-MM-DD format"""
	if not date_str or date_str.strip() == "":
		return None
	try:
		return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
	except ValueError:
		raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def parse_roster(file_path: Path) -> List[Participant]:
	"""Parse roster file with optional busy schedule information"""
	if not file_path.exists():
		raise FileNotFoundError(f"Roster file not found: {file_path}")
	
	participants = []
	
	with open(file_path, 'r', newline='') as csvfile:
		reader = csv.reader(csvfile)
		header = next(reader, None)
		
		# Determine CSV format based on header
		if header and len(header) >= 4:
			has_busy_schedule = len(header) > 4
		else:
			has_busy_schedule = False
		
		for row_num, row in enumerate(reader, start=2):
			if len(row) < 4:
				print(f"Skipping row {row_num}: insufficient columns")
				continue
			
			name, tz, start_time_str, end_time_str = row[:4]
			
			try:
				start_time = parse_time(start_time_str)
				end_time = parse_time(end_time_str)
				
				participant = Participant(
					name=name,
					tz=tz,
					start_time=start_time,
					end_time=end_time
				)
				
				# Parse busy schedule if present
				if has_busy_schedule and len(row) > 4:
					busy_schedule_str = row[4] if len(row) > 4 else ""
					if busy_schedule_str.strip():
						parse_busy_schedule(participant, busy_schedule_str)
				
				participants.append(participant)
				
			except ValueError as e:
				print(f"Skipping row {row_num}: {e}")
	
	if not participants:
		raise ValueError("No valid participants found in roster file")
	
	return participants


def parse_busy_schedule(participant: Participant, busy_schedule_str: str) -> None:
	"""Parse busy schedule string and add to participant
	
	Format examples:
	- "09:00-10:00" (daily recurring)
	- "09:00-10:00@2023-12-25" (specific date)
	- "09:00-10:00@2023-12-25:Meeting" (with description)
	- "09:00-10:00@Mon:Weekly standup" (recurring weekly)
	- Multiple slots separated by semicolons: "09:00-10:00;14:00-15:00"
	"""
	if not busy_schedule_str.strip():
		return
	
	# Split multiple busy slots
	slots = [slot.strip() for slot in busy_schedule_str.split(';') if slot.strip()]
	
	for slot_str in slots:
		try:
			# Parse individual busy slot
			parts = slot_str.split('@', 1)
			time_part = parts[0].strip()
			
			# Parse time range
			if '-' not in time_part:
				print(f"Warning: Invalid time range format '{time_part}' for {participant.name}")
				continue
			
			start_str, end_str = time_part.split('-', 1)
			start_time = parse_time(start_str.strip())
			end_time = parse_time(end_str.strip())
			
			# Parse date/description part if present
			busy_date = None
			description = ""
			recurring = False
			
			if len(parts) > 1:
				date_desc_part = parts[1].strip()
				
				# Check if it contains description (separated by colon)
				if ':' in date_desc_part:
					date_part, description = date_desc_part.split(':', 1)
					date_part = date_part.strip()
					description = description.strip()
				else:
					date_part = date_desc_part
				
				# Parse date part
				if date_part:
					# Check for day names (recurring weekly)
					day_names = {
						'mon': 0, 'monday': 0,
						'tue': 1, 'tuesday': 1,
						'wed': 2, 'wednesday': 2,
						'thu': 3, 'thursday': 3,
						'fri': 4, 'friday': 4,
						'sat': 5, 'saturday': 5,
						'sun': 6, 'sunday': 6
					}
					
					if date_part.lower() in day_names:
						# Recurring weekly - create a reference date for the weekday
						weekday = day_names[date_part.lower()]
						# Use next occurrence of this weekday as reference
						today = datetime.now().date()
						days_ahead = weekday - today.weekday()
						if days_ahead <= 0:
							days_ahead += 7
						busy_date = today + datetime.timedelta(days=days_ahead)
						recurring = True
					else:
						# Specific date
						busy_date = parse_date(date_part)
			
			# Add the busy slot
			participant.add_busy_slot(
				start_time=start_time,
				end_time=end_time,
				date=busy_date,
				description=description,
				recurring=recurring
			)
			
		except Exception as e:
			print(f"Warning: Could not parse busy slot '{slot_str}' for {participant.name}: {e}")


def export_roster_with_busy_schedule(participants: List[Participant], file_path: Path) -> bool:
	"""Export participants with busy schedule to CSV file"""
	try:
		with open(file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(['name', 'timezone', 'start_time', 'end_time', 'busy_schedule'])
			
			for participant in participants:
				# Format busy schedule
				busy_schedule_parts = []
				for busy_slot in participant.busy_slots:
					time_part = f"{busy_slot.start_time.strftime('%H:%M')}-{busy_slot.end_time.strftime('%H:%M')}"
					
					if busy_slot.date:
						if busy_slot.recurring:
							# Use day name for recurring
							day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
							date_part = day_names[busy_slot.date.weekday()]
						else:
							# Use specific date
							date_part = busy_slot.date.strftime('%Y-%m-%d')
						
						if busy_slot.description:
							busy_part = f"{time_part}@{date_part}:{busy_slot.description}"
						else:
							busy_part = f"{time_part}@{date_part}"
					else:
						# No specific date (applies daily)
						if busy_slot.description:
							busy_part = f"{time_part}:{busy_slot.description}"
						else:
							busy_part = time_part
					
					busy_schedule_parts.append(busy_part)
				
				busy_schedule_str = ';'.join(busy_schedule_parts)
				
				writer.writerow([
					participant.name,
					participant.tz,
					participant.start_time.strftime('%H:%M'),
					participant.end_time.strftime('%H:%M'),
					busy_schedule_str
				])
		return True
	except Exception as e:
		print(f"Error exporting roster: {e}")
		return False