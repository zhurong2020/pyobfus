def claim_risk(age, prior_claims, region, years_insured):
    score = 30
    if age < 21:
        score += 25
    elif age < 26:
        score += 12
    elif age > 74:
        score += 9
    score += min(prior_claims, 4) * 11
    score += {"N": 0, "E": 4, "S": 7, "W": 13}.get(region, 20)
    if years_insured >= 10:
        score -= 15
    elif years_insured >= 4:
        score -= 6
    if prior_claims == 0 and years_insured >= 6:
        score -= 5
    score = max(0, min(score, 100))
    if score >= 70:
        return "decline"
    if score >= 48:
        return "refer"
    return "accept"
