"""Example usage of the Auto ICD MCP Server."""

import asyncio
import json
from auto_icd_mcp.predictor import EnhancedICDPredictor, PatientDetails


async def example_1_diabetes_patient():
    """Example 1: Diabetes patient with hypertension."""
    print("=" * 80)
    print("Example 1: Diabetes Patient with Hypertension")
    print("=" * 80)
    
    predictor = EnhancedICDPredictor()
    
    patient = PatientDetails(
        age=58,
        sex='M',
        height_cm=175,
        weight_kg=95,
        systolic_bp=145,
        diastolic_bp=92,
        heart_rate=78,
        symptoms=['frequent urination', 'increased thirst', 'fatigue', 'blurred vision'],
        comorbidities=['hypertension', 'obesity'],
        doctor_specialty='ENDOCRINOLOGY'
    )
    
    print(f"\nPatient Profile:")
    print(f"  Age: {patient.age} years")
    print(f"  Sex: {patient.sex}")
    print(f"  BMI: {patient.bmi} ({patient.bmi_category})")
    print(f"  Blood Pressure: {patient.systolic_bp}/{patient.diastolic_bp} mmHg ({patient.bp_category})")
    print(f"  Symptoms: {', '.join(patient.symptoms)}")
    print(f"  Comorbidities: {', '.join(patient.comorbidities)}")
    
    predictions = predictor.predict(patient, top_n=5)
    
    print(f"\n{'Top 5 Predictions:'}")
    print("-" * 80)
    
    for i, pred in enumerate(predictions, 1):
        print(f"\n{i}. {pred.code} - {pred.description}")
        print(f"   Probability: {pred.probability_score:.3f} | Confidence: {pred.confidence_level}")
        print(f"   Matched Symptoms: {', '.join(pred.matched_symptoms) if pred.matched_symptoms else 'None'}")
        if pred.related_vitals:
            print(f"   Relevant Vitals: {', '.join(f'{k}={v}' for k, v in pred.related_vitals.items())}")
        print(f"   Explanation: {pred.matching_explanation[:150]}...")


async def example_2_pediatric_respiratory():
    """Example 2: Pediatric respiratory infection."""
    print("\n" + "=" * 80)
    print("Example 2: Pediatric Respiratory Infection")
    print("=" * 80)
    
    predictor = EnhancedICDPredictor()
    
    patient = PatientDetails(
        age=7,
        sex='F',
        height_cm=125,
        weight_kg=24,
        temperature_c=38.9,
        heart_rate=110,
        respiratory_rate=28,
        symptoms=['cough', 'fever', 'difficulty breathing', 'chest pain'],
        primary_complaints=['persistent cough for 3 days'],
        doctor_specialty='PEDIATRICS'
    )
    
    print(f"\nPatient Profile:")
    print(f"  Age: {patient.age} years")
    print(f"  Sex: {patient.sex}")
    print(f"  Temperature: {patient.temperature_c}°C")
    print(f"  Heart Rate: {patient.heart_rate} bpm")
    print(f"  Respiratory Rate: {patient.respiratory_rate} breaths/min")
    print(f"  Symptoms: {', '.join(patient.symptoms)}")
    print(f"  Primary Complaints: {', '.join(patient.primary_complaints)}")
    
    predictions = predictor.predict(patient, top_n=5)
    
    print(f"\n{'Top 5 Predictions:'}")
    print("-" * 80)
    
    for i, pred in enumerate(predictions, 1):
        print(f"\n{i}. {pred.code} - {pred.description}")
        print(f"   Probability: {pred.probability_score:.3f} | Confidence: {pred.confidence_level}")
        print(f"   Matched Symptoms: {', '.join(pred.matched_symptoms) if pred.matched_symptoms else 'None'}")
        if pred.related_vitals:
            print(f"   Relevant Vitals: {', '.join(f'{k}={v}' for k, v in pred.related_vitals.items())}")


async def example_3_cardiac_patient():
    """Example 3: Cardiac patient with chest pain."""
    print("\n" + "=" * 80)
    print("Example 3: Cardiac Patient with Chest Pain")
    print("=" * 80)
    
    predictor = EnhancedICDPredictor()
    
    patient = PatientDetails(
        age=65,
        sex='M',
        height_cm=178,
        weight_kg=88,
        systolic_bp=160,
        diastolic_bp=95,
        heart_rate=95,
        symptoms=['chest pain', 'shortness of breath', 'dizziness', 'fatigue'],
        primary_complaints=['severe chest pain radiating to left arm'],
        comorbidities=['hypertension', 'hyperlipidemia'],
        medical_history=['coronary artery disease', 'previous myocardial infarction'],
        doctor_specialty='CARDIOLOGY'
    )
    
    print(f"\nPatient Profile:")
    print(f"  Age: {patient.age} years")
    print(f"  Sex: {patient.sex}")
    print(f"  BMI: {patient.bmi} ({patient.bmi_category})")
    print(f"  Blood Pressure: {patient.systolic_bp}/{patient.diastolic_bp} mmHg ({patient.bp_category})")
    print(f"  Heart Rate: {patient.heart_rate} bpm")
    print(f"  Symptoms: {', '.join(patient.symptoms)}")
    print(f"  Medical History: {', '.join(patient.medical_history)}")
    
    predictions = predictor.predict(patient, top_n=5)
    
    print(f"\n{'Top 5 Predictions:'}")
    print("-" * 80)
    
    for i, pred in enumerate(predictions, 1):
        print(f"\n{i}. {pred.code} - {pred.description}")
        print(f"   Probability: {pred.probability_score:.3f} | Confidence: {pred.confidence_level}")
        print(f"   Matched Symptoms: {', '.join(pred.matched_symptoms) if pred.matched_symptoms else 'None'}")
        if pred.related_vitals:
            print(f"   Relevant Vitals:")
            for k, v in pred.related_vitals.items():
                print(f"     - {k}: {v}")


async def example_4_search_codes():
    """Example 4: Search for codes by description."""
    print("\n" + "=" * 80)
    print("Example 4: Search ICD Codes by Description")
    print("=" * 80)
    
    predictor = EnhancedICDPredictor()
    
    search_terms = ['diabetes', 'pneumonia', 'hypertension']
    
    for term in search_terms:
        print(f"\nSearching for: '{term}'")
        print("-" * 40)
        
        results = [
            entry for entry in predictor.icd_list 
            if term.lower() in entry['description']
        ][:5]
        
        for result in results:
            print(f"  {result['code']} - {result['description'].capitalize()}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("Auto ICD MCP Server - Usage Examples")
    print("=" * 80)
    
    await example_1_diabetes_patient()
    await example_2_pediatric_respiratory()
    await example_3_cardiac_patient()
    await example_4_search_codes()
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
