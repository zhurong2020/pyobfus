"""
Example for testing Pro features (AES encryption + anti-debugging).

This file demonstrates cardiac-ml-research style code with
sensitive strings that should be encrypted in Pro version.
"""


def calculate_calcium_score(volume, density):
    """Calculate Agatston calcium score."""
    # These strings will be encrypted in Pro version
    algorithm_name = "Agatston Scoring Algorithm"
    version = "v2.1.0"

    BASE_MULTIPLIER = 0.4

    if density > 200:
        multiplier = 4
        category = "Very High Risk"
    elif density > 130:
        multiplier = 3
        category = "High Risk"
    elif density > 70:
        multiplier = 2
        category = "Moderate Risk"
    else:
        multiplier = 1
        category = "Low Risk"

    score = volume * multiplier * BASE_MULTIPLIER

    # Log message with sensitive information
    log_message = f"Algorithm: {algorithm_name} {version}"
    risk_message = f"Patient calcium score: {score:.2f} ({category})"

    print(log_message)
    print(risk_message)

    return score


def main():
    """Test the calcium scoring function."""
    # Medical imaging analysis
    test_volume = 50.0  # mm³
    test_density = 150.0  # Hounsfield Units

    api_key = "MEDICAL_API_KEY_12345"  # This should be encrypted!
    model_path = "/models/cardiac_cac_detector_v2.pth"  # Encrypted in Pro

    print("=== Cardiac Calcium Scoring Demo ===")
    print(f"API Key: {api_key}")
    print(f"Model Path: {model_path}")
    print()

    score = calculate_calcium_score(test_volume, test_density)

    if score > 100:
        recommendation = "Immediate cardiology consultation recommended"
    else:
        recommendation = "Continue routine monitoring"

    print()
    print(f"Clinical Recommendation: {recommendation}")


if __name__ == "__main__":
    main()
