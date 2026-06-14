# AI Digital Twin — Human Body Disease Simulator

An interactive, high-fidelity PyQt6 desktop application simulating the physiological progression and treatment response of infectious diseases (Malaria, Dengue Fever, and Chikungunya). This platform features a contoured 3D humanoid body model with glowing holographic organs, a real-time vitals dashboard, clinical charts, and an AI Health Prediction Engine.
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
*   **Disease Simulator Mode**: Mathematical model simulating standard incubation, peak, and recovery curves for Malaria, Dengue Fever, and Chikungunya.
*   **AI Health Prediction Engine**: Generates a consolidated clinical summary detailing thermal control, organ defense metrics, recovery speeds, and side effects.
*   **Interactive Treatment Panel**: Apply targeted medications (e.g., Chloroquine for Malaria, Paracetamol/IV fluids for Dengue, NSAIDs/Corticosteroids for Chikungunya) and immediately visualize vital signs recovering.

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

## Project Structure

```
├── main.py                     # Main GUI layout, widgets, and window orchestration
├── disease_engine.py           # Core disease simulation profiles and mathematical equations
├── body_model.py               # 3D Matplotlib humanoid meshes and rendering parameters
├── dashboard.py                # Real-time vitals card display and warning calculations
├── charts.py                   # Matplotlib chart panels (Fever, Vitals, Organ Risk)
├── organ_panel.py              # Organ risk metrics list and bullet layout
├── medication_panel.py         # Drug selection buttons and interactions
├── ai_prediction.py           # AI Health Engine analytics template and generator
└── requirements.txt            # Package dependencies
```

---

## Medical Disclaimer

**This software is for educational and research demonstration purposes only.** It is not a clinically validated medical tool and must not be used to diagnose, treat, or manage real-world medical cases. It has not been approved by any healthcare regulatory body.
