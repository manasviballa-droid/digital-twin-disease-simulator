"""
AI Health Prediction Engine
Analyzes disease progression, vital signs, and generates clinical predictions
"""

import numpy as np
from typing import Dict, List


class AIPredictionEngine:
    def __init__(self):
        self.rng = np.random.RandomState(123)

    def analyze(self, disease: str, day: int, data: Dict, medications: List[str], sim_hour: int = 0, sim_minute: int = 0, max_days: int = 21) -> str:
        color_map = {
            "CRITICAL": "#b83b3b", "HIGH": "#c45d30", "MEDIUM": "#b88a30",
            "LOW": "#4faf8c", "GOOD": "#4faf8c", "GUARDED": "#b88a30", "POOR": "#c45d30"
        }

        def colored(text, level):
            c = color_map.get(level.upper(), "#4fc3f7")
            return f'<span style="color:{c}; font-weight:bold;">{text}</span>'

        prog = data.get('progression', 0)
        severity = data.get('severity', 0)
        recovery = data.get('recovery_probability', 0)
        hosp_risk = data.get('hospitalization_risk', 0)

        temp_c = data.get('temperature', 36.6)
        temp_f = temp_c * 1.8 + 32.0
        hr = data.get('heart_rate', 72)
        spo2 = data.get('oxygen_saturation', 98)
        platelet = data.get('platelet_count', 250)
        hgb = data.get('hemoglobin', 15.0)
        wbc = data.get('wbc_count', 7000)

        organ_risks = data.get('organ_risks', {})
        critical_organs = [o for o, (lvl, _) in organ_risks.items() if lvl == "Critical"]
        high_organs = [o for o, (lvl, _) in organ_risks.items() if lvl == "High"]

        # Compute composite risk
        critical_count = len(critical_organs)
        high_count = len(high_organs)
        composite_risk = min(100, severity + critical_count * 15 + high_count * 8)

        # Duration estimate
        remaining = max(1, max_days - day)
        with_meds = max(1, remaining - len(medications) * 2)
        recovery_days = with_meds if medications else remaining

        # Complications
        complications = self._get_complications(disease, data, medications)

        # Prognosis
        prognosis = self._get_prognosis(composite_risk, recovery, medications)

        # Medication effects section
        from disease_engine import MEDICATION_EFFECTS
        
        med_effects_html = []
        if not medications:
            med_effects_html.append(
                f'<span style="color:#ff6b35; font-weight:bold;">⚠️ NO ACTIVE MEDICAL TREATMENT</span><br>'
                f'• Patient body is fighting infection using baseline immune response.<br>'
                f'• High risk of temperature spikes and unchecked organ damage.<br>'
                f'• Recommendation: Administer targeted medications immediately.'
            )
        else:
            total_fever_red = 0.0
            total_rec_boost = 0.0
            total_organ_prot = 0.0
            all_side_effects = []
            
            for med in medications:
                if med in MEDICATION_EFFECTS:
                    eff = MEDICATION_EFFECTS[med]
                    f_red = eff.get("fever_reduction", 0.0)
                    r_boost = eff.get("recovery_boost", 0.0) * 100
                    o_prot = eff.get("organ_protection", 0.0) * 50  # organ risk reduction percentage
                    side = eff.get("side_effects", [])
                    
                    total_fever_red += f_red
                    total_rec_boost += r_boost
                    total_organ_prot += o_prot
                    all_side_effects.extend(side)
                    
            summary_points = []
            if disease == "Malaria" and "Chloroquine" in medications:
                summary_points.append("• <b>Chloroquine Action</b>: It controls thermal and reduces risk of spreading.")
            if disease == "Dengue Fever" and "Oral Rehydration (ORT)" in medications:
                summary_points.append("• <b>Oral Rehydration Action</b>: Maintenance of electrolyte balance and maintenance of overall fluids.")
            if disease == "Dengue Fever" and "IV Fluids" in medications:
                summary_points.append("• <b>IV Fluids Action</b>: Maintenance of hydration and electrolyte balance.")
            if disease == "Dengue Fever" and "Platelet Transfusion" in medications:
                summary_points.append("• <b>Platelet Transfusion Action</b>: To reduce risk of bleeding, to reduce infections, and maintenance of platelets.")
            if disease == "Chikungunya" and "Anti-inflammatory (NSAIDs)" in medications:
                summary_points.append("• <b>Anti-inflammatory Action</b>: Temperature reduces, pain reduces, and reduces risk of rashes.")
            if total_fever_red > 0:
                summary_points.append(f"• <b>Thermal Control</b>: Fever temperature reduced by {total_fever_red*1.8:.1f}°F, lowering cardiovascular stress.")
            if total_organ_prot > 0:
                summary_points.append(f"• <b>Organ Defense</b>: Major organ strain reduced by {min(40.0, total_organ_prot):.0f}%, preventing critical organ failures.")
            if total_rec_boost > 0:
                summary_points.append(f"• <b>Immune Boost</b>: Overall recovery pathway accelerated by {total_rec_boost:.0f}%.")
            if all_side_effects:
                unique_side = list(set(all_side_effects))
                summary_points.append(f"• ⚠️ <b>Side Effects Warning</b>: Patient showing mild {', '.join(unique_side)}.")
                
            med_effects_html.append("<br>".join(summary_points))

        meds_section = "<br>".join(med_effects_html)
        timeline_section = self._get_24h_timeline(disease, day, data, medications, sim_hour, sim_minute)

        # Build HTML report

        html = f"""
<div style="font-family: Consolas, monospace; font-size: 12px; line-height: 1.7; color: #7ecbf5;">
<div style="border-bottom: 1px solid #0d2d5e; padding-bottom: 6px; margin-bottom: 8px;">
  <span style="color: #4fc3f7; font-size: 15px; font-weight: bold; letter-spacing: 0.5px;">
    AI HEALTH ANALYSIS REPORT
  </span><br>
  <span style="color: #3a6ea0;">Disease: {disease} | Day {day} of {max_days} @ {sim_hour:02d}:{sim_minute:02d}</span>
</div>

<span style="color: #4fc3f7; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">━━ SEVERITY ASSESSMENT ━━</span><br>
Composite Risk Score: {colored(f'{composite_risk:.0f}/100', 'CRITICAL' if composite_risk > 80 else ('HIGH' if composite_risk > 60 else 'MEDIUM'))}<br>
<br>

<span style="color: #4fc3f7; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">━━ TREATMENT IMPACT & PHYSIOLOGICAL EFFECTS ━━</span><br>
{meds_section}<br>
<br>

<span style="color: #4fc3f7; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">━━ ORGAN RISK SUMMARY ━━</span><br>
{f'<span style="color:#b83b3b; font-weight:bold;">⚠️ CRITICAL ORGANS: {", ".join(critical_organs)}</span><br>' if critical_organs else ''}
{f'<span style="color:#c45d30; font-weight:bold;">▲ HIGH RISK ORGANS: {", ".join(high_organs)}</span><br>' if high_organs else ''}
{f'<span style="color:#4faf8c; font-weight:bold;">✓ All organs within acceptable risk</span><br>' if not critical_organs and not high_organs else ''}
<br>

<span style="color: #4fc3f7; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">━━ COMPLICATIONS FORECAST ━━</span><br>
{"".join(f'• {c}<br>' for c in complications)}
<br>

<span style="color: #4fc3f7; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">━━ 24-HOUR CLINICAL TIMELINE (TODAY) ━━</span><br>
{timeline_section}<br>
<br>

<span style="color: #4fc3f7; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">━━ TREATMENT RESPONSE ━━</span><br>
Active Medications: {colored(str(len(medications)), 'GOOD') if medications else colored('NONE — UNTREATED', 'HIGH')}<br>
{("".join(f'✓ <span style="color:#4faf8c; font-weight:bold;">{m}</span><br>' for m in medications)) if medications else ''}
Estimated Recovery: {colored(f'~{recovery_days} days remaining', 'GOOD' if recovery_days < 7 else ('MEDIUM' if recovery_days < 12 else 'HIGH'))}<br>
<br>

<span style="color: #4fc3f7; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">━━ PROGNOSIS ━━</span><br>
{colored(prognosis, prognosis.split()[0] if prognosis else 'MEDIUM')}
</div>
"""
        return html

    def _get_complications(self, disease, data, medications):
        prog = data.get('progression', 0)
        complications = []

        if disease == "Malaria":
            if prog > 0.6 and data.get('hemoglobin', 15) < 8:
                complications.append("Severe hemolytic anemia — transfusion may be required")
            if prog > 0.7 and 'Chloroquine' not in medications:
                complications.append("Cerebral malaria risk — neurological involvement possible")
            if prog > 0.5:
                complications.append("Splenomegaly — organ enlargement progressing")
            if prog > 0.8:
                complications.append("Acute kidney injury — monitor creatinine levels")
        elif disease == "Dengue Fever":
            if data.get('platelet_count', 250) < 50:
                complications.append("SEVERE thrombocytopenia — hemorrhage imminent")
            if prog > 0.5:
                complications.append("Dengue shock syndrome — plasma leakage risk")
            if data.get('liver_enzymes', 40) > 100:
                complications.append("Hepatitis — elevated liver enzymes")
            if prog > 0.6:
                complications.append("Internal bleeding — monitor for signs")
        elif disease == "Chikungunya":
            if prog > 0.4:
                complications.append("Chronic polyarthritis — may persist months")
            if prog > 0.6:
                complications.append("Post-infectious neuropathy risk")
            if prog > 0.5:
                complications.append("Persistent joint damage — physical therapy and rest recommended")

        if not complications:
            complications.append("No immediate complications detected")
        return complications

    def _get_prognosis(self, risk, recovery, medications):
        if recovery > 75:
            outlook = "GOOD: Patient expected to recover within normal timeframe"
        elif recovery > 50:
            outlook = "GUARDED: Recovery likely with appropriate treatment"
        elif recovery > 25:
            outlook = "POOR: Significant complications risk — intensive care may be needed"
        else:
            outlook = "CRITICAL: Immediate medical intervention required"

        if medications:
            outlook += f". Treatment protocol reducing severity by estimated {len(medications) * 15}%."
        return outlook

    def _get_24h_timeline(self, disease: str, day: int, data: Dict, medications: List[str], sim_hour: int, sim_minute: int) -> str:
        temp_c = data.get('temperature', 36.6)
        temp_f = temp_c * 1.8 + 32.0
        hr = data.get('heart_rate', 72)
        pain = data.get('pain_level', 0)
        fatigue = data.get('fatigue', 0)
        hydration = data.get('hydration', 100)
        wbc = data.get('wbc_count', 7000)
        platelets = data.get('platelet_count', 250)
        hgb = data.get('hemoglobin', 15.0)

        phases = [
            ("00:00 - 06:00", "NIGHTTIME REST & METABOLIC BASAL STATE"),
            ("06:00 - 12:00", "MORNING CIRCADIAN RISE & STRESS LEVEL"),
            ("12:00 - 18:00", "MIDDAY IMMUNE INTERACTION & PEAK SYMPTOMS"),
            ("18:00 - 24:00", "EVENING RECOVERY & THERMOLYSIS")
        ]

        html_lines = []
        for time_range, phase_name in phases:
            start_h = int(time_range.split(":")[0])
            end_h = int(time_range.split(" - ")[1].split(":")[0])
            is_active = (start_h <= sim_hour < end_h)

            desc = ""
            if disease == "Chikungunya":
                joint_stiff = data.get('joint_stiffness', 0)
                joint_swel = data.get('joint_swelling', 0)
                muscle_pa = data.get('muscle_pain', 0)
                joint_pain = data.get('joint_pain', pain)

                if start_h == 0:
                    desc = f"Synovial fluid is cool and static; patient experiences joint stiffness ({joint_stiff}%) and muscle soreness ({muscle_pa}%) during nighttime. Temperature: {temp_f:.1f}°F."
                elif start_h == 6:
                    desc = f"Morning circadian cortisol rise. Patient reports pronounced stiffness ({joint_stiff}%) and joint inflammation. Heart rate: {hr} bpm."
                elif start_h == 12:
                    desc = f"Peak daily joint pain ({joint_pain}%) and swelling ({joint_swel}%) restricts physical mobility. Hydration status: {hydration}%."
                else:
                    desc = f"Significant weakness persists into evening hours. General fatigue: {fatigue}%. Anti-inflammatory treatments active."

            elif disease == "Dengue Fever":
                leakage = data.get('plasma_leakage', 0)
                bleeding = data.get('bleeding_risk', 0)

                if start_h == 0:
                    desc = f"Vascular permeability monitor active. Platelet count: {platelets}k/μL. Dehydration level at {100-hydration}%."
                elif start_h == 6:
                    desc = f"Circadian blood pressure shifts. Hemoglobin: {hgb} g/dL, indicating hematocrit status. WBC count: {wbc}/μL."
                elif start_h == 12:
                    desc = f"Midday retro-orbital headache and muscle pain peak. Fatigue: {fatigue}%. Plasma leakage rate: {leakage}%."
                else:
                    desc = f"Critical platelet crash warning. Hemorrhagic bleeding risk evaluated at {bleeding}%. Plasma leaking is {leakage}%."

            else:  # Malaria
                spleen = data.get('spleen_size', 1.0)
                parasites = data.get('parasite_load', 0)
                cyclic_phase = data.get('cyclic_phase', 'Fever')

                if start_h == 0:
                    desc = f"Basal metabolic strain from red blood cell lysis. Spleen enlargement is {spleen}x. Parasite count: {parasites}/μL."
                elif start_h == 6:
                    desc = f"Circ circadian immune response. Hemoglobin: {hgb} g/dL, checking for severe hemolytic anemia."
                elif start_h == 12:
                    desc = f"Patient is in cyclic **{cyclic_phase.upper()}** phase. Temperature: {temp_f:.1f}°F. Tachycardia risk with heart rate of {hr} bpm."
                else:
                    desc = f"Profuse sweating and heat dissipation as paroxysm completes. Fatigue is {fatigue}%. Rehydration is crucial (hydration: {hydration}%)."

            # Formatting
            if is_active:
                phase_title = f'<span style="color:#ffd600; font-weight:bold;">● {phase_name} ({time_range}) &lt;ACTIVE&gt;</span>'
                phase_desc = f'<span style="color:#ffffff;">• {desc}</span>'
            else:
                phase_title = f'<span style="color:#3a6ea0;">○ {phase_name} ({time_range})</span>'
                phase_desc = f'<span style="color:#5c8dbf;">• {desc}</span>'

            html_lines.append(f"{phase_title}<br>{phase_desc}")

        return "<br>".join(html_lines)
