"""
AI Health Prediction Engine
Analyzes disease progression, vital signs, and generates clinical predictions
"""

import numpy as np
from typing import Dict, List


class AIPredictionEngine:
    def __init__(self):
        self.rng = np.random.RandomState(123)

    def analyze(self, disease: str, day: int, data: Dict, medications: List[str]) -> str:
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
        remaining = max(1, 21 - day)
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

        # Build HTML report

        html = f"""
<div style="font-family: Consolas, monospace; font-size: 12px; line-height: 1.7; color: #7ecbf5;">
<div style="border-bottom: 1px solid #0d2d5e; padding-bottom: 6px; margin-bottom: 8px;">
  <span style="color: #4fc3f7; font-size: 15px; font-weight: bold; letter-spacing: 0.5px;">
    AI HEALTH ANALYSIS REPORT
  </span><br>
  <span style="color: #3a6ea0;">Disease: {disease} | Day {day} of 21</span>
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
            if prog > 0.7 and 'Artemisinin (ACT)' not in medications:
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
                complications.append("Persistent joint damage — physiotherapy recommended")

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
