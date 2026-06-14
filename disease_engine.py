"""
Disease Engine — Core simulation logic
Handles disease progression, vital signs, organ risks for
Malaria, Dengue Fever, and Chikungunya
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiseaseProfile:
    name: str
    incubation_days: int
    peak_day: int
    recovery_start: int
    base_severity: float
    affected_organs: List[str]
    primary_symptoms: List[str]


DISEASE_PROFILES = {
    "Malaria": DiseaseProfile(
        name="Malaria",
        incubation_days=2,
        peak_day=7,
        recovery_start=12,
        base_severity=0.75,
        affected_organs=["Liver", "Spleen", "Blood", "Brain", "Kidneys"],
        primary_symptoms=["Cyclic Fever", "Chills", "Hemolytic Anemia", "Splenomegaly"]
    ),
    "Dengue Fever": DiseaseProfile(
        name="Dengue Fever",
        incubation_days=1,
        peak_day=6,
        recovery_start=10,
        base_severity=0.80,
        affected_organs=["Blood", "Liver", "Skin", "Heart", "Kidneys"],
        primary_symptoms=["Hemorrhagic Fever", "Thrombocytopenia", "Rash", "Plasma Leakage"]
    ),
    "Chikungunya": DiseaseProfile(
        name="Chikungunya",
        incubation_days=2,
        peak_day=5,
        recovery_start=9,
        base_severity=0.65,
        affected_organs=["Joints", "Muscles", "Liver", "Eyes", "Skin"],
        primary_symptoms=["Polyarthralgia", "Myalgia", "Maculopapular Rash", "Arthritis"]
    ),
}

# Medication effects
MEDICATION_EFFECTS = {
    # Malaria meds

    "Chloroquine": {
        "fever_reduction": 1.2,
        "recovery_boost": 0.15,
        "parasite_clearance": 0.6,
        "organ_protection": 0.2,
        "side_effects": ["GI Upset", "Vision Changes"],
        "diseases": ["Malaria"]
    },
    "Primaquine": {
        "fever_reduction": 0.8,
        "recovery_boost": 0.20,
        "parasite_clearance": 0.7,
        "organ_protection": 0.15,
        "side_effects": ["Hemolysis", "Abdominal Pain"],
        "diseases": ["Malaria"]
    },
    # Dengue meds
    "Paracetamol": {
        "fever_reduction": 1.5,
        "recovery_boost": 0.10,
        "parasite_clearance": 0.0,
        "organ_protection": 0.1,
        "side_effects": ["Liver Stress (high dose)"],
        "diseases": ["Dengue Fever", "Chikungunya", "Malaria"]
    },
    "Oral Rehydration (ORT)": {
        "fever_reduction": 0.3,
        "recovery_boost": 0.15,
        "parasite_clearance": 0.0,
        "organ_protection": 0.25,
        "side_effects": [],
        "diseases": ["Dengue Fever", "Chikungunya"]
    },
    "IV Fluids": {
        "fever_reduction": 0.5,
        "recovery_boost": 0.20,
        "parasite_clearance": 0.0,
        "organ_protection": 0.40,
        "side_effects": ["Fluid Overload (risk)"],
        "diseases": ["Dengue Fever"]
    },
    "Platelet Transfusion": {
        "fever_reduction": 0.0,
        "recovery_boost": 0.10,
        "parasite_clearance": 0.0,
        "organ_protection": 0.5,
        "side_effects": ["Transfusion Reaction (rare)"],
        "diseases": ["Dengue Fever"]
    },
    # Chikungunya meds
    "Anti-inflammatory (NSAIDs)": {
        "fever_reduction": 1.0,
        "recovery_boost": 0.12,
        "parasite_clearance": 0.0,
        "organ_protection": 0.2,
        "side_effects": ["GI Irritation", "Renal Stress"],
        "diseases": ["Chikungunya"]
    },
    "Corticosteroids": {
        "fever_reduction": 0.8,
        "recovery_boost": 0.08,
        "parasite_clearance": 0.0,
        "organ_protection": 0.15,
        "side_effects": ["Immunosuppression", "Blood Sugar Rise"],
        "diseases": ["Chikungunya"]
    },
    "Physiotherapy": {
        "fever_reduction": 0.0,
        "recovery_boost": 0.18,
        "parasite_clearance": 0.0,
        "organ_protection": 0.3,
        "side_effects": [],
        "diseases": ["Chikungunya"]
    },
}


def smooth_curve(x, peak_x, peak_y, start_y=0.0, end_y=0.0, total=21):
    """Generate a smooth bell-like disease curve."""
    if x <= peak_x:
        t = x / peak_x if peak_x > 0 else 0
        return start_y + (peak_y - start_y) * (3*t**2 - 2*t**3)
    else:
        t = (x - peak_x) / (total - peak_x) if total > peak_x else 0
        return peak_y + (end_y - peak_y) * (3*t**2 - 2*t**3)


class DiseaseEngine:
    def __init__(self):
        self.current_disease = "Malaria"
        self.medications = []
        self.med_effect_multiplier = 1.0
        self.fever_reduction = 0.0
        self.recovery_boost = 0.0
        self.organ_protection = 0.0
        self.rng = np.random.RandomState(42)

    def set_disease(self, disease: str):
        self.current_disease = disease
        self.reset()

    def reset(self):
        self.medications = []
        self.med_effect_multiplier = 1.0
        self.fever_reduction = 0.0
        self.recovery_boost = 0.0
        self.organ_protection = 0.0
        self.rng = np.random.RandomState(42)

    def apply_medication(self, medication: str):
        if medication in MEDICATION_EFFECTS:
            eff = MEDICATION_EFFECTS[medication]
            self.fever_reduction += eff["fever_reduction"]
            self.recovery_boost += eff["recovery_boost"]
            self.organ_protection += eff["organ_protection"]
            self.medications.append(medication)

    def get_day_data(self, day: int, medications: List[str] = None) -> Dict:
        """Generate comprehensive vital signs and organ data for a given day."""
        profile = DISEASE_PROFILES.get(self.current_disease)
        if not profile:
            return self._empty_data()

        # Base disease progression curve (0-1)
        progression = self._get_progression(day, profile)
        recovery_factor = self._get_recovery_factor(day, profile)

        # Apply medication effects (fever reduction in Celsius)
        med_fever = self.fever_reduction
        med_recovery = self.recovery_boost
        med_organ = min(0.8, self.organ_protection)

        effective_progression = max(0, progression * (1 - med_recovery))
        noise = self.rng.normal(0, 0.02)

        data = {}

        if self.current_disease == "Malaria":
            data = self._malaria_vitals(day, effective_progression, recovery_factor, med_fever, noise)
        elif self.current_disease == "Dengue Fever":
            data = self._dengue_vitals(day, effective_progression, recovery_factor, med_fever, noise)
        elif self.current_disease == "Chikungunya":
            data = self._chikungunya_vitals(day, effective_progression, recovery_factor, med_fever, noise)

        # Compute organ risks
        data['organ_risks'] = self._compute_organ_risks(day, effective_progression, med_organ)
        data['severity'] = effective_progression * 100
        data['recovery_probability'] = max(0, min(100, recovery_factor * 100 + med_recovery * 30))
        data['progression'] = effective_progression
        data['day'] = day
        data['disease'] = self.current_disease
        data['medications'] = list(self.medications)
        data['hospitalization_risk'] = max(0, min(100, effective_progression * 85))

        return data

    def _get_progression(self, day, profile):
        """Disease progression curve peaking at worst day."""
        if day == 0:
            return 0.0
        peak = smooth_curve(day, profile.peak_day, 1.0, 0.1, 0.05)
        return max(0, min(1, peak))

    def _get_recovery_factor(self, day, profile):
        if day <= profile.recovery_start:
            return max(0, day / profile.recovery_start * 0.3)
        else:
            t = (day - profile.recovery_start) / (21 - profile.recovery_start)
            return 0.3 + 0.7 * (3*t**2 - 2*t**3)

    def _malaria_vitals(self, day, prog, rec, med_fever, noise):
        # Malaria: cyclic fever pattern, anemia, splenomegaly
        cyclic_fever = np.sin(day * np.pi / 1.5) * 0.3 * prog  # 48-72h cycle
        base_temp = 36.5 + prog * 4.5 - med_fever + cyclic_fever + noise
        temp = max(36.0, min(41.5, base_temp))

        hemoglobin = max(5.0, 15.5 - prog * 8.0 + rec * 4.0)  # Hemolytic anemia
        platelet = max(50, int(250 - prog * 100 + rec * 80))
        wbc = max(2000, int(7000 + prog * 5000 - rec * 3000))  # Leukocytosis
        rbc = max(2.5, 5.2 - prog * 2.0 + rec * 1.5)

        return {
            'temperature': round(temp, 1),
            'heart_rate': int(70 + prog * 45 + cyclic_fever * 5 - rec * 20),
            'systolic_bp': int(120 - prog * 20 + rec * 15),
            'diastolic_bp': int(80 - prog * 15 + rec * 10),
            'oxygen_saturation': round(max(85, 98 - prog * 8 + rec * 5), 1),
            'platelet_count': platelet,
            'hemoglobin': round(hemoglobin, 1),
            'wbc_count': wbc,
            'rbc_count': round(rbc, 2),
            'fatigue': min(100, int(prog * 90 - rec * 60)),
            'hydration': max(40, int(100 - prog * 45 + rec * 35)),
            'pain_level': min(100, int(prog * 70 - rec * 50)),
            'inflammation': min(100, int(prog * 85 - rec * 60)),
            'nausea': min(100, int(prog * 75 - rec * 55)),
            'headache': min(100, int(prog * 80 - rec * 60)),
            'weakness': min(100, int(prog * 85 - rec * 65)),
            'spleen_size': round(1.0 + prog * 3.5, 1),  # enlarged spleen (cm)
            'liver_enzymes': int(40 + prog * 120 - rec * 80),  # ALT
            'parasite_load': max(0, int(prog * 100000 - rec * 60000)),
            'cyclic_phase': "Fever" if cyclic_fever > 0.1 else ("Chills" if cyclic_fever < -0.1 else "Sweating"),
        }

    def _dengue_vitals(self, day, prog, rec, med_fever, noise):
        # Dengue: dramatic platelet crash, plasma leakage, rash
        # Phase 1: febrile (1-3), Phase 2: critical (4-6), Phase 3: recovery (7+)
        if day <= 3:
            phase = "Febrile"
            platelet_drop = 1.0 - day * 0.1
        elif day <= 6:
            phase = "Critical"
            platelet_drop = 0.7 - (day - 3) * 0.15
        else:
            phase = "Recovery"
            platelet_drop = max(0.2, 0.25 + (day - 6) * 0.08)

        platelet = max(10, int(250 * max(0.05, platelet_drop) * (1 - prog * 0.5) + rec * 100))
        hemorrhage_risk = max(0, (1 - platelet_drop) * prog * 100)

        temp = max(36.5, min(41.5, 36.5 + prog * 4.8 - med_fever + noise))

        return {
            'temperature': round(temp, 1),
            'heart_rate': int(75 + prog * 50 - rec * 25),
            'systolic_bp': int(120 - prog * 30 + rec * 20),
            'diastolic_bp': int(80 - prog * 20 + rec * 15),
            'oxygen_saturation': round(max(88, 98 - prog * 7 + rec * 4), 1),
            'platelet_count': platelet,
            'hemoglobin': round(max(8, 15.5 - prog * 3 + rec * 2), 1),
            'wbc_count': max(1500, int(7000 - prog * 4500 + rec * 3000)),  # Leukopenia
            'rbc_count': round(max(3.5, 5.2 - prog * 1.0 + rec * 0.5), 2),
            'fatigue': min(100, int(prog * 95 - rec * 65)),
            'hydration': max(35, int(100 - prog * 55 + rec * 40)),
            'pain_level': min(100, int(prog * 85 - rec * 60)),
            'inflammation': min(100, int(prog * 80 - rec * 55)),
            'nausea': min(100, int(prog * 80 - rec * 60)),
            'headache': min(100, int(prog * 90 - rec * 70)),
            'weakness': min(100, int(prog * 90 - rec * 70)),
            'rash_severity': min(100, int(prog * 80 * (1 if day >= 2 else 0) - rec * 60)),
            'bleeding_risk': min(100, int(hemorrhage_risk)),
            'plasma_leakage': min(100, int(prog * 70 * (1 if day >= 4 else 0) - rec * 50)),
            'dengue_phase': phase,
            'liver_enzymes': int(40 + prog * 150 - rec * 100),
        }

    def _chikungunya_vitals(self, day, prog, rec, med_fever, noise):
        # Chikungunya: intense joint pain, prolonged arthritis
        joint_pain = min(100, int(prog * 95 - rec * 30))  # joint pain persists longer
        if day > 10:
            joint_pain = max(30, joint_pain)  # chronic phase

        temp = max(36.5, min(40.5, 36.5 + prog * 4.0 - med_fever + noise))

        return {
            'temperature': round(temp, 1),
            'heart_rate': int(72 + prog * 35 - rec * 20),
            'systolic_bp': int(118 - prog * 15 + rec * 10),
            'diastolic_bp': int(78 - prog * 10 + rec * 8),
            'oxygen_saturation': round(max(92, 98 - prog * 5 + rec * 3), 1),
            'platelet_count': max(100, int(250 - prog * 80 + rec * 70)),
            'hemoglobin': round(max(10, 15.0 - prog * 2.5 + rec * 2), 1),
            'wbc_count': max(4000, int(7000 + prog * 6000 - rec * 4000)),
            'rbc_count': round(max(4.0, 5.2 - prog * 0.8 + rec * 0.5), 2),
            'fatigue': min(100, int(prog * 85 - rec * 55)),
            'hydration': max(55, int(100 - prog * 35 + rec * 28)),
            'pain_level': joint_pain,
            'inflammation': min(100, int(prog * 90 - rec * 40)),  # Persists
            'nausea': min(100, int(prog * 55 - rec * 45)),
            'headache': min(100, int(prog * 75 - rec * 60)),
            'weakness': min(100, int(prog * 80 - rec * 60)),
            'joint_swelling': min(100, int(prog * 95 - rec * 25)),
            'muscle_pain': min(100, int(prog * 90 - rec * 50)),
            'rash_severity': min(100, int(prog * 70 * (1 if day >= 2 else 0) - rec * 65)),
            'joint_stiffness': min(100, int(prog * 85 - rec * 20)),  # Very persistent
            'eye_pain': min(100, int(prog * 50 - rec * 45)),
            'liver_enzymes': int(40 + prog * 80 - rec * 60),
        }

    def _compute_organ_risks(self, day, progression, organ_protection) -> Dict:
        """Calculate risk level for each major organ."""
        p = progression
        op = organ_protection

        def risk_level(score):
            s = max(0, score - op * score * 0.5)
            if s < 25: return "Low", s
            if s < 55: return "Medium", s
            if s < 80: return "High", s
            return "Critical", s

        organs = {}
        if self.current_disease == "Malaria":
            organs = {
                "Liver": risk_level(p * 75),
                "Spleen": risk_level(p * 90),
                "Brain": risk_level(p * 60),
                "Heart": risk_level(p * 40),
                "Lungs": risk_level(p * 35),
                "Kidneys": risk_level(p * 55),
                "Blood System": risk_level(p * 95),
                "Muscles": risk_level(p * 30),
                "Joints": risk_level(p * 20),
            }
        elif self.current_disease == "Dengue Fever":
            # Critical platelet risk
            organs = {
                "Liver": risk_level(p * 80),
                "Spleen": risk_level(p * 50),
                "Brain": risk_level(p * 45),
                "Heart": risk_level(p * 55),
                "Lungs": risk_level(p * 50),
                "Kidneys": risk_level(p * 60),
                "Blood System": risk_level(p * 100),
                "Skin": risk_level(p * 70),
                "Joints": risk_level(p * 35),
            }
        elif self.current_disease == "Chikungunya":
            organs = {
                "Liver": risk_level(p * 45),
                "Spleen": risk_level(p * 30),
                "Brain": risk_level(p * 35),
                "Heart": risk_level(p * 30),
                "Lungs": risk_level(p * 25),
                "Kidneys": risk_level(p * 35),
                "Blood System": risk_level(p * 40),
                "Muscles": risk_level(p * 90),
                "Joints": risk_level(p * 98),
            }

        return organs

    def _empty_data(self):
        return {
            'temperature': 36.6, 'heart_rate': 72, 'systolic_bp': 120,
            'diastolic_bp': 80, 'oxygen_saturation': 98.5, 'platelet_count': 250,
            'hemoglobin': 15.0, 'wbc_count': 7000, 'fatigue': 0, 'hydration': 100,
            'pain_level': 0, 'inflammation': 0, 'nausea': 0, 'headache': 0,
            'weakness': 0, 'severity': 0, 'recovery_probability': 100,
            'organ_risks': {}, 'hospitalization_risk': 0, 'progression': 0,
            'medications': [], 'rbc_count': 5.2,
        }
