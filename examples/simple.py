"""
Simple example script for demonstrating pyobfus obfuscation.

This script calculates cardiovascular risk based on age and calcium score.
"""


def calculate_risk(age, calcium_score):
    """
    Calculate cardiovascular risk.

    Args:
        age: Patient age in years
        calcium_score: Agatston calcium score

    Returns:
        float: Risk score
    """
    risk_factor = 0.1

    if calcium_score > 100:
        risk_factor = 0.5
    elif calcium_score > 50:
        risk_factor = 0.3

    return age * risk_factor


def main():
    """Main function."""
    # Test data
    patient_age = 55
    patient_calcium = 150

    # Calculate risk
    risk = calculate_risk(patient_age, patient_calcium)

    # Display result
    print(f"Patient age: {patient_age}")
    print(f"Calcium score: {patient_calcium}")
    print(f"Risk score: {risk}")


if __name__ == "__main__":
    main()
