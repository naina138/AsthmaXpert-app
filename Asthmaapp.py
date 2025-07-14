import streamlit as st
import pandas as pd
import joblib
import os

# ✅ Must be FIRST Streamlit command
st.set_page_config(page_title="Asthma Risk Predictor", layout="wide")

# 🔹 Load external CSS
def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# 🔹 App Title
st.markdown("<h1 style='text-align: center;'>🫁 Asthma Risk Prediction Dashboard</h1>", unsafe_allow_html=True)

MODEL_PATH = "voting_hybrid_model.pkl"
RECORD_FILE = "asthma_patient_records.csv"

# ---- 🔹 Load Model ----
model = joblib.load(MODEL_PATH)
expected_features = model.feature_names_in_.tolist()

# ---- 🔹 Load Records ----
if os.path.exists(RECORD_FILE):
    st.session_state.patient_records = pd.read_csv(RECORD_FILE)
else:
    st.session_state.patient_records = pd.DataFrame()

# ---- 🔹 Sidebar Inputs ----
st.sidebar.header("🧑‍⚕️ Enter Patient Details")
patient_name = st.sidebar.text_input("Patient Name", "John Doe")
doctor_note = st.sidebar.text_area("📝 Doctor's Notes", placeholder="Write any observations or suggestions")

age = st.sidebar.slider("Age", 0, 100, 30)
bmi = st.sidebar.slider("BMI", 10.0, 50.0, 22.5)
physical = st.sidebar.slider("Physical Activity (0–10)", 0, 10, 5)
diet = st.sidebar.slider("Diet Quality (0–10)", 0, 10, 5)
sleep = st.sidebar.slider("Sleep Quality (0–10)", 0, 10, 6)
pollution = st.sidebar.slider("Pollution Exposure (0–10)", 0, 10, 5)
pollen = st.sidebar.slider("Pollen Exposure (0–10)", 0, 10, 5)
dust = st.sidebar.slider("Dust Exposure (0–10)", 0, 10, 5)
fev1 = st.sidebar.slider("Lung Function FEV1", 0.5, 5.0, 3.2)
fvc = st.sidebar.slider("Lung Function FVC", 0.5, 6.0, 4.0)
symptoms = st.sidebar.slider("Symptom Score (0–6)", 0, 6, 2)
smoking = st.sidebar.selectbox("Smoking Status", [0, 1])
pet_allergy = st.sidebar.selectbox("Pet Allergy", [0, 1])
family_history = st.sidebar.selectbox("Family History of Asthma", [0, 1])
history_allergy = st.sidebar.selectbox("History of Allergies", [0, 1])

fev1_fvc_ratio = round(fev1 / fvc, 3)

# ---- 🔹 Prepare Input ----
input_dict = {
    "Age": age,
    "BMI": bmi,
    "PhysicalActivity": physical,
    "DietQuality": diet,
    "SleepQuality": sleep,
    "PollutionExposure": pollution,
    "PollenExposure": pollen,
    "DustExposure": dust,
    "LungFunctionFEV1": fev1,
    "LungFunctionFVC": fvc,
    "FEV1_FVC_Ratio": fev1_fvc_ratio,
    "SymptomScore": symptoms,
    "Smoking": smoking,
    "PetAllergy": pet_allergy,
    "FamilyHistoryAsthma": family_history,
    "HistoryOfAllergies": history_allergy
}
input_data = pd.DataFrame([input_dict])

# Ensure columns match training
for col in expected_features:
    if col not in input_data.columns:
        input_data[col] = 0
input_data = input_data[expected_features]

# ---- 🔹 Predict ----
if st.button("🔍 Predict Asthma Risk"):
    prob = model.predict_proba(input_data)[0][1]
    prediction = model.predict(input_data)[0]
    risk_percent = round(prob * 100, 2)
    label = "Asthma Detected" if prediction == 1 else "No Asthma"

    # Risk level
    risk_level = "🟢 Low Risk" if risk_percent < 30 else "🟡 Medium Risk" if risk_percent < 70 else "🔴 High Risk"

    # Age group
    age_group = "👶 Child" if age < 13 else "🧑 Adult" if age < 60 else "👴 Senior"

    # Action
    if risk_percent >= 70:
        action = "🔔 Refer to pulmonologist urgently."
    elif risk_percent >= 40:
        action = "🩺 Suggest lung function test."
    else:
        action = "✅ No immediate action needed."

    # Top risk features
    risk_factors = [
        "PetAllergy", "PollenExposure", "DustExposure",
        "PollutionExposure", "Smoking", "SymptomScore",
        "HistoryOfAllergies", "FamilyHistoryAsthma"
    ]
    available_factors = [f for f in risk_factors if f in input_data.columns]
    input_risk_vals = input_data[available_factors].iloc[0]
    top_risks = input_risk_vals.sort_values(ascending=False).head(3).index.tolist()
    top_risk_str = ", ".join(top_risks)

    # ---- 🔹 Display Output ----
    st.header(f"📄 Result for: {patient_name}")
    st.subheader(f"🎯 Prediction: **{label}**")
    st.markdown(f"📈 **Risk Probability:** `{risk_percent}%`")
    st.markdown(f"📊 **Risk Level:** {risk_level}")
    st.markdown(f"🧓 **Age Group:** {age_group}")
    st.markdown(f"⚠️ **Top Risk Factors:** `{top_risk_str}`")
    st.markdown(f"📌 **Suggested Action:** {action}")
    if doctor_note.strip():
        st.markdown(f"📝 **Doctor's Note:** {doctor_note.strip()}")

    # ---- 🔹 Save Record with Doctor Note ----
    record = input_data.copy()
    record.insert(0, "PatientName", patient_name)
    record["Prediction"] = label
    record["RiskPercent"] = risk_percent
    record["RiskLevel"] = risk_level
    record["AgeGroup"] = age_group
    record["TopRisks"] = top_risk_str
    record["Action"] = action
    record["DoctorNote"] = doctor_note.strip()

    st.session_state.patient_records = pd.concat(
        [st.session_state.patient_records, record], ignore_index=True
    )
    st.session_state.patient_records.to_csv(RECORD_FILE, index=False)

# ---- 🔹 View Past Patients ----
if st.sidebar.checkbox("📁 Show All Patient Predictions"):
    st.subheader("📋 Patient History")
    if not st.session_state.patient_records.empty:
        st.dataframe(st.session_state.patient_records[[
            "PatientName", "Prediction", "RiskPercent", "RiskLevel",
            "AgeGroup", "TopRisks", "Action", "DoctorNote"
        ]])
    else:
        st.info("No records yet.")

# ---- 🔹 Export ----
if st.sidebar.button("⬇ Export to Excel"):
    st.session_state.patient_records.to_excel("asthma_predictions.xlsx", index=False)
    st.success("✅ Exported to asthma_predictions.xlsx")

# ---- 🔹 Clear Records ----
if st.sidebar.button("🗑 Clear All Records"):
    st.session_state.patient_records = pd.DataFrame()
    if os.path.exists(RECORD_FILE):
        os.remove(RECORD_FILE)
    st.success("🧹 All records cleared.")
