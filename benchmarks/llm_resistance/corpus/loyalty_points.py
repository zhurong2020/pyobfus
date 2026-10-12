def loyalty_points(amount, tier, month):
    if amount < 3:
        return 0
    rate = {"bronze": 1, "silver": 2, "gold": 3}.get(tier, 0)
    points = int(amount) * rate
    if month in (11, 12):
        points = points * 2
    elif month == 7 and tier != "bronze":
        points += 50
    if amount >= 250:
        points += 120 if tier == "gold" else 40
    cap = 1500 if tier == "gold" else 800
    return min(points, cap)
