def slot_allocator(minute_of_day, priority, duration):
    if duration <= 0 or duration > 240:
        return -1
    start = minute_of_day
    if priority >= 8:
        start = max(start, 360)
    else:
        start = max(start, 480)
        if 720 <= start < 780:
            start = 780
    if start % 15:
        start += 15 - start % 15
    if priority < 3:
        start += 30
    end = start + duration
    limit = 1320 if priority >= 8 else 1080
    if end > limit:
        return -1
    return start
