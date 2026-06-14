# AI Digital Twin — Human Body Disease Simulator

An interactive, high-fidelity PyQt6 desktop application simulating the physiological progression and treatment response of infectious diseases (Malaria, Dengue Fever, and Chikungunya). This platform features a contoured 3D humanoid body model with glowing holographic organs, a real-time vitals dashboard, clinical charts, and an AI Health Prediction Engine.

Additionally, it supports a **Clinical CSV Mode** to import and visualize actual or synthetic patient datasets for "what-if" treatment analysis.

---

## Key Features

*   **Contoured 3D Humanoid Body Model**: 
    *   Tapered torso, neck, and limbs representing realistic anatomical proportions.
    *   Glass-like translucent body shell showing internal organs (Brain, Heart, Lungs, Liver, Spleen, Kidneys, Joints, Muscles).
    *   Dynamic holographic wireframe scanning grid overlays on affected organs.
    *   Dynamic blood vessel and skin rash rendering based on disease progression.
    *   Non-clipping camera-based zooming (`0.4x` to `5.0x`) and interactive orbital rotation.
*   **Real-time Vitals Dashboard**:
    *   Displays Fahrenheit (°F) temperature metrics, heart rate, blood pressure, SpO₂ levels, platelets, hemoglobin, and WBC counts.
    *   Adaptive, clinical color-coded status banners reflecting severity (Normal, Warning, Danger, Critical).
*   **Dual Data Modes**:
    *   **Simulator Mode**: Mathematical model simulating standard incubation, peak, and recovery curves.
    *   **Clinical CSV Import Mode**: Load external patient CSV logs (e.g. from clinical research or hospital EHR systems) to drive the digital twin telemetry.
*   **Autodetection of Disease Profiles**: When importing a CSV, the application scans the headers and automatically configures itself to Dengue, Malaria, or Chikungunya mode (updating labels, 3D highlights, and vitals).
*   **AI Health Prediction Engine**: Generates a consolidated clinical summary detailing thermal control, organ defense metrics, recovery speeds, and side effects.
*   **Interactive Treatment Panel**: Apply targeted medications (e.g., Artemisinin for Malaria, Paracetamol/IV fluids for Dengue, NSAIDs/Physiotherapy for Chikungunya) and immediately visualize vital signs recovering.

---

## Installation & Setup

### Prerequisites
*   Python 3.10 or higher
*   Pip package manager

### 1. Install Dependencies
Navigate to the project directory and install the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Start the simulator:
```bash
python main.py
```
*(On Unix-based systems, you can also run `./run.sh`)*

---

## Clinical CSV File Format

To import custom patient data, create a CSV file with a header row matching the format below. The day range can be flexible (the slider and charts will adjust dynamically).

| Column Header | Description | Expected Range / Units |
| :--- | :--- | :--- |
| `day` | Timeline index (starts at 0) | `0, 1, 2, ...` |
| `temperature` | Body temperature | `96.0 - 106.0` (°F) or `35.0 - 41.5` (°C) |
| `heart_rate` | Pulse frequency | `60 - 150` bpm |
| `systolic_bp` | Blood pressure upper limit | `90 - 150` mmHg |
| `diastolic_bp` | Blood pressure lower limit | `50 - 100` mmHg |
| `oxygen_saturation` | SpO₂ levels | `80 - 100` % |
| `platelet_count` | Platelets density | `10 - 400` ×10³/μL |
| `hemoglobin` | Red blood cell protein density | `5.0 - 18.0` g/dL |
| `wbc_count` | Immune cell count | `1000 - 15000` /μL |
| `fatigue` | Tiredness gauge | `0 - 100` % |
| `hydration` | Water levels | `0 - 100` % |
| `pain_level` | Pain indicator | `0 - 100` % |
| `inflammation` | Inflammation indicator | `0 - 100` % |

*Optional Disease-Specific Columns:*
*   **Malaria**: `parasite_load`, `spleen_size`
*   **Chikungunya**: `joint_pain`, `joint_swelling`, `joint_stiffness`, `muscle_pain`
*   **Dengue**: `rash_severity`, `bleeding_risk`, `plasma_leakage`

---

## Pre-Provided Clinical Datasets
Three sample datasets representing typical 14-day case trajectories are included in the repository:
1.  **[sample_clinical_dengue.csv](file:///c:/Users/Manasvi/Downloads/digital_twin_app%20(1)/sample_clinical_dengue.csv)**: Features early high fever, severe thrombocytopenia (platelet crash to `22`), leukopenia, and recovery.
2.  **[sample_clinical_malaria.csv](file:///c:/Users/Manasvi/Downloads/digital_twin_app%20(1)/sample_clinical_malaria.csv)**: Features tertian cyclic fever spikes, parasite load tracking, spleen enlargement, and hemolytic anemia (hemoglobin crash).
3.  **[sample_clinical_chikungunya.csv](file:///c:/Users/Manasvi/Downloads/digital_twin_app%20(1)/sample_clinical_chikungunya.csv)**: Features early fever, joint swelling, and chronic, persistent joint stiffness/pain.

---

## Project Structure

```
├── main.py                     # Main GUI layout, widgets, and window orchestration
├── disease_engine.py           # Core disease simulation profiles and CSV loader logic
├── body_model.py               # 3D Matplotlib humanoid meshes and rendering parameters
├── dashboard.py                # Real-time vitals card display and warning calculations
├── charts.py                   # Matplotlib chart panels (Fever, Vitals, Organ Risk)
├── organ_panel.py              # Organ risk metrics list and bullet layout
├── medication_panel.py         # Drug selection buttons and interactions
├── ai_prediction.py           # AI Health Engine analytics template and generator
├── requirements.txt            # Package dependencies
└── sample_clinical_*.csv       # Clinical sample patient data files
```

---

## Medical Disclaimer

**This software is for educational and research demonstration purposes only.** It is not a clinically validated medical tool and must not be used to diagnose, treat, or manage real-world medical cases. It has not been approved by any healthcare regulatory body.
