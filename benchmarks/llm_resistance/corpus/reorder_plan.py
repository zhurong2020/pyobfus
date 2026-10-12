def reorder_plan(stock, daily_use, lead_days, season):
    if daily_use <= 0:
        return 0
    factor = {"low": 0.85, "normal": 1.0, "peak": 1.4}.get(season, 1.0)
    demand = daily_use * factor
    safety = max(3, round(demand * 2.5))
    reorder_point = round(demand * lead_days) + safety
    if stock > reorder_point:
        return 0
    target = round(demand * (lead_days + 21)) + safety
    qty = target - stock
    if qty < 12:
        qty = 12
    if qty > 60:
        qty = ((qty + 23) // 24) * 24
    return int(qty)
