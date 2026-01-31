from datetime import datetime, timedelta

class ManualPlanner:
    def __init__(self):
        pass

    def generate_plan(self, subjects_info, start_date_str, end_date_str):
        """
        Generates a schedule by distributing subjects evenly across the available days.
        subjects_info: List of dicts [{'name': 'Math', 'topics': 'Algebra, Calculus'}]
        """
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        total_days = (end_date - start_date).days
        
        if total_days <= 0:
            return []

        schedule = []
        num_subjects = len(subjects_info)
        
        current_date = start_date
        subject_index = 0
        
        # Simple Logic: Rotate through subjects day by day
        # Day 1: Subject 1
        # Day 2: Subject 2
        # ...
        
        for day_offset in range(total_days + 1):
            if num_subjects == 0:
                break
                
            current_date = start_date + timedelta(days=day_offset)
            subject = subjects_info[subject_index % num_subjects]
            
            # Simple task generation
            topics = subject.get('topics', '').split(',')
            topic_to_study = topics[day_offset % len(topics)].strip() if topics and topics[0] else f"General study for {subject['name']}"
            
            schedule.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "subject": subject['name'],
                "task": f"Study {topic_to_study}",
                "is_completed": False
            })
            
            subject_index += 1
            
        return schedule
