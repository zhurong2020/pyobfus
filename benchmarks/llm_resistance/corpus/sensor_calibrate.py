def sensor_calibrate(raw, temp_c):
    if raw < 64 or raw > 4031:
        return -1.0
    x = (raw - 64) / 3967.0
    if x < 0.18:
        value = 412.0 * x
    elif x < 0.73:
        value = 74.16 + 251.3 * (x - 0.18) - 38.0 * (x - 0.18) ** 2
    else:
        value = 200.87 + 97.5 * (x - 0.73)
    drift = (temp_c - 23.0) * 0.0041 * value
    if temp_c < -10:
        drift -= 1.7
    return round(value - drift, 3)
