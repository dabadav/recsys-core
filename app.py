import streamlit as st
from datetime import datetime, timedelta
from services.scoring import ProtocolScorer
from services.data_service import PatientRepository, ProtocolRepository
from utils.clinical_scores import ClinicalScoresAnalyzer
from typing import Callable, Dict, List, Optional, Any

# Initialize repositories
patient_repo = PatientRepository()
protocol_repo = ProtocolRepository()

if 'patients' not in st.session_state:
    st.session_state.patients = patient_repo.get_all_patient_ids()
if 'protocols' not in st.session_state:
    st.session_state.protocols = protocol_repo.get_all_protocols()
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None
if 'motor_weight' not in st.session_state:
    st.session_state.motor_weight = None
if 'cognitive_weight' not in st.session_state:
    st.session_state.cognitive_weight = None

from typing import List, Dict

def generate_weekly_plan(scored_protocols: List[Dict]) -> Dict[str, List[Dict]]:
    """Distribute protocols across the week, balancing motor and cognitive activities."""
    weekly_plan = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": []
    }

    # Separate motor and cognitive protocols
    motor_protocols = [p for p in scored_protocols if p["type"] == "motor"]
    cognitive_protocols = [p for p in scored_protocols if p["type"] == "cognitive"]

    # Assign 4 activities per day, alternating motor and cognitive focus
    for day in weekly_plan.keys():
        # Alternate focus between motor and cognitive days
        is_motor_day = list(weekly_plan.keys()).index(day) % 2 == 0

        # Add 4 activities per day
        while len(weekly_plan[day]) < 4:
            if is_motor_day and motor_protocols:
                weekly_plan[day].append(motor_protocols.pop(0))
            elif cognitive_protocols:
                weekly_plan[day].append(cognitive_protocols.pop(0))

            # If no more protocols of the preferred type, use the other type
            if is_motor_day and not motor_protocols and cognitive_protocols:
                weekly_plan[day].append(cognitive_protocols.pop(0))
            elif not cognitive_protocols and motor_protocols:
                weekly_plan[day].append(motor_protocols.pop(0))

            # Stop if no more protocols are available
            if not motor_protocols and not cognitive_protocols:
                break

    return weekly_plan

# def generate_weekly_plan(scored_protocols: List[Dict]) -> Dict[str, List[Dict]]:
#     """Distribute protocols across the week, balancing motor and cognitive activities."""
#     weekly_plan = {
#         "Monday": [],
#         "Tuesday": [],
#         "Wednesday": [],
#         "Thursday": [],
#         "Friday": [],
#         "Saturday": [],
#         "Sunday": []
#     }

#     # Separate motor and cognitive protocols
#     motor_protocols = [p for p in scored_protocols if p["type"] == "motor"]
#     cognitive_protocols = [p for p in scored_protocols if p["type"] == "cognitive"]

#     # Assign protocols to days
#     for i, day in enumerate(weekly_plan.keys()):
#         if i % 2 == 0:  # Motor-focused days (Monday, Wednesday, Friday, etc.)
#             if motor_protocols:
#                 weekly_plan[day].append(motor_protocols.pop(0))
#         else:  # Cognitive-focused days (Tuesday, Thursday, etc.)
#             if cognitive_protocols:
#                 weekly_plan[day].append(cognitive_protocols.pop(0))

#         # Add a second protocol if time allows
#         if sum(p["safety_constraints"]["max_duration"] for p in weekly_plan[day]) < 60:  # 60 mins/day
#             if i % 2 == 0 and motor_protocols:
#                 weekly_plan[day].append(motor_protocols.pop(0))
#             elif cognitive_protocols:
#                 weekly_plan[day].append(cognitive_protocols.pop(0))

#     return weekly_plan

def main():

    # Initialize repositories
    # patient_repo = PatientRepository()
    # protocol_repo = ProtocolRepository()

    # --- Sidebar ---
    st.session_state.selected_patient = st.sidebar.selectbox(
        "Select Patient",
        st.session_state.patients  # Instead of patients.keys()
    )

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigate",
        # ["Patient Management", "Protocol Recommendations", "Treatment Planning", "Analytics"]
        ["Patient Management", "Treatment Planning"]
    )

    if page == "Patient Management":
        patient_page()
    elif page == "Protocol Recommendations":
        pass
    elif page == "Treatment Planning":
        treatment_page()
    else:
        pass

