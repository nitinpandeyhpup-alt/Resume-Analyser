import json
import os
import tempfile

import streamlit as st

from backend import analyze_resume, read_resume


# Page configuration
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)


# Main heading
st.title("📄 AI Resume Analyzer")

st.subheader("Analyze your resume using Gemini AI")

st.write(
    "Upload your resume to get an ATS score, "
    "strengths, weaknesses and improvement suggestions."
)

st.divider()


# PDF uploader
uploaded_file = st.file_uploader(
    "Upload your Resume (PDF)",
    type=["pdf"]
)


# Analyze button
if uploaded_file is not None:

    st.success("Resume uploaded successfully!")

    if st.button("Analyze Resume", type="primary"):

        temp_path = None

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_pdf:

                temp_pdf.write(uploaded_file.getvalue())
                temp_path = temp_pdf.name

            with st.spinner("Analyzing your resume..."):

                resume_text = read_resume(temp_path)

                result = analyze_resume(resume_text)

            st.session_state["result"] = result

            st.success("Resume analysis completed!")

        except Exception as e:

            st.error(f"Error: {e}")

        finally:

            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


# Display results
if "result" in st.session_state:

    result = st.session_state["result"]

    st.divider()

    st.header("📊 Resume Analysis Results")

    score = result.get("ats_score", 0)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "ATS Score",
            f"{score}/100"
        )

        st.progress(score / 100)

    with col2:

        st.subheader("Summary")

        st.write(result.get("summary", ""))


    st.subheader("✅ Strengths")

    for item in result.get("strengths", []):
        st.write("•", item)


    st.subheader("❌ Weaknesses")

    for item in result.get("weaknesses", []):
        st.write("•", item)


    st.subheader("🧩 Missing Skills")

    for item in result.get("missing_skills", []):
        st.write("•", item)


    st.subheader("💡 Improvement Suggestions")

    for item in result.get("improvement_suggestions", []):
        st.write("•", item)


    st.subheader("✍️ Rewritten Bullet Points")

    for item in result.get("rewritten_bullet_points", []):

        with st.expander("View rewritten bullet point"):

            st.write("Original:")
            st.write(item.get("original", ""))

            st.write("Improved:")
            st.write(item.get("improved", ""))


    st.download_button(
        label="Download Analysis",
        data=json.dumps(result, indent=2),
        file_name="resume_analysis.json",
        mime="application/json"
    )
