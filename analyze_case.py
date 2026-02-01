"""Quick analysis script for patient case."""
import sys
sys.path.insert(0, '/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_server')

from auto_icd_mcp.predictor import EnhancedICDPredictor, PatientDetails

# Patient data
patient = PatientDetails(
    age=30,  # Assuming adult age
    sex='M',  # Assuming male
    height_cm=175,
    weight_kg=100,
    symptoms=['lower back pain', 'fatigue'],
    primary_complaints=['lower back pain', 'fatigue']
)

# Initialize predictor
predictor = EnhancedICDPredictor()

# Get predictions
predictions = predictor.predict(patient, top_n=5)

# Display results
print("\n" + "="*80)
print("PATIENT ANALYSIS")
print("="*80)
print(f"\nPatient Profile:")
print(f"  Age: {patient.age} years")
print(f"  Sex: {patient.sex}")
print(f"  Height: {patient.height_cm} cm")
print(f"  Weight: {patient.weight_kg} kg")
print(f"  BMI: {patient.bmi} ({patient.bmi_category})")
print(f"\nSymptoms:")
for symptom in patient.symptoms:
    print(f"  - {symptom}")

print("\n" + "="*80)
print("TOP 5 ICD-10 PREDICTIONS")
print("="*80)

for i, pred in enumerate(predictions, 1):
    print(f"\n{i}. {pred.code}: {pred.description}")
    print(f"   Confidence: {pred.confidence_level} ({pred.probability_score:.1%})")
    print(f"   Matched Symptoms: {', '.join(pred.matched_symptoms) if pred.matched_symptoms else 'None'}")
    if pred.related_vitals:
        print(f"   Related Vitals: {', '.join([f'{k}: {v}' for k, v in pred.related_vitals.items()])}")
    print(f"   Explanation: {pred.matching_explanation}")

print("\n" + "="*80)
