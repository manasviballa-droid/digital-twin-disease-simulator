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
        "recovery_boost": 0.0,
        "parasite_clearance": 0.6,
        "organ_protection": 0.0,
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
        "fever_reduction": 0.0,
        "recovery_boost": 0.0,
        "parasite_clearance": 0.0,
        "organ_protection": 0.0,
        "side_effects": [],
        "diseases": ["Dengue Fever", "Chikungunya"]
    },
    "IV Fluids": {
        "fever_reduction": 0.0,
        "recovery_boost": 0.20,
        "parasite_clearance": 0.0,
        "organ_protection": 0.40,
        "side_effects": ["Fluid Overload (risk)"],
        "diseases": ["Dengue Fever"]
    },
    "Platelet Transfusion": {
        "fever_reduction": 0.0,
        "recovery_boost": 0.0,
        "parasite_clearance": 0.0,
        "organ_protection": 0.0,
        "side_effects": ["Transfusion Reaction (rare)"],
        "diseases": ["Dengue Fever"]
    },
    # Chikungunya meds
    "Anti-inflammatory (NSAIDs)": {
        "fever_reduction": 1.0,
        "recovery_boost": 0.0,
        "parasite_clearance": 0.0,
        "organ_protection": 0.0,
        "side_effects": ["GI Irritation", "Renal Stress"],
        "diseases": ["Chikungunya"]
    },
    "Corticosteroids": {
        "fever_reduction": 0.8,
        "recovery_boost": 0.08,
        "parasite_clearance": 0.0,
        "organ_protection": 0.0,
        "side_effects": ["Immunosuppression", "Blood Sugar Rise"],
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
        self.medications = {}  # med_name -> day_administered
        self.med_effect_multiplier = 1.0
        self.rng = np.random.RandomState(42)
        self.is_csv_mode = False
        self.csv_data = None
        self.csv_file_path = ""

    def set_disease(self, disease: str):
        self.current_disease = disease
        self.reset()

    def reset(self):
        self.medications = {}
        self.med_effect_multiplier = 1.0
        self.rng = np.random.RandomState(42)

    def apply_medication(self, medication: str, day: int = 0):
        self.medications[medication] = day

    def load_patient_csv(self, file_path: str):
        """Load clinical patient dataset from CSV file."""
        try:
            df = pd.read_csv(file_path)
            if 'day' in df.columns and 'hour' in df.columns:
                df = df.set_index(['day', 'hour'], drop=False)
                self.csv_data = df
                self.csv_file_path = file_path
                self.is_csv_mode = True
                num_days = int(df['day'].max()) + 1
                return True, f"Loaded {len(df)} hourly records ({num_days} days) of patient records."
            else:
                if 'day' not in df.columns:
                    df['day'] = range(len(df))
                df = df.set_index('day', drop=False)
                self.csv_data = df
                self.csv_file_path = file_path
                self.is_csv_mode = True
                return True, f"Loaded {len(df)} days of patient records."
        except Exception as e:
            return False, f"Failed to load CSV: {str(e)}"

    @property
    def max_days(self) -> int:
        if self.is_csv_mode and self.csv_data is not None:
            if isinstance(self.csv_data.index, pd.MultiIndex):
                return int(self.csv_data['day'].max())
            else:
                return len(self.csv_data) - 1
        return 21

    def _parse_csv_row(self, row, day: int, medications: List[str] = None) -> Dict:
        medications = medications if medications is not None else []
        
        # Calculate active medication effects
        med_fever = 0.0
        med_recovery = 0.0
        med_organ = 0.0

        for med in medications:
            if med in MEDICATION_EFFECTS:
                eff = MEDICATION_EFFECTS[med]
                med_fever += eff.get("fever_reduction", 0.0)
                med_recovery += eff.get("recovery_boost", 0.0)
                med_organ += eff.get("organ_protection", 0.0)

        med_organ = min(0.8, med_organ)

        # Parse temperature (Fahrenheit vs Celsius)
        raw_temp = float(row.get('temperature', 36.6))
        if raw_temp > 50:
            temp_c = (raw_temp - 32.0) / 1.8
        else:
            temp_c = raw_temp

        # Apply antipyretic (fever reduction)
        temp_c = max(36.0, temp_c - med_fever)

        # Parse platelets and apply transfusion if active
        platelet = int(row.get('platelet_count', 250))
        if "Platelet Transfusion" in medications:
            platelet = max(platelet, 120)

        # Bleeding risk and plasma leakage reduction from fluids
        bleeding_risk = int(row.get('bleeding_risk', 0))
        plasma_leakage = int(row.get('plasma_leakage', 0))
        if "IV Fluids" in medications:
            bleeding_risk = max(0, bleeding_risk - 40)
            plasma_leakage = max(0, plasma_leakage - 50)
        if "Oral Rehydration (ORT)" in medications:
            bleeding_risk = max(0, bleeding_risk - 20)
            plasma_leakage = max(0, plasma_leakage - 25)

        # Build vitals dict
        vitals = {
            'temperature': round(temp_c, 1),
            'heart_rate': int(row.get('heart_rate', 72)),
            'systolic_bp': int(row.get('systolic_bp', 120)),
            'diastolic_bp': int(row.get('diastolic_bp', 80)),
            'oxygen_saturation': round(float(row.get('oxygen_saturation', 98.5)), 1),
            'platelet_count': platelet,
            'hemoglobin': round(float(row.get('hemoglobin', 15.0)), 1),
            'wbc_count': int(row.get('wbc_count', 7000)),
            'rbc_count': round(float(row.get('rbc_count', 5.2)), 2),
            'fatigue': max(0, int(row.get('fatigue', 0)) - int(med_recovery * 30)),
            'hydration': min(100, int(row.get('hydration', 100)) + (20 if "IV Fluids" in medications else 0)),
            'pain_level': max(0, int(row.get('pain_level', 0)) - (30 if "Paracetamol" in medications or "Anti-inflammatory (NSAIDs)" in medications else 0)),
            'inflammation': max(0, int(row.get('inflammation', 0)) - (30 if "Anti-inflammatory (NSAIDs)" in medications else 0)),
            'nausea': int(row.get('nausea', 0)),
            'headache': int(row.get('headache', 0)),
            'weakness': int(row.get('weakness', 0)),
        }

        # Optional disease-specific columns
        vitals['spleen_size'] = float(row.get('spleen_size', 1.0))
        vitals['liver_enzymes'] = int(row.get('liver_enzymes', 40))
        vitals['parasite_load'] = int(row.get('parasite_load', 0))
        vitals['rash_severity'] = int(row.get('rash_severity', 0))
        vitals['bleeding_risk'] = bleeding_risk
        vitals['plasma_leakage'] = plasma_leakage
        vitals['joint_swelling'] = int(row.get('joint_swelling', 0))
        vitals['muscle_pain'] = int(row.get('muscle_pain', 0))
        vitals['joint_stiffness'] = int(row.get('joint_stiffness', 0))
        vitals['joint_pain'] = int(row.get('joint_pain', 0))

        # Determine active progression/severity index (scaled 0.0 - 1.0)
        prog = max(0.0, min(1.0, (temp_c - 36.5) / 4.5))
        if platelet < 150:
            prog = max(prog, min(1.0, (150 - platelet) / 130))

        effective_progression = max(0.0, prog * (1 - med_recovery))

        # Compute organ risks
        vitals['organ_risks'] = self._compute_organ_risks(day, effective_progression, med_organ)
        vitals['severity'] = effective_progression * 100
        
        # We estimate total days based on loaded CSV index length
        if isinstance(self.csv_data.index, pd.MultiIndex):
            total_days = int(self.csv_data['day'].max()) + 1
        else:
            total_days = len(self.csv_data)
            
        rec_factor = (day / total_days) if total_days > 0 else 1.0
        vitals['recovery_probability'] = max(0, min(100, (1.0 - effective_progression) * 70 + rec_factor * 30 + med_recovery * 30))
        vitals['progression'] = effective_progression
        vitals['day'] = day
        vitals['disease'] = self.current_disease
        vitals['medications'] = list(medications)
        vitals['hospitalization_risk'] = max(0, min(100, effective_progression * 85))

        return vitals

    def get_day_data(self, day: int, medications: List[str] = None) -> Dict:
        """Generate comprehensive vital signs and organ data for a given day."""
        if self.is_csv_mode and self.csv_data is not None:
            if isinstance(self.csv_data.index, pd.MultiIndex):
                # Filter rows for the given day
                day_rows = self.csv_data[self.csv_data['day'] == day]
                if not day_rows.empty:
                    if 12 in day_rows['hour'].values:
                        row = day_rows[day_rows['hour'] == 12].iloc[0]
                    else:
                        closest_idx = (day_rows['hour'] - 12).abs().idxmin()
                        row = self.csv_data.loc[closest_idx]
                    return self._parse_csv_row(row, day, medications)
            else:
                if day in self.csv_data.index:
                    row = self.csv_data.loc[day]
                    return self._parse_csv_row(row, day, medications)

        profile = DISEASE_PROFILES.get(self.current_disease)
        if not profile:
            return self._empty_data()


        # Base disease progression curve (0-1)
        progression = self._get_progression(day, profile)
        recovery_factor = self._get_recovery_factor(day, profile)

        # Apply active medication effects dynamically for this specific day
        med_fever = 0.0
        med_recovery = 0.0
        med_organ = 0.0

        medications = medications if medications is not None else []
        for med in medications:
            if med in MEDICATION_EFFECTS:
                eff = MEDICATION_EFFECTS[med]
                med_fever += eff.get("fever_reduction", 0.0)
                med_recovery += eff.get("recovery_boost", 0.0)
                med_organ += eff.get("organ_protection", 0.0)

        med_organ = min(0.8, med_organ)

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
        data['medications'] = list(medications)
        data['hospitalization_risk'] = max(0, min(100, effective_progression * 85))

        return data

    def get_hour_data(self, day: int, hour: int, medications: List[str] = None) -> Dict:
        """Generate/retrieve vital signs and organ data for a given day and hour."""
        medications = medications if medications is not None else []
        
        # If in CSV mode and MultiIndex is loaded
        if self.is_csv_mode and self.csv_data is not None:
            if isinstance(self.csv_data.index, pd.MultiIndex):
                if (day, hour) in self.csv_data.index:
                    row = self.csv_data.loc[(day, hour)]
                    return self._parse_csv_row(row, day, medications)
            
            # Fallback if CSV has only day-level records
            if day in self.csv_data.index:
                # Interpolate between this day and next day at the given hour fraction
                f = hour / 24.0
                row_curr = self.csv_data.loc[day]
                next_day = min(len(self.csv_data) - 1, day + 1)
                row_next = self.csv_data.loc[next_day]
                
                row_interp = {}
                for col in self.csv_data.columns:
                    try:
                        v_curr = float(row_curr[col])
                        v_next = float(row_next[col])
                        row_interp[col] = (1.0 - f) * v_curr + f * v_next
                    except:
                        row_interp[col] = row_curr[col]
                
                return self._parse_csv_row(row_interp, day, medications)

        # Simulated (non-CSV) mode or fallback:
        # Interpolate day-level baselines and overlay realistic circadian patterns
        day_data = self.get_day_data(day, medications)
        next_day_data = self.get_day_data(min(21, day + 1), medications)
        
        f = hour / 24.0
        vitals = {}
        for key in day_data:
            if key in ('temperature', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'oxygen_saturation', 'platelet_count', 'hemoglobin', 'wbc_count', 'rbc_count', 'fatigue', 'hydration', 'pain_level', 'inflammation', 'nausea', 'headache', 'weakness', 'spleen_size', 'liver_enzymes', 'parasite_load', 'rash_severity', 'bleeding_risk', 'plasma_leakage', 'joint_swelling', 'muscle_pain', 'joint_stiffness', 'joint_pain'):
                try:
                    v_curr = float(day_data[key])
                    v_next = float(next_day_data[key])
                    vitals[key] = (1.0 - f) * v_curr + f * v_next
                except:
                    vitals[key] = day_data[key]
            else:
                vitals[key] = day_data[key]
                
        # Add circadian/hourly fluctuations on top of the interpolated values
        circadian_temp = 0.4 * np.sin((hour - 8) * 2 * np.pi / 24.0)
        vitals['temperature'] = round(vitals['temperature'] + circadian_temp, 1)
        
        circadian_hr = 5 * np.sin((hour - 8) * 2 * np.pi / 24.0)
        vitals['heart_rate'] = int(vitals['heart_rate'] + circadian_hr)
        
        # Malaria cyclic fever paroxysm: fluctuates hour-by-hour
        if self.current_disease == "Malaria":
            total_hours = day * 24 + hour
            cycle_phase = np.sin(total_hours * 2 * np.pi / 48.0)
            if cycle_phase > 0.6:
                vitals['temperature'] = round(vitals['temperature'] + 1.5 * cycle_phase, 1)
                vitals['heart_rate'] = int(vitals['heart_rate'] + 15 * cycle_phase)
                vitals['cyclic_phase'] = "Fever"
            elif cycle_phase < -0.6:
                vitals['temperature'] = round(vitals['temperature'] - 0.5 * abs(cycle_phase), 1)
                vitals['cyclic_phase'] = "Chills"
            else:
                vitals['cyclic_phase'] = "Sweating" if cycle_phase > 0 else "Normal"
                
        vitals['day'] = day
        vitals['hour'] = hour
        
        # Recalculate organ risks
        med_organ = 0.0
        for med in medications:
            if med in MEDICATION_EFFECTS:
                med_organ += MEDICATION_EFFECTS[med].get("organ_protection", 0.0)
        med_organ = min(0.8, med_organ)
        vitals['organ_risks'] = self._compute_organ_risks(day, vitals.get('progression', 0.1), med_organ)
        
        return vitals

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
            'joint_pain': joint_pain,
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

    def get_organ_status_html(self, organ_name: str, data: dict) -> str:
        """Generate high-fidelity HTML-formatted status scan for the selected organ showing baseline, current, and post-intervention prognosis."""
        organ_risks = data.get('organ_risks', {})
        disease = data.get('disease', self.current_disease)
        day = data.get('day', 0)
        hour = data.get('hour', 12)
        meds = data.get('medications', [])
        p = data.get('progression', 0.0)
        
        # Determine risk level and score
        level = "Low"
        score = 0.0
        if organ_name in organ_risks:
            level, score = organ_risks[organ_name]
        
        # Color coding for risk level
        color_map = {
            "Low": "#00e676",      # Green
            "Medium": "#ff9100",   # Orange
            "High": "#ff5252",     # Light Red
            "Critical": "#d50000"  # Deep Red
        }
        risk_color = color_map.get(level, "#7ecbf5")
        
        # ── 1. BEFORE EFFECTS (BASELINE STATUS) ──
        before_desc = {
            "Liver": "Healthy hepatocytes, metabolic clearance of toxins, normal protein synthesis. ALT transaminases remain stable &lt; 40 U/L.",
            "Spleen": "Normal diameter of ~1.0 cm. Baseline clearance of senescent erythrocytes. No left upper quadrant discomfort.",
            "Brain": "Intact blood-brain barrier. Normal cerebral perfusion and oxygenation. Cognitive function is baseline; zero headache.",
            "Heart": "Sinus rhythm, normal heart rate (60-100 bpm), stable stroke volume, and blood pressure within 120/80 mmHg range.",
            "Lungs": "Clear bilateral breath sounds. Intact pleural membranes. Oxygen saturation (SpO2) sits stably at 97-100% on room air.",
            "Kidneys": "Glomerular filtration rate &gt; 90 mL/min, normal urine concentration, stable creatinine/hydration (100%).",
            "Blood System": "Platelets 150k-450k/uL, Hemoglobin 12-16 g/dL, WBC 4k-11k/uL. Normal clotting cascades and RBC oxygen carrying capacity.",
            "Muscles": "Stable muscle tone, intact sarcolemma, zero inflammatory markers, normal lactic acid clearance, full motor strength.",
            "Joints": "Smooth synovial fluid, uninflamed articular cartilage, normal range of motion in extremities, zero pain/stiffness.",
            "Skin": "Normal skin turgor, clear dermal layers, zero rash, petechiae, or pruritus."
        }.get(organ_name, "Baseline physiology is normal with standard vital bounds.")

        # ── 2. CURRENT CONDITION (REAL-TIME STATUS) ──
        metrics_html = ""
        if organ_name == "Liver":
            alt = data.get('liver_enzymes', 40)
            metrics_html = f"ALT Transaminase: {alt} U/L (Normal: &lt;40 U/L)"
        elif organ_name == "Spleen":
            sz = data.get('spleen_size', 1.0)
            metrics_html = f"Splenic Diameter: {sz:.1f} cm (Normal: 1.0 cm)"
        elif organ_name == "Brain":
            headache = data.get('headache', 0)
            temp = data.get('temperature', 36.6)
            metrics_html = f"Headache: {int(headache)}% | Systemic Temp: {temp:.1f}°C"
        elif organ_name == "Heart":
            hr = data.get('heart_rate', 72)
            sbp = data.get('systolic_bp', 120)
            dbp = data.get('diastolic_bp', 80)
            metrics_html = f"Heart Rate: {hr} bpm | BP: {sbp}/{dbp} mmHg"
        elif organ_name == "Lungs":
            o2 = data.get('oxygen_saturation', 98.5)
            leak = data.get('plasma_leakage', 0)
            metrics_html = f"SpO2 Saturation: {o2:.1f}% | Pleural Leakage: {int(leak)}%"
        elif organ_name == "Kidneys":
            hyd = data.get('hydration', 100)
            metrics_html = f"Renal Perfusion: {'Adequate' if hyd > 65 else 'Impaired'} | Hydration: {int(hyd)}%"
        elif organ_name == "Blood System":
            hb = data.get('hemoglobin', 15.0)
            rbc = data.get('rbc_count', 5.0)
            wbc = data.get('wbc_count', 7000)
            plat = data.get('platelet_count', 250)
            metrics_html = f"Platelets: {plat}k/uL | Hb: {hb:.1f} g/dL | RBC: {rbc:.2f}M | WBC: {wbc}"
        elif organ_name == "Muscles":
            pain = data.get('muscle_pain', data.get('pain_level', 0))
            weak = data.get('weakness', 0)
            metrics_html = f"Myalgia Severity: {int(pain)}% | Muscle Weakness: {int(weak)}%"
        elif organ_name == "Joints":
            jp = data.get('joint_pain', data.get('pain_level', 0))
            js = data.get('joint_swelling', 0)
            jst = data.get('joint_stiffness', 0)
            metrics_html = f"Joint Pain: {int(jp)}% | Swelling: {int(js)}% | Stiffness: {int(jst)}%"
        elif organ_name == "Skin":
            rash = data.get('rash_severity', 0)
            bleed = data.get('bleeding_risk', 0)
            metrics_html = f"Rash Coverage: {int(rash)}% | Petechiae Risk: {int(bleed)}%"
        else:
            metrics_html = "Metrics within normal baseline range."

        is_recovery = day >= 7
        pathology = ""
        
        if disease == "Malaria":
            if organ_name == "Liver":
                pathology = "Hepatic clearance phase. The exoerythrocytic cycle has ended; liver cells are slowly recovering." if is_recovery else ("Active hepatic stage. Hepatocytes are under strain from merozoite multiplication and focal tissue congestion." if p > 0.35 else "Early incubation. Sporozoites have invaded hepatocytes to multiply into merozoites; subclinical transaminase elevations.")
            elif organ_name == "Spleen":
                pathology = "Splenic regression. Erythrocyte clearance load is decreasing, allowing the spleen to slowly shrink." if is_recovery else (f"Severe splenomegaly. Spleen is swollen to {data.get('spleen_size', 1.0):.1f}x normal size due to rapid clearance of damaged RBCs; high rupture risk." if p > 0.35 else "Early immune reaction. Splenic blood filtration is accelerating, causing mild congestion.")
            elif organ_name == "Brain":
                pathology = "Microvascular recovery. Adhesion of infected cells has resolved; neurological risk is low." if is_recovery else ("Microvascular sequestration warning. Parasitized RBCs are adhering to vessel walls, obstructing blood flow." if p > 0.35 else "Early headache. Mild blood flow changes in response to systemic inflammatory release.")
            elif organ_name == "Heart":
                pathology = f"Compensatory tachycardia ({data.get('heart_rate', 72)} bpm) driven by high systemic fever paroxysms. Workload is elevated to maintain oxygen perfusion."
            elif organ_name == "Lungs":
                pathology = "Mild respiratory strain. Systemic febrile load increases metabolic oxygen requirements." if p > 0.35 else "Stable respiration. Airway clearance is normal, maintaining SpO2."
            elif organ_name == "Kidneys":
                pathology = "Hemoglobin filtration strain. Intense hemolysis releases free hemoglobin, risking tubular obstruction and acute tubular necrosis." if p > 0.35 else "Renal function is stable. Adequate hydration supports clearance."
            elif organ_name == "Blood System":
                pathology = "Hematopoietic recovery. Bone marrow is actively generating new RBCs (erythropoiesis) to restore counts." if is_recovery else ("Acute hemolytic anemia. Rapid intravascular lysis of infected red blood cells is driving hemoglobin and RBC count drops." if p > 0.35 else "Early parasitemia. RBC invasion has begun, with low-level hemolysis.")
            elif organ_name in ("Muscles", "Joints"):
                pathology = "Mild systemic arthralgia/myalgia. Pain is driven by pyrogenic cytokine release (IL-1, TNF-alpha) during fever peaks."
            else:
                pathology = f"Baseline physiology remains stable. No active disease markers detected."
                
        elif disease == "Dengue Fever":
            if organ_name == "Liver":
                pathology = "Hepatic tissue resolution. Transaminases are stabilizing, and risk of acute liver injury is passing." if is_recovery else ("Direct viral hepatocyte strain. Dengue replication in liver cells causes ALT/AST elevation and moderate hepatomegaly." if p > 0.35 else "Early systemic viremia. Minor hepatic exposure with subclinical transaminase elevations.")
            elif organ_name == "Blood System":
                pathology = "Platelet recovery. Bone marrow is restoring platelets, and plasma leakage has ceased." if is_recovery else ("Critical thrombocytopenia. Severe platelet destruction by anti-platelet antibodies and capillary leakage." if p > 0.35 else "Platelets are beginning to fall due to viral suppression of hematopoietic progenitor cells.")
            elif organ_name == "Heart":
                pathology = "Hypovolemia. Plasma leakage out of capillary beds reduces blood volume, causing hypotension and reflex tachycardia." if p > 0.35 else "Cardiac stability. Mild compensatory heart rate elevation."
            elif organ_name == "Lungs":
                pathology = "Pleural effusion risk. Increased capillary permeability drives plasma leakage into the pleural space, compressing the lungs." if p > 0.35 else "Lungs are clear. Pleural membranes are dry and intact."
            elif organ_name == "Kidneys":
                pathology = "Pre-renal AKI risk. Capillary leakage and dehydration reduce renal blood flow, causing glomerular filtration strain." if p > 0.35 else "Filtration is stable. Adequate hydration supports function."
            elif organ_name == "Skin":
                pathology = "Convalescent rash. Classical 'white islands in a sea of red' rash appears, showing recovery of capillary integrity." if is_recovery else ("Vascular maculopapular rash and micro-hemorrhages (petechiae) in dermal layers due to thrombocytopenia." if p > 0.35 else "Transient early flushing. Skin erythema due to vasodilation.")
            elif organ_name in ("Muscles", "Joints"):
                pathology = "Severe 'breakbone' myalgia. Viral infection of muscle fibers and cytokine release cause agonizing pain."
            else:
                pathology = f"Baseline physiology remains stable. No active disease markers detected."

        elif disease == "Chikungunya":
            if organ_name == "Joints":
                pathology = "Sub-acute joint arthritis. Joint inflammation is declining, though sub-acute stiffness can persist." if is_recovery else ("Debilitating polyarthritis. Viral replication in synovial fibroblasts causes severe swelling, stiffness, and extreme pain." if p > 0.35 else "Early joint stiffness. Discomfort and mild arthralgia in fingers, wrists, knees, and ankles.")
            elif organ_name == "Muscles":
                pathology = "Systemic myositis. Viral infiltration of skeletal muscles is causing muscle pain, soreness, and moderate weakness." if p > 0.35 else "Mild muscle fatigue and soreness secondary to viral immunopathology."
            elif organ_name == "Liver":
                pathology = "Subclinical liver strain. Mild transaminase elevation due to general systemic inflammatory cytokine production."
            elif organ_name == "Skin":
                pathology = "Maculopapular rash active. Pruritic rash is distributed over the torso and extremities." if p > 0.35 else "Mild dermal warmth due to high fever."
            else:
                pathology = f"Baseline physiology remains stable. No active disease markers detected."
        else:
            pathology = "Normal baseline physiology. No active disease markers detected."

        # ── 3. AFTER EFFECTS & PROGNOSIS (POST-INTERVENTION) ──
        after_desc = ""
        active_meds_desc = []
        
        if meds:
            for med in meds:
                if med == "Paracetamol":
                    if organ_name == "Liver":
                        active_meds_desc.append("• <b>Paracetamol</b>: Reduces fever. <b style='color:#ff5252;'>WARNING:</b> High doses strain hepatocytes. ALT/AST should normalize in 3-5 days if dose is kept under 3g/day.")
                    else:
                        active_meds_desc.append("• <b>Paracetamol</b>: Effectively controls fever, reducing cardiac workload and metabolic rate.")
                elif med == "IV Fluids":
                    if organ_name in ("Heart", "Kidneys", "Lungs"):
                        active_meds_desc.append("• <b>IV Fluids</b>: Restores volume. Stabilizes BP and kidney filtration. <b style='color:#ff9100;'>Warning:</b> Monitor SpO2 to avoid pleural overload.")
                    elif organ_name == "Blood System":
                        active_meds_desc.append("• <b>IV Fluids</b>: Directly counteracts plasma leak and hemoconcentration, stabilizing hematocrit.")
                    else:
                        active_meds_desc.append("• <b>IV Fluids</b>: Restores systemic hydration and protects vital organ tissue perfusion.")
                elif med == "Platelet Transfusion":
                    if organ_name == "Blood System":
                        active_meds_desc.append("• <b>Platelets</b>: Resolves thrombocytopenia. Platelet count will rise back above critical bleeding threshold in 1-2 days.")
                    elif organ_name == "Skin":
                        active_meds_desc.append("• <b>Platelets</b>: Stops dermal micro-hemorrhages (petechiae) and resolves skin bleeding risks.")
                    else:
                        active_meds_desc.append("• <b>Platelets</b>: Supports global hemostasis.")
                elif med in ("Artemether", "Chloroquine"):
                    if organ_name in ("Liver", "Spleen", "Blood System", "Brain"):
                        active_meds_desc.append(f"• <b>{med}</b>: Directly clears malaria parasites. Hemolysis and organ congestion will resolve, and spleen size will regress to 1.0 cm in 2 weeks.")
                    else:
                        active_meds_desc.append(f"• <b>{med}</b>: Eliminates parasite replication, preventing further systemic risk progression.")
                elif med == "NSAIDs (Ibuprofen)":
                    if organ_name in ("Joints", "Muscles"):
                        active_meds_desc.append("• <b>Ibuprofen</b>: Suppresses COX inflammation. Joint swelling and stiffness will regress over 5-7 days.")
                    elif organ_name == "Kidneys":
                        active_meds_desc.append("• <b>Ibuprofen</b>: <b style='color:#ff9100;'>Warning:</b> NSAID constriction of renal arterioles can increase creatinine; monitor hydration.")
                    else:
                        active_meds_desc.append("• <b>Ibuprofen</b>: Alleviates joint pain, myalgia, and generalized tissue inflammation.")
            after_desc = "<br>".join(active_meds_desc)
        else:
            prognosis = "• <b>No active treatment</b>. "
            if disease == "Malaria":
                if organ_name == "Spleen":
                    prognosis += "Untreated parasitemia risks severe splenomegaly, splenic infarction, or splenic rupture under physical trauma."
                elif organ_name == "Kidneys":
                    prognosis += "Severe hemolysis risks tubular occlusion (Blackwater Fever) and acute tubular necrosis."
                elif organ_name == "Brain":
                    prognosis += "Obstructed cerebral microcirculation risks cerebral malaria, coma, and a 20% mortality rate."
                elif organ_name == "Blood System":
                    prognosis += "Continued RBC destruction risks severe hemolytic anemia and tissue hypoxia."
                else:
                    prognosis += "Recommend administering <b>Artemether</b> or <b>Chloroquine</b> to clear plasmodium parasites."
            elif disease == "Dengue Fever":
                if organ_name == "Blood System":
                    prognosis += "Thrombocytopenia risks severe gastrointestinal hemorrhage or internal bleeding."
                elif organ_name == "Heart":
                    prognosis += "Severe capillary leakage risks hypovolemic collapse (Dengue Shock Syndrome)."
                elif organ_name == "Lungs":
                    prognosis += "Uncontrolled plasma leakage risks severe pleural effusion and respiratory failure."
                else:
                    prognosis += "Recommend administering supportive <b>IV Fluids</b> to maintain blood volume."
            elif disease == "Chikungunya":
                if organ_name in ("Joints", "Muscles"):
                    prognosis += "Synovial inflammation risks transition to chronic arthralgia and persistent joint stiffness lasting months."
                else:
                    prognosis += "Recommend administering <b>NSAIDs (Ibuprofen)</b> to control arthritis inflammation."
            else:
                prognosis += "Baseline prognosis is excellent. Rest and hydration are supportive."
            after_desc = prognosis

        # Build the HTML output
        html = f"""
        <div style="font-family: 'Consolas', monospace; font-size: 11px; color: #7ecbf5;">
            <div style="border-bottom: 1px solid #0d2d5e; padding-bottom: 4px; margin-bottom: 6px;">
                <span style="color: #4fc3f7; font-weight: bold;">◈ ORGAN SCAN:</span> {organ_name.upper()}<br>
                <span style="color: #4fc3f7; font-weight: bold;">◈ RISK LEVEL:</span> 
                <span style="color: {risk_color}; font-weight: bold;">{level.upper()} ({int(score)}%)</span>
            </div>
            
            <div style="margin-bottom: 6px;">
                <span style="color: #5a8fd4; font-weight: bold;">1. BEFORE EFFECTS (BASELINE STATUS)</span><br>
                <span style="color: #a0c0e0;">• {before_desc}</span>
            </div>
            
            <div style="margin-bottom: 6px; border-top: 1px solid #0a1b33; padding-top: 4px;">
                <span style="color: #ffaa00; font-weight: bold;">2. CURRENT CONDITION (REAL-TIME STATUS)</span><br>
                <span style="color: #ffffff;">• Metrics: {metrics_html}<br>• Pathology: {pathology}</span>
            </div>
            
            <div style="margin-bottom: 4px; border-top: 1px solid #0a1b33; padding-top: 4px;">
                <span style="color: #00e676; font-weight: bold;">3. AFTER EFFECTS & PROGNOSIS (POST-INTERVENTION)</span><br>
                <span style="color: #b0e8b0;">{after_desc}</span>
            </div>
        </div>
        """
        return html
