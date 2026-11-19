import json
import os
import re
from typing import Any

import PyPDF2
from google import genai


MODEL_NAME = "gemini-3.5-flash-lite"


# 1. Read PDF Resume
def read_resume(file_path: str) -> str:

    extracted_pages = []

    with open(file_path, "rb") as pdf_file:

        reader = PyPDF2.PdfReader(pdf_file)

        for page_number, page in enumerate(reader.pages, start=1):

            page_text = page.extract_text() or ""

            if page_text.strip():
                extracted_pages.append(page_text)

    resume_text = "\n\n".join(extracted_pages).strip()

    if not resume_text:
        raise ValueError(
            "No readable text was found in this PDF. "
            "If it is a scanned resume, OCR is required."
        )

    return resume_text


# 2. Analyze Resume Using Gemini AI
def analyze_resume(resume_text: str) -> dict[str, Any]:

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add your Gemini API key "
            "to the environment variable before starting the app."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an ATS resume analyzer and career coach.

Analyze the resume below. Be specific, evidence-based, and constructive.
Do not invent experience, qualifications, or skills that are not present.

RESUME:
{resume_text}

Return a valid JSON object with exactly these keys:

{{
  "ats_score": 0,
  "summary": "A concise overall assessment",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "missing_skills": ["..."],
  "improvement_suggestions": ["..."],
  "rewritten_bullet_points": [
    {{
      "original": "Original resume bullet",
      "improved": "Suggested rewrite"
    }}
  ]
}}

Rules:
- ats_score must be an integer from 0 to 100.
- Keep every list as a JSON array, even if it is empty.
- Only suggest missing skills relevant to the target role.
- Do not claim a skill is missing if the resume demonstrates it.
- Rewritten bullets must preserve the truth of the original.
- Do not fabricate metrics.
- Output ONLY valid JSON.
- No Markdown fences or extra commentary.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        },
    )

    raw_response = (response.text or "").strip()

    if not raw_response:
        raise RuntimeError("Gemini returned an empty response.")

    # Remove accidental Markdown code fences
    raw_response = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw_response
    )

    raw_response = re.sub(
        r"\s*```$",
        "",
        raw_response
    )

    # Convert Gemini response into Python dictionary
    try:
        result = json.loads(raw_response)

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Gemini returned invalid JSON.\n"
            f"Raw response:\n{raw_response}"
        ) from exc

    # Validate ATS score
    score = result.get("ats_score")

    if not isinstance(score, int) or not 0 <= score <= 100:

        raise RuntimeError(
            "The analysis response did not contain a valid ATS score."
        )

    return result