def patient_page():

    if not st.session_state.selected_patient:
        st.warning("Please select a patient first.")
        return

    patient_id = st.session_state.selected_patient
    patient = patient_repo.get_patient(patient_id)

    # --- Main Content ---
    st.title(f"Patient: {patient_id}")

    # Patient Overview Columns
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Demographics")
        st.markdown(f"""
            - **Age**: {patient.demographics['age']}
            - **Gender**: {patient.demographics['gender'].capitalize()}
            - **Handedness**: {patient.demographics['handedness'].capitalize()}
            - **Days Post-Stroke**: {(datetime.now() - patient.stroke_info.onset_date).days}
        """)

    with col2:
        st.subheader("Recovery Profile")
        st.markdown(f"""
            - **Group**: {patient.recovery_profile.group}
            - **Expected Adherence**: {patient.recovery_profile.expected_adherence*100}%
            - **Motor Trajectory**: {patient.recovery_profile.motor_trajectory['slope']:.1f} pts/wk
        """)

    # In the patient profile section
    clinician_notes = st.text_area("Clinician Notes", value=patient.clinician_notes or "")

    # Display ARAT radar plot
    analyzer = ClinicalScoresAnalyzer()

    col1, col2 = st.columns(2)
    with col1:
        arat_fig = analyzer.create_arat_radar(patient.clinical_scores.ARAT)
        st.pyplot(arat_fig, use_container_width=True)

    with col2:
        # Display MoCA radar plot
        moca_fig = analyzer.create_moca_radar(patient.clinical_scores.MoCA)
        st.pyplot(moca_fig, use_container_width=True)

    tags = st.multiselect(
        "Tags",
        options=["mild_neglect", "low_motivation", "prefers_gamification", "high_risk"],
        default=patient.tags or []
    )

    # Update patient object
    patient.clinician_notes = clinician_notes
    patient.tags = tags

    # Motor/Cognitive Progress Chart
    st.subheader("Recovery Trajectory")
    tab1, tab2 = st.tabs(["Motor (ARAT)", "Cognitive (MoCA)"])
    with tab1:
        st.line_chart([12, 14, 15, 16], height=200)  # Mock ARAT progress
    with tab2:
        st.line_chart([22, 23, 23, 24], height=200)  # Mock MoCA progress

    # --- Recommendation Engine ---
    st.header("Treatment Recommendations")

    # Protocol Scoring Controls
    with st.expander("Scoring Parameters"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.session_state.motor_weight = st.slider("Motor Priority", 0.0, 1.0, 0.6)
        with col_b:
            st.session_state.cognitive_weight = st.slider("Cognitive Priority", 0.0, 1.0, 0.3)

def treatment_page():
    # Generate recommendations
    patient_id = st.session_state.selected_patient
    patient = patient_repo.get_patient(patient_id)
    protocols = st.session_state.protocols

    scorer = ProtocolScorer(patient, protocols)
    scored_protocols = scorer.score_all_protocols(st.session_state.motor_weight, st.session_state.cognitive_weight)
    weekly_plan = generate_weekly_plan(scored_protocols)

    # Display weekly plan
    st.subheader("Personalized Treatment Plan")
    for day, protocols in weekly_plan.items():
        with st.expander(f"{day}", expanded=(day != "Saturday" and day != "Sunday")):
            for protocol in protocols:
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"""
                    **{protocol['name']}**
                    (*{protocol['type'].capitalize()} Protocol*)

                    🔸 Target: {', '.join([k for k, v in protocol['body_targets'].items() if v])}
                    🔸 Difficulty: :muscle: {protocol['difficulty_motor'].capitalize()} :brain: {protocol['difficulty_cognitive'].capitalize()}

                    """)
                with cols[1]:
                    st.metric("Match Score", f"{protocol['score']:.1f}")
                    if st.button("Log Session", key=f"log_{day}_{protocol['protocol_id']}"):
                        handle_session_log(patient, protocol)

            # Session Logging Form
            with st.form(key=f"session_form_{day}"):
                st.write("Session Feedback")
                mood = st.slider("Patient Mood", 1, 5, key=f"mood_{day}")
                adherence = st.slider("Adherence %", 0, 100, key=f"adherence_{day}")
                if st.form_submit_button("Save Session Data"):
                    save_session_data(patient_id, day, mood, adherence)

    # --- Hidden Developer Section ---
    with st.expander("Developer Tools"):
        st.json(patient.dict())

def handle_session_log(patient, protocol):
    # Implementation for session logging
    st.success(f"Session logged for {protocol['name']}")

def save_session_data(patient_id, day, mood, adherence):
    # Implementation for saving session data
    st.toast(f"Session data saved for {day}")

if __name__ == "__main__":
    st.set_page_config(page_title="RecSYS Demo")
    main()