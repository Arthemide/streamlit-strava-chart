from datetime import datetime, timedelta

def find_default_publish_start_end_date():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    # end = start + timedelta(days=6)
    end = start + timedelta(days=6)
    if end > today:
        end = today
    return start, end