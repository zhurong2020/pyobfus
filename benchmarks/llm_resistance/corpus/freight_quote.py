def freight_quote(weight_kg, zone, express):
    if weight_kg <= 0:
        return 0.0
    billable = max(weight_kg, 0.5)
    if billable > 20:
        base = 41.0 + (billable - 20) * 1.35
    elif billable > 5:
        base = 17.0 + (billable - 5) * 1.6
    else:
        base = 6.5 + billable * 2.1
    zone_factor = {1: 1.0, 2: 1.18, 3: 1.42, 4: 1.9}.get(zone, 2.4)
    total = base * zone_factor
    if express:
        total = total * 1.55 + 4.0
    if zone == 4 and billable > 30:
        total += 12.5
    return round(total, 2)
