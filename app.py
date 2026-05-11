
# import os
# import sqlite3
# import json
# import base64
# from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
# from werkzeug.security import generate_password_hash, check_password_hash
# from datetime import datetime
# from PIL import Image
# from io import BytesIO
# import time
# import docx
# import pdfplumber
# import re
# import cv2
# import numpy as np
# from groq import Groq


# app = Flask(__name__)
# app.secret_key = 'your_super_secret_key_hr_portal_2025'
# DATABASE = 'hr_portal.db'
# UPLOAD_FOLDER = 'uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# # Resume scoring threshold
# RESUME_THRESHOLD = 60

# # Email configuration
# from flask_mail import Mail, Message

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'shahjhalak0412@gmail.com'
# app.config['MAIL_PASSWORD'] = 'uwiw nufh yhgq vzmn'
# app.config['MAIL_DEFAULT_SENDER'] = 'shahjhalak0412@gmail.com'

# mail = Mail(app)


# def send_test_link_email(candidate_email, candidate_name, job_title, test_link):
#     """Send test link email to a candidate"""
#     try:
#         print(f"📧 Attempting to send email to: {candidate_email}")
#         print(f"   Name: {candidate_name}")
#         print(f"   Job: {job_title}")
#         print(f"   Link: {test_link}")

#         msg = Message(
#             subject=f"🎯 Test Invitation: {job_title}",
#             recipients=[candidate_email]
#         )

#         msg.body = f"""
# Dear {candidate_name},

# Congratulations! Based on your resume screening, you have been selected for the next round - the online assessment for {job_title}.

# Your Test Link: {test_link}

# Important Instructions:
# ✅ Complete the test before the deadline
# ✅ Ensure stable internet connection
# ✅ Face verification will be required
# ✅ You cannot retake the test once submitted
# ✅ Find a quiet place with good lighting for face verification

# Best of luck!
# HR Team
#         """

#         msg.html = f"""
# <!DOCTYPE html>
# <html>
# <head>
#     <style>
#         body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
#         .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
#         .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
#         .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; }}
#         .button {{ display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
#         .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; text-align: center; }}
#     </style>
# </head>
# <body>
#     <div class="container">
#         <div class="header">
#             <h2>Test Invitation</h2>
#         </div>
#         <div class="content">
#             <p>Dear <strong>{candidate_name}</strong>,</p>
#             <p>Congratulations! Based on your resume screening, you have been selected for the next round - the online assessment for <strong>{job_title}</strong>.</p>
#             <p><strong>Your Test Link:</strong></p>
#             <p style="text-align: center;">
#                 <a href="{test_link}" class="button">Start Your Test</a>
#             </p>
#             <p><strong>Important Instructions:</strong></p>
#             <ul>
#                 <li>Complete the test before the deadline</li>
#                 <li>Ensure stable internet connection</li>
#                 <li>Face verification will be required</li>
#                 <li>You cannot retake the test once submitted</li>
#             </ul>
#             <p>Best of luck!</p>
#             <p><strong>HR Team</strong></p>
#         </div>
#         <div class="footer">
#             <p>This is an automated message. Please do not reply to this email.</p>
#         </div>
#     </div>
# </body>
# </html>
#         """

#         mail.send(msg)
#         print(f"✅ Email successfully sent to {candidate_name} at {candidate_email}")
#         return True

#     except Exception as e:
#         print(f"❌ Failed to send email to {candidate_email}: {str(e)}")
#         print(f"   Error type: {type(e).__name__}")
#         return False


# def get_db_connection():
#     """Get database connection with timeout and error handling"""
#     try:
#         conn = sqlite3.connect(DATABASE, timeout=10)
#         conn.row_factory = sqlite3.Row
#         conn.execute("PRAGMA journal_mode=WAL")
#         return conn
#     except sqlite3.Error as e:
#         print(f"Database connection error: {e}")
#         return None


# # Register Jinja filter for JSON loading in templates
# def json_load(value):
#     try:
#         return json.loads(value)
#     except (TypeError, json.JSONDecodeError):
#         return {}

# app.jinja_env.filters['from_json'] = json_load

# # Internal Admin credentials
# ADMIN_USERNAME = 'hr_admin'
# ADMIN_PASSWORD_HASH = generate_password_hash('admin123')


# # Groq Client
# GROQ_CLIENT = None
# try:
#     GROQ_API_KEY = os.getenv("GROQ_API_KEY")
#     if not GROQ_API_KEY:
#         print("WARNING: GROQ_API_KEY not found in environment variables.")
#     else:
#         GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)
#         print("Groq API Client loaded successfully.")
# except Exception as e:
#     print(f"Groq Client failed to load: {e}")


# # --- GENERAL UTILITY FUNCTIONS ---

# def send_message(candidate_id, job_id, subject, body):
#     conn = get_db_connection()
#     try:
#         conn.execute(
#             'INSERT INTO messages (candidate_id, job_id, subject, body) VALUES (?, ?, ?, ?)',
#             (candidate_id, job_id, subject, body)
#         )
#         conn.commit()
#     except Exception as e:
#         print(f"Error sending message: {e}")
#     finally:
#         conn.close()


# def log_proctor_event(candidate_id, job_id, event_type, details=""):
#     conn = get_db_connection()
#     try:
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (candidate_id, job_id, event_type, details)
#         )
#         conn.commit()
#     except Exception as e:
#         print(f"Error logging event: {e}")
#     finally:
#         conn.close()


# # --- GROQ RESUME SCORING & AUTH UTILITY FUNCTIONS ---

# def extract_text_from_resume(resume_path):
#     """Extracts text from PDF or DOCX file."""
#     if not resume_path or not os.path.exists(resume_path):
#         return None

#     file_extension = os.path.splitext(resume_path)[1].lower()
#     text = ""

#     try:
#         if file_extension == '.pdf':
#             with pdfplumber.open(resume_path) as pdf:
#                 for page in pdf.pages:
#                     text += page.extract_text() or ""
#         elif file_extension == '.docx':
#             doc = docx.Document(resume_path)
#             text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
#         return text
#     except Exception as e:
#         return None


# def score_resume(resume_text, job_requirements_text):
#     """Scores the resume against job requirements using Groq API (llama-3.3-70b-versatile)."""
#     if not GROQ_CLIENT:
#         return 0, "Groq API Client not initialised. Check GROQ_API_KEY environment variable."

#     if not resume_text or not job_requirements_text:
#         return 0, "Missing resume or job requirements."

#     try:
#         prompt = f"""You are an expert HR recruitment analyst. Your task is to objectively score a candidate's
# resume against the provided job requirements. The score must reflect skill relevance,
# experience level, and domain expertise. You MUST respond with a single JSON object and nothing else.

# --- JOB REQUIREMENTS ---
# {job_requirements_text}

# --- CANDIDATE RESUME TEXT ---
# {resume_text}

# Based solely on the provided text, generate a score between 0 and 100 and a detailed, neutral rationale.
# Respond ONLY with this exact JSON format (no markdown, no extra text):
# {{"score": <integer 0-100>, "rationale": "<string>"}}"""

#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are an expert HR resume scoring assistant. "
#                         "Always respond with valid JSON only — no markdown fences, no prose, no explanation."
#                     )
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.1,
#         )

#         response_text = completion.choices[0].message.content.strip()

#         # Strip markdown fences if present
#         if response_text.startswith("```"):
#             response_text = re.sub(r"^```[a-zA-Z]*\n?", "", response_text)
#             response_text = re.sub(r"\n?```$", "", response_text).strip()

#         result = json.loads(response_text)
#         score = max(0, min(100, int(result.get('score', 0))))
#         rationale = result.get('rationale', "Score generated by Groq AI.")
#         return score, rationale

#     except json.JSONDecodeError as e:
#         return 0, f"Groq returned invalid JSON for resume scoring: {e}"
#     except Exception as e:
#         return 0, f"Error calling Groq API for resume scoring: {e}"


# # FaceNet setup
# try:
#     from keras_facenet import FaceNet
#     _facenet_embedder = FaceNet()
#     _face_detector_proto = os.path.join("models", "deploy.prototxt")
#     _face_detector_model = os.path.join("models", "res10_300x300_ssd_iter_140000_fp16.caffemodel")
#     if os.path.exists(_face_detector_proto) and os.path.exists(_face_detector_model):
#         _face_net_cv = cv2.dnn.readNetFromCaffe(_face_detector_proto, _face_detector_model)
#         FACENET_READY = True
#         print("FaceNet + OpenCV face detector loaded successfully.")
#     else:
#         FACENET_READY = False
#         print("WARNING: Caffe face detector model files not found in ./models/. Face verification disabled.")
# except Exception as _e:
#     FACENET_READY = False
#     print(f"WARNING: FaceNet not available ({_e}). Face verification disabled.")


# def _cv2_extract_face(img_bgr, size=(160, 160)):
#     """Detect and crop the largest confident face from a BGR image."""
#     h, w = img_bgr.shape[:2]
#     blob = cv2.dnn.blobFromImage(
#         cv2.resize(img_bgr, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
#     )
#     _face_net_cv.setInput(blob)
#     detections = _face_net_cv.forward()
#     if detections.shape[2] == 0:
#         return None
#     i = int(np.argmax(detections[0, 0, :, 2]))
#     conf = float(detections[0, 0, i, 2])
#     if conf < 0.5:
#         return None
#     box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
#     x1, y1, x2, y2 = box.astype(int)
#     face_crop = img_bgr[max(0, y1):y2, max(0, x1):x2]
#     if face_crop.size == 0:
#         return None
#     face_rgb = cv2.cvtColor(cv2.resize(face_crop, size), cv2.COLOR_BGR2RGB)
#     return face_rgb


# def _facenet_embedding(face_rgb):
#     """Return an L2-normalised FaceNet embedding for a (160,160,3) RGB array."""
#     emb = _facenet_embedder.embeddings(
#         np.expand_dims(face_rgb.astype("float32"), axis=0)
#     )[0]
#     return emb / np.linalg.norm(emb)


# def generate_ai_test(domain, num_questions):
#     """Generate test questions using Groq AI"""
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized"

#     try:
#         prompt = f"""
# Generate {num_questions} multiple choice questions about {domain}.
# Each question must have 4 options with exactly one correct answer.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "radio",
#     "options": ["Option A", "Option B", "Option C", "Option D"],
#     "answer": "Option A",
#     "category": "technical"
#   }}
# ]
# """
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.3
#         )

#         response_text = completion.choices[0].message.content.strip()

#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)

#         questions = json.loads(response_text)
#         return questions, None

#     except Exception as e:
#         return None, str(e)


# def verify_faces(stored_image_path, live_image_data_uri):
#     """
#     Compare a stored profile photo against a live webcam capture.
#     Uses local FaceNet embeddings — no external API required.
#     Falls back to a permissive pass if FaceNet is not available.
#     """
#     if not FACENET_READY:
#         return True, "Face verification skipped (FaceNet not available)."

#     full_stored_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_image_path)
#     if not os.path.exists(full_stored_path):
#         return False, "Reference photo not found in profile."

#     try:
#         stored_bgr = cv2.imread(full_stored_path)
#         if stored_bgr is None:
#             return False, "Could not read stored profile photo."
#         stored_face = _cv2_extract_face(stored_bgr)
#         if stored_face is None:
#             return False, "No face detected in stored profile photo."

#         _, encoded = live_image_data_uri.split(',', 1)
#         live_bytes = base64.b64decode(encoded)
#         live_pil = Image.open(BytesIO(live_bytes)).convert('RGB')
#         live_bgr = cv2.cvtColor(np.array(live_pil), cv2.COLOR_RGB2BGR)
#         live_face = _cv2_extract_face(live_bgr)
#         if live_face is None:
#             return False, "No face detected in live camera image. Ensure good lighting and look directly at the camera."

#         stored_emb = _facenet_embedding(stored_face)
#         live_emb = _facenet_embedding(live_face)
#         distance = float(np.linalg.norm(stored_emb - live_emb))

#         THRESHOLD = 0.55
#         if distance < THRESHOLD:
#             return True, f"Verification successful (distance={distance:.3f})."
#         else:
#             return False, f"Face mismatch (distance={distance:.3f}). Try better lighting or re-upload your profile photo."

#     except Exception as e:
#         return False, f"Verification error: {e}"


# # --- GROQ: QUESTION GENERATION & TEST GRADING ---

# def generate_assessment_json(test_name, domain_text, num_questions, question_type):
#     """Generate test questions using Groq AI."""
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized. Please set the GROQ_API_KEY environment variable."

#     try:
#         if question_type == "audio":
#             type_instruction = (
#                 "Create scenario-based questions that require a verbal/written response. "
#                 "Set 'type' to 'audio_text' for every question. "
#                 "Set 'options' to an empty array []. "
#                 "The 'answer' field should contain a sample ideal response."
#             )
#         else:
#             type_instruction = (
#                 "Create multiple-choice questions (MCQ). "
#                 "Set 'type' to 'radio' for every question. "
#                 "Provide exactly 4 distinct strings in 'options'. "
#                 "The 'answer' field must exactly match one of the 4 options."
#             )

#         prompt = f"""You are an expert HR assessment creator.

# Generate a recruitment test with the details below and return ONLY a valid JSON array — no markdown, no explanation, no extra text.

# Test Name     : {test_name}
# Topic / Domain: {domain_text}
# Total Questions: {num_questions}
# Question Type : {question_type}

# Instructions:
# {type_instruction}

# Required JSON schema for every question object:
# {{
#   "q"      : "<question text>",
#   "type"   : "<radio | audio_text>",
#   "options": ["<opt1>", "<opt2>", "<opt3>", "<opt4>"],
#   "answer" : "<correct answer or ideal response>"
# }}

# Return a JSON array of exactly {num_questions} question objects."""

#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a professional HR assessment generator. "
#                         "Always respond with valid JSON only — no markdown fences, no prose."
#                     )
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.3,
#         )

#         response_text = completion.choices[0].message.content.strip()

#         if response_text.startswith("```"):
#             response_text = re.sub(r"^```[a-zA-Z]*\n?", "", response_text)
#             response_text = re.sub(r"\n?```$", "", response_text).strip()

#         questions = json.loads(response_text)

#         if not isinstance(questions, list):
#             return None, "Groq returned an unexpected format (expected a JSON array)."

#         return questions, None

#     except json.JSONDecodeError as e:
#         return None, f"Groq returned invalid JSON: {e}"
#     except Exception as e:
#         return None, f"AI Question Generation failed: {str(e)}"


# # def grade_test_ai(test, submitted_answers):
# #     """
# #     Hybrid grader:
# #     - MCQ (radio): exact string match locally.
# #     - Scenario (audio_text): scored by Groq AI.
# #     """
# #     try:
# #         questions = json.loads(test['questions_json'])
# #         print(f"Grading test with {len(questions)} questions")
# #         print(f"Submitted answers: {submitted_answers}")
# #     except Exception as e:
# #         print(f"Error parsing questions: {e}")
# #         return 0, f"Could not parse test questions: {e}"

# #     if not questions:
# #         return 0, "No questions found in test."

# #     def _norm(s):
# #         """Normalize answer strings for comparison: strip, lowercase, collapse whitespace."""
# #         return " ".join(str(s).strip().lower().split()) if s else ""

# #     # Build a lookup: normalized question text → question object
# #     # This allows matching submitted answers even if question order differs
# #     q_by_text = {_norm(q.get("q", "")): q for q in questions}

# #     # Check if the form submitted a q_map (display_index → questions_json_index)
# #     # e.g., q_map = "2,0,4,1,3" means display q_1 is questions[2], q_2 is questions[0], etc.
# #     raw_q_map = submitted_answers.get("q_map", "")
# #     if isinstance(raw_q_map, list):
# #         raw_q_map = raw_q_map[0] if raw_q_map else ""

# #     q_map = None
# #     if raw_q_map:
# #         try:
# #             q_map = [int(x) for x in str(raw_q_map).split(",")]
# #         except Exception:
# #             q_map = None

# #     # Also build a lookup: normalized question text submitted per form key (q_N_text)
# #     # so we can match back to the correct question if q_map is absent
# #     q_text_by_key = {}
# #     for key, val in submitted_answers.items():
# #         if key.endswith("_text") and key.startswith("q_"):
# #             raw = val[0] if isinstance(val, list) else val
# #             q_text_by_key[key.replace("_text", "")] = _norm(raw)

# #     total_q = len(questions)
# #     points_earned = 0.0
# #     rationale_parts = []
# #     correct_count = 0
# #     audio_text_qs = []

# #     for idx, q in enumerate(questions):
# #         form_key = f"q_{idx + 1}"
# #         print(f"Looking for key: {form_key} in submitted answers")

# #         # If q_map was submitted, use it to find which form key corresponds to this question
# #         if q_map and idx < len(q_map):
# #             # q_map[display_position] = questions_json_index
# #             # We need: for this question at questions_json_index=idx, which display position?
# #             display_pos = None
# #             for disp, json_idx in enumerate(q_map):
# #                 if json_idx == idx:
# #                     display_pos = disp + 1
# #                     break
# #             if display_pos is not None:
# #                 form_key = f"q_{display_pos}"

# #         raw_answer = submitted_answers.get(form_key, "")

# #         # Flask's dict(request.form) wraps values in lists; unwrap safely
# #         if isinstance(raw_answer, list):
# #             raw_answer = raw_answer[0] if raw_answer else ""

# #         # Normalize: strip whitespace, collapse internal spaces, lowercase
# #         # This prevents mismatches caused by extra spaces or apostrophe differences
# #         def _norm(s):
# #             return " ".join(str(s).strip().lower().split()) if s else ""

# #         candidate_ans = _norm(raw_answer)
# #         correct_ans = _norm(q.get("answer", ""))

# #         q_type = q.get("type", "radio")

# #         print(f"Q{idx+1}: Type={q_type}, Candidate='{candidate_ans}', Correct='{correct_ans}'")

# #         if q_type == "radio":
# #             if candidate_ans and candidate_ans == correct_ans:
# #                 points_earned += 1
# #                 correct_count += 1
# #                 rationale_parts.append(f"Q{idx+1}: Correct ✓")
# #                 print(f"  ✅ Correct match!")
# #             else:
# #                 if not candidate_ans:
# #                     rationale_parts.append(f"Q{idx+1}: No answer provided")
# #                     print(f"  ❌ No answer")
# #                 else:
# #                     rationale_parts.append(
# #                         f"Q{idx+1}: Wrong (answered '{candidate_ans}', correct '{correct_ans}')"
# #                     )
# #                     print(f"  ❌ Wrong answer")
# #         else:
# #             audio_text_qs.append((idx, q, candidate_ans))

# #     print(f"MCQ Results: {correct_count}/{len([q for q in questions if q.get('type')=='radio'])} correct")

# #     if audio_text_qs and GROQ_CLIENT:
# #         try:
# #             batch_items = "\n\n".join([
# #                 f"[Q{idx+1}]\nQuestion: {q['q']}\nIdeal answer: {q.get('answer','')}\nCandidate answer: {ans}"
# #                 for idx, q, ans in audio_text_qs
# #             ])

# #             prompt = f"""You are grading written scenario answers.
# # For each question below, award a score from 0 to 10 based on relevance and quality vs the ideal answer.
# # Return ONLY a JSON array with one object per question, in order:
# # [{{"q": 1, "score": <0-10>, "comment": "<one sentence>"}}, ...]

# # {batch_items}"""

# #             completion = GROQ_CLIENT.chat.completions.create(
# #                 model="llama-3.3-70b-versatile",
# #                 messages=[
# #                     {"role": "system", "content": "You are an exam evaluator. Reply with valid JSON only."},
# #                     {"role": "user", "content": prompt}
# #                 ],
# #                 temperature=0,
# #             )
# #             result_text = completion.choices[0].message.content.strip()
# #             if result_text.startswith("```"):
# #                 result_text = re.sub(r"^```[a-zA-Z]*\n?", "", result_text)
# #                 result_text = re.sub(r"\n?```$", "", result_text).strip()

# #             ai_scores = json.loads(result_text)

# #             for i, (idx, q, ans) in enumerate(audio_text_qs):
# #                 raw = ai_scores[i] if i < len(ai_scores) else {}
# #                 ai_pts = max(0, min(10, int(raw.get("score", 0))))
# #                 points_earned += ai_pts / 10.0
# #                 rationale_parts.append(
# #                     f"Q{idx+1} (scenario): {ai_pts}/10 — {raw.get('comment','')}"
# #                 )

# #         except Exception as e:
# #             print(f"Groq grading error: {e}")
# #             for idx, q, ans in audio_text_qs:
# #                 points_earned += 0.5
# #                 rationale_parts.append(f"Q{idx+1} (scenario): AI grading failed, partial credit awarded.")

# #     elif audio_text_qs:
# #         for idx, q, ans in audio_text_qs:
# #             points_earned += 0.5
# #             rationale_parts.append(f"Q{idx+1} (scenario): Groq unavailable, partial credit awarded.")

# #     final_score = round((points_earned / total_q) * 100)
# #     final_score = max(0, min(100, final_score))
# #     rationale = " | ".join(rationale_parts)

# #     print(f"Final score: {final_score}% ({points_earned}/{total_q} points)")

# #     return final_score, rationale



# def grade_test_ai(test, submitted_answers):
#     """
#     Hybrid grader:
#     - MCQ (radio): matched by question index embedded in the form key (q_<json_index>).
#     - Scenario (audio_text): scored by Groq AI.
#     """
#     try:
#         questions = json.loads(test['questions_json'])
#         print(f"Grading test with {len(questions)} questions")
#         print(f"Submitted answers: {submitted_answers}")
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         return 0, f"Could not parse test questions: {e}"

#     if not questions:
#         return 0, "No questions found in test."

#     def _norm(s):
#         return " ".join(str(s).strip().lower().split()) if s else ""

#     total_q = len(questions)
#     points_earned = 0.0
#     rationale_parts = []
#     correct_count = 0
#     audio_text_qs = []

#     for idx, q in enumerate(questions):
#         # Form key is now "q_<json_index>" — always maps 1:1 to questions array
#         form_key = f"q_{idx}"
#         raw_answer = submitted_answers.get(form_key, "")

#         if isinstance(raw_answer, list):
#             raw_answer = raw_answer[0] if raw_answer else ""

#         candidate_ans = _norm(raw_answer)
#         correct_ans = _norm(q.get("answer", ""))
#         q_type = q.get("type", "radio")

#         print(f"Q{idx}: Type={q_type}, Candidate='{candidate_ans}', Correct='{correct_ans}'")

#         if q_type == "radio":
#             if candidate_ans and candidate_ans == correct_ans:
#                 points_earned += 1
#                 correct_count += 1
#                 rationale_parts.append(f"Q{idx+1}: Correct ✓")
#             else:
#                 if not candidate_ans:
#                     rationale_parts.append(f"Q{idx+1}: No answer provided")
#                 else:
#                     rationale_parts.append(
#                         f"Q{idx+1}: Wrong (answered '{candidate_ans}', correct '{correct_ans}')"
#                     )
#         else:
#             audio_text_qs.append((idx, q, candidate_ans))

#     print(f"MCQ Results: {correct_count}/{len([q for q in questions if q.get('type')=='radio'])} correct")

#     if audio_text_qs and GROQ_CLIENT:
#         try:
#             batch_items = "\n\n".join([
#                 f"[Q{idx+1}]\nQuestion: {q['q']}\nIdeal answer: {q.get('answer','')}\nCandidate answer: {ans}"
#                 for idx, q, ans in audio_text_qs
#             ])
#             prompt = f"""You are grading written scenario answers.
# For each question below, award a score from 0 to 10 based on relevance and quality vs the ideal answer.
# Return ONLY a JSON array with one object per question, in order:
# [{{"q": 1, "score": <0-10>, "comment": "<one sentence>"}}, ...]

# {batch_items}"""
#             completion = GROQ_CLIENT.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=[
#                     {"role": "system", "content": "You are an exam evaluator. Reply with valid JSON only."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0,
#             )
#             result_text = completion.choices[0].message.content.strip()
#             if result_text.startswith("```"):
#                 result_text = re.sub(r"^```[a-zA-Z]*\n?", "", result_text)
#                 result_text = re.sub(r"\n?```$", "", result_text).strip()

#             ai_scores = json.loads(result_text)
#             for i, (idx, q, ans) in enumerate(audio_text_qs):
#                 raw = ai_scores[i] if i < len(ai_scores) else {}
#                 ai_pts = max(0, min(10, int(raw.get("score", 0))))
#                 points_earned += ai_pts / 10.0
#                 rationale_parts.append(
#                     f"Q{idx+1} (scenario): {ai_pts}/10 — {raw.get('comment','')}"
#                 )
#         except Exception as e:
#             print(f"Groq grading error: {e}")
#             for idx, q, ans in audio_text_qs:
#                 points_earned += 0.5
#                 rationale_parts.append(f"Q{idx+1} (scenario): AI grading failed, partial credit awarded.")
#     elif audio_text_qs:
#         for idx, q, ans in audio_text_qs:
#             points_earned += 0.5
#             rationale_parts.append(f"Q{idx+1} (scenario): Groq unavailable, partial credit awarded.")

#     final_score = round((points_earned / total_q) * 100)
#     final_score = max(0, min(100, final_score))
#     rationale = " | ".join(rationale_parts)
#     print(f"Final score: {final_score}% ({points_earned}/{total_q} points)")
#     return final_score, rationale




# # --- AUTHENTICATION & GLOBAL ROUTES ---

# @app.route('/')
# def index():
#     return render_template('index.html')


# @app.route('/logout')
# def logout():
#     session.clear()
#     flash("You have been logged out successfully.", 'info')
#     return redirect(url_for('index'))


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# # --- CANDIDATE ROUTES ---

# @app.route('/signup', methods=('GET', 'POST'))
# def candidate_signup():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email']
#         password = request.form['password']

#         if not all([name, email, password]):
#             flash("Missing required fields (Name, Email, Password).", 'error')
#             return redirect(url_for('candidate_signup'))

#         conn = get_db_connection()
#         try:
#             conn.execute(
#                 'INSERT INTO candidates (name, email, password_hash) VALUES (?, ?, ?)',
#                 (name, email, generate_password_hash(password))
#             )
#             conn.commit()
#             flash("Account created! Log in and complete your profile before applying.", 'success')
#             return redirect(url_for('candidate_login'))
#         except sqlite3.IntegrityError:
#             flash("Email already registered.", 'error')
#             return redirect(url_for('candidate_signup'))
#         finally:
#             conn.close()

#     return render_template('candidate_signup.html')


# @app.route('/login', methods=('GET', 'POST'))
# def candidate_login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']

#         conn = get_db_connection()
#         user = conn.execute('SELECT * FROM candidates WHERE email = ?', (email,)).fetchone()
#         conn.close()

#         if user and check_password_hash(user['password_hash'], password):
#             session['user_id'] = user['id']
#             session['user_type'] = 'candidate'
#             flash(f"Welcome back, {user['name']}!", 'success')
#             return redirect(url_for('candidate_jobs'))
#         else:
#             flash("Invalid email or password.", 'error')
#             return render_template('candidate_login.html')

#     return render_template('candidate_login.html')


# @app.route('/candidate/profile', methods=('GET', 'POST'))
# def candidate_profile():
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to manage your profile.", 'warning')
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()
#     candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

#     if request.method == 'POST':
#         name = request.form['name']
#         dob = request.form['dob']
#         phone = request.form['phone']
#         address = request.form['address']
#         profile_image_data = request.form.get('profile_image_data')

#         resume_path = candidate['resume_path']
#         resume_file = request.files.get('resume')
#         db_resume_path = resume_path
#         db_image_path = candidate['profile_image_path']

#         if resume_file and resume_file.filename != '':
#             if resume_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], resume_path)):
#                 os.remove(os.path.join(app.config['UPLOAD_FOLDER'], resume_path))
#             filename = f"resume_{candidate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume_file.filename}"
#             resume_path_full = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             resume_file.save(resume_path_full)
#             db_resume_path = filename

#         if profile_image_data:
#             if db_image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], db_image_path)):
#                 os.remove(os.path.join(app.config['UPLOAD_FOLDER'], db_image_path))

#             header, encoded = profile_image_data.split(',', 1)
#             image_bytes = base64.b64decode(encoded)
#             img = Image.open(BytesIO(image_bytes))

#             image_filename = f"face_{candidate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
#             image_path_full = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
#             img.save(image_path_full, 'jpeg')
#             db_image_path = image_filename

#         try:
#             conn.execute(
#                 '''UPDATE candidates SET name=?, dob=?, phone=?, address=?, resume_path=?, profile_image_path=? WHERE id=?''',
#                 (name, dob, phone, address, db_resume_path, db_image_path, candidate_id)
#             )
#             conn.commit()
#             flash("Profile updated successfully!", 'success')
#             candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
#         except Exception as e:
#             flash(f"Error updating profile: {e}", 'error')
#         finally:
#             conn.close()

#     return render_template('candidate_profile.html', candidate=candidate)


# @app.route('/candidate/messages')
# def candidate_messages():
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     messages = conn.execute('''
#         SELECT 
#             m.*, j.title AS job_title 
#         FROM messages m 
#         LEFT JOIN jobs j ON m.job_id = j.id
#         WHERE m.candidate_id = ? 
#         ORDER BY m.created_at DESC
#     ''', (candidate_id,)).fetchall()

#     conn.execute('UPDATE messages SET is_read = 1 WHERE candidate_id = ? AND is_read = 0', (candidate_id,))
#     conn.commit()
#     conn.close()

#     return render_template('candidate_messages.html', messages=messages)


# @app.route('/candidate/jobs')
# def candidate_jobs():
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to view job postings.", 'warning')
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     candidate = conn.execute('SELECT resume_path, phone, address FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

#     can_apply = all([
#         candidate,
#         candidate['resume_path'],
#         candidate['phone'],
#         candidate['address']
#     ])

#     if not can_apply:
#         flash("Warning: You must complete all profile details (including resume, phone, and address) to apply.", 'warning')

#     jobs = conn.execute('''
#         SELECT j.*, a.status,
#                t.questions_json AS test_questions_json
#         FROM jobs j 
#         LEFT JOIN applications a 
#             ON j.id = a.job_id AND a.candidate_id = ?
#         LEFT JOIN tests t
#             ON j.id = t.job_id
#         WHERE j.deadline >= date('now') 
#         ORDER BY j.posted_date DESC
#     ''', (candidate_id,)).fetchall()

#     jobs_list = []
#     for job in jobs:
#         job_dict = dict(job)
#         is_softskills = False
#         try:
#             qs = json.loads(job_dict.get('test_questions_json') or '[]')
#             if qs and all(q.get('type') == 'audio_text' for q in qs):
#                 is_softskills = True
#         except Exception:
#             pass
#         job_dict['is_softskills'] = is_softskills
#         jobs_list.append(job_dict)

#     conn.close()

#     return render_template('candidate_jobs.html',
#                            jobs=jobs_list,
#                            can_apply=can_apply)


# @app.route('/candidate/apply/<int:job_id>')
# def candidate_apply(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()
#     candidate = conn.execute('SELECT resume_path, phone, address FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

#     if not all([candidate['resume_path'], candidate['phone'], candidate['address']]):
#         flash("Application failed: Please complete all profile details before applying.", 'error')
#         conn.close()
#         return redirect(url_for('candidate_jobs'))

#     try:
#         conn.execute(
#             'INSERT INTO applications (job_id, candidate_id, status) VALUES (?, ?, ?)',
#             (job_id, candidate_id, 'Applied')
#         )
#         conn.commit()
#         flash("Application submitted successfully!", 'success')
#     except sqlite3.IntegrityError:
#         flash("You have already applied for this job.", 'info')
#     except Exception as e:
#         flash(f"An error occurred during application: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))


# # --- CANDIDATE TESTING/AUTH ROUTES ---

# @app.route('/candidate/test/auth/<int:job_id>')
# def candidate_auth_start(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()
#     candidate = conn.execute('SELECT profile_image_path FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
#     test = conn.execute('SELECT title, questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     application = conn.execute('SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?', (job_id, candidate_id)).fetchone()
#     conn.close()

#     if not test or application['status'] != 'Selected for Test':
#         flash("You are not authorized for this test.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     if not candidate['profile_image_path']:
#         flash("Profile image required for authentication. Please update your profile.", 'warning')
#         return redirect(url_for('candidate_profile'))

#     is_softskills = False
#     try:
#         title_lower = (test['title'] or '').lower()
#         questions = json.loads(test['questions_json'] or '[]')
#         if 'soft skill' in title_lower or 'soft skills' in title_lower:
#             is_softskills = True
#         elif questions and all(q.get('type') == 'audio_text' for q in questions):
#             is_softskills = True
#     except Exception:
#         pass

#     session[f'test_type_{job_id}'] = 'softskills' if is_softskills else 'standard'

#     return render_template('candidate_auth_start.html', job_id=job_id, job_title=test['title'])


# @app.route('/candidate/test/verify/<int:job_id>', methods=['POST'])
# def candidate_test_verify(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

#     candidate_id = session['user_id']
#     live_image_data_uri = request.json.get('image')

#     conn = get_db_connection()
#     candidate = conn.execute('SELECT profile_image_path FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
#     conn.close()

#     stored_path = candidate['profile_image_path']

#     if not stored_path or not live_image_data_uri:
#         log_proctor_event(candidate_id, job_id, 'Face Auth Failed', 'Missing image data.')
#         return jsonify({'success': False, 'message': 'Authentication failed: Missing image data.'}), 400

#     is_verified, message = verify_faces(stored_path, live_image_data_uri)

#     if is_verified:
#         log_proctor_event(candidate_id, job_id, 'Face Auth Success', message)

#         conn2 = get_db_connection()
#         test_row = conn2.execute('SELECT title, questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#         conn2.close()

#         is_softskills = False
#         if test_row:
#             try:
#                 title_lower = (test_row['title'] or '').lower()
#                 qs = json.loads(test_row['questions_json'] or '[]')
#                 if 'soft skill' in title_lower:
#                     is_softskills = True
#                 elif qs and all(q.get('type') == 'audio_text' for q in qs):
#                     is_softskills = True
#             except Exception:
#                 pass

#         if is_softskills:
#             redirect_url = url_for('softskills.candidate_softskills_view', job_id=job_id)
#         else:
#             redirect_url = url_for('candidate_view_test', job_id=job_id)

#         return jsonify({'success': True, 'message': 'Verification successful.', 'redirect': redirect_url})
#     else:
#         log_proctor_event(candidate_id, job_id, 'Face Auth Failed', message)
#         return jsonify({'success': False, 'message': f'Verification failed. {message}'}), 401


# @app.route('/candidate/test/<int:job_id>')
# def candidate_view_test(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     # Check if test already submitted
#     existing_result = conn.execute(
#         'SELECT * FROM test_results WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()

#     if existing_result:
#         conn.close()
#         flash("You have already completed this test.", 'info')
#         return redirect(url_for('candidate_jobs'))

#     # Get test details
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     application = conn.execute('SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?',
#                                (job_id, candidate_id)).fetchone()
#     conn.close()

#     # Validate test access
#     if not test:
#         flash("Test not found. Please contact the administrator.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     if not application or application['status'] != 'Selected for Test':
#         flash("You are not authorized to take this test.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     # Parse questions with better error handling
#     questions = []
#     try:
#         if test['questions_json']:
#             # Clean up any potential markdown formatting
#             questions_json_str = test['questions_json'].strip()
            
#             # Remove markdown code blocks if present
#             if questions_json_str.startswith('```'):
#                 questions_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', questions_json_str)
#                 questions_json_str = re.sub(r'\n?```$', '', questions_json_str)
            
#             questions = json.loads(questions_json_str)
            
#             # Validate questions structure
#             if not isinstance(questions, list):
#                 print(f"❌ Questions is not a list, got: {type(questions)}")
#                 questions = []
#             elif len(questions) == 0:
#                 print("❌ Questions list is empty")
#                 flash("No questions found in the test. Please contact administrator.", 'error')
#                 return redirect(url_for('candidate_jobs'))
#             else:
#                 print(f"✅ Successfully loaded {len(questions)} questions")
#                 print(f"First question: {questions[0].get('q', 'No question text')[:100]}")
#         else:
#             print("❌ No questions_json found in test")
#             flash("Test questions are missing. Please contact administrator.", 'error')
#             return redirect(url_for('candidate_jobs'))
            
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON decode error: {e}")
#         print(f"Raw JSON: {test['questions_json'][:200] if test['questions_json'] else 'None'}")
#         flash("Error loading test questions. The test format is invalid. Please contact administrator.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     except Exception as e:
#         print(f"❌ Unexpected error parsing questions: {e}")
#         flash("Error loading test questions. Please contact administrator.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     # Handle start time - ensure it's valid
#     can_start = True
#     time_status = ""
#     try:
#         if test['start_time']:
#             start_time = datetime.strptime(test['start_time'], '%Y-%m-%d %H:%M:%S')
#             current_time = datetime.now()
            
#             if current_time < start_time:
#                 time_status = f"Test opens on {start_time.strftime('%B %d, %Y at %I:%M %p')}"
#                 can_start = False
#             else:
#                 time_status = f"Test duration: {test['duration_minutes']} minutes. Best of luck!"
#                 can_start = True
#         else:
#             time_status = f"Test duration: {test['duration_minutes']} minutes. You can start now!"
#             can_start = True
#     except (ValueError, TypeError) as e:
#         print(f"⚠️ Error parsing start_time: {e}, allowing test to start")
#         time_status = f"Test duration: {test['duration_minutes']} minutes."
#         can_start = True

#     # Debug information
#     print(f"=== Test Debug Info ===")
#     print(f"Job ID: {job_id}")
#     print(f"Test Title: {test['title']}")
#     print(f"Duration: {test['duration_minutes']} minutes")
#     print(f"Start Time: {test['start_time']}")
#     print(f"Number of Questions: {len(questions)}")
#     print(f"Can Start: {can_start}")
#     print(f"======================")

#     return render_template('candidate_view_test.html',
#                            test=test,
#                            questions=questions,
#                            time_status=time_status,
#                            can_start=can_start,
#                            job_id=job_id,
#                            questions_json=json.dumps(questions))  # Pass JSON string to template

# @app.route('/admin/test_email_config')
# def test_email_config():
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     try:
#         msg = Message(
#             subject="Test Email from HR Portal",
#             recipients=['shahjhalak0412@gmail.com'],
#             body="This is a test email to verify SMTP configuration is working."
#         )
#         mail.send(msg)
#         return "✅ Test email sent successfully! Check your inbox."
#     except Exception as e:
#         return f"❌ Email failed: {str(e)}"



# # ─────────────────────────────────────────────────────────────────────────────
# # PATCH for app.py  →  replace your existing candidate_submit_test route
# # with the version below.
# #
# # The key fix: when ANY submitted answer is a base64 data URI (audio recording),
# # we route the whole submission through the softskills pipeline so the audio
# # gets saved to disk and the admin can play it back later.
# # ─────────────────────────────────────────────────────────────────────────────


# # Abhi aj ka OG jo chlra 4-4-2026 ka 
# @app.route('/candidate/submit_test/<int:job_id>', methods=['POST'])
# def candidate_submit_test(job_id):
#     if session.get('user_type') != 'candidate' or request.method != 'POST':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     print(f"=== SUBMIT TEST CALLED for job_id: {job_id} ===")

#     conn = get_db_connection()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if not test:
#         conn.close()
#         flash("Test configuration not found.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     # Check duplicate submission
#     existing_result = conn.execute(
#         'SELECT id FROM test_results WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
#     if existing_result:
#         conn.close()
#         flash("You have already submitted this test.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     submitted_answers = dict(request.form)

#     # ── Detect if any answer contains a base64 audio recording ──────────────
#     has_audio_answers = any(
#         str(v[0] if isinstance(v, list) else v).startswith('data:')
#         for v in submitted_answers.values()
#     )

#     if has_audio_answers:
#         # Route through softskills pipeline to save audio files properly
#         conn.close()
#         print("  → Detected audio answers, routing to softskills submission")

#         # Build a proper answer_N / audio_N mapping expected by softskills submit
#         import re as _re
#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)

#         # Fetch questions so we can store question_text
#         questions = []
#         try:
#             questions = json.loads(test['questions_json'] or '[]')
#         except Exception:
#             pass

#         conn2 = get_db_connection()
#         try:
#             # Guard: check softskills_responses too
#             existing_ss = conn2.execute(
#                 'SELECT id FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#                 (candidate_id, job_id)
#             ).fetchone()
#             if existing_ss:
#                 flash("You have already submitted this interview.", 'info')
#                 return redirect(url_for('candidate_jobs'))

#             saved = 0
#             for key, val in submitted_answers.items():
#                 m = _re.match(r'^q_(\d+)$', key)
#                 if not m:
#                     continue
#                 question_num = int(m.group(1))
#                 raw_val = val[0] if isinstance(val, list) else val

#                 audio_path_db = None
#                 answer_text = ''

#                 if raw_val and raw_val.startswith('data:'):
#                     try:
#                         _, encoded = raw_val.split(',', 1)
#                         audio_bytes = base64.b64decode(encoded)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(audio_bytes)
#                         audio_path_db = filename
#                         saved += 1
#                         print(f"  ✅ Saved audio Q{question_num}: {filename} ({len(audio_bytes)} bytes)")
#                     except Exception as e:
#                         print(f"  ⚠️ Audio decode failed Q{question_num}: {e}")
#                         answer_text = raw_val
#                 else:
#                     answer_text = raw_val

#                 # Also grab optional typed text (q_N_text)
#                 text_fallback = submitted_answers.get(f'q_{question_num}_text', '')
#                 if isinstance(text_fallback, list):
#                     text_fallback = text_fallback[0]
#                 if text_fallback and not answer_text:
#                     answer_text = text_fallback

#                 q_text = ''
#                 if question_num <= len(questions):
#                     q_text = questions[question_num - 1].get('q', '')

#                 conn2.execute('''
#                     INSERT INTO softskills_responses
#                     (candidate_id, job_id, question_number, question_text, audio_path, answer_text)
#                     VALUES (?, ?, ?, ?, ?, ?)
#                 ''', (candidate_id, job_id, question_num, q_text, audio_path_db, answer_text))

#             conn2.execute(
#                 "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#                 (candidate_id, job_id)
#             )
#             conn2.execute('''
#                 INSERT OR REPLACE INTO test_results
#                 (candidate_id, job_id, score, submitted_answers_json)
#                 VALUES (?, ?, ?, ?)
#             ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills audio interview completed'})))
#             conn2.commit()

#             log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Audio interview, {saved} files saved")
#             flash(f"Interview submitted successfully! Your {saved} audio recording(s) have been saved.", 'success')

#         except Exception as e:
#             print(f"❌ Error saving audio answers: {e}")
#             import traceback; traceback.print_exc()
#             flash(f"Error saving your answers: {e}", 'error')
#         finally:
#             conn2.close()

#         return redirect(url_for('candidate_jobs'))

#     # ── Standard MCQ / text test grading ────────────────────────────────────
#     # score, rationale = grade_test_ai(test, submitted_answers)
#     # log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Score: {score}")

#     # try:
#     #     conn.execute(
#     #         '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json) VALUES (?, ?, ?, ?)''',
#     #         (candidate_id, job_id, score, json.dumps(submitted_answers))
#     #     )
#     #     conn.execute(
#     #         "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#     #         (candidate_id, job_id)
#     #     )
#     #     conn.commit()
#     #     flash(f"Test submitted successfully! Final Score: {score}. Rationale: {rationale}", 'success')
#     # except Exception as e:
#     #     flash(f"Error saving test results: {e}", 'error')
#     # finally:
#     #     conn.close()

#     # return redirect(url_for('candidate_jobs'))


   
#     # ───────────── MCQ GRADING (FINAL FIXED) ─────────────
#     print("=== QUESTIONS JSON FROM DB ===")
#     print(test['questions_json'])   # 🔥 DEBUG

#     questions = []
#     try:
#         questions = json.loads(test['questions_json'] or '[]')
#     except Exception as e:
#         print("Error loading questions:", e)

#     def normalize(text):
#         return str(text).strip().lower().replace(".", "").replace("'", "")

#     score = 0
#     total_questions = len(questions)

#     print(f"Grading test with {total_questions} questions")
#     print("Submitted answers:", submitted_answers)

#     for idx, q in enumerate(questions, start=1):
#         key = f"q_{idx}"

#         candidate_answer = submitted_answers.get(key, "")
#         if isinstance(candidate_answer, list):
#             candidate_answer = candidate_answer[0]

#         candidate_answer = normalize(candidate_answer)
#         correct_answer = normalize(q.get('answer', ''))

#         options = q.get('options', [])

#         # Handle A/B/C/D answers
#         if candidate_answer in ['a', 'b', 'c', 'd'] and options:
#             option_index = ord(candidate_answer) - ord('a')
#             if option_index < len(options):
#                 candidate_answer = normalize(options[option_index])

#         print(f"Q{idx}: Candidate='{candidate_answer}' | Correct='{correct_answer}'")

#         if candidate_answer == correct_answer:
#             score += 1
#             print("  ✅ Correct")
#         else:
#             print("  ❌ Wrong")

#     score_percent = (score / total_questions) * 100 if total_questions > 0 else 0
#     score_percent = round(score_percent, 2)

#     print(f"Final Score: {score_percent}%")

#     # Save result
#     try:
#         conn.execute(
#             '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json)
#                VALUES (?, ?, ?, ?)''',
#             (candidate_id, job_id, score_percent, json.dumps(submitted_answers))
#         )

#         conn.execute(
#             "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#             (candidate_id, job_id)
#         )

#         conn.commit()
#         flash(f"Test submitted successfully! Score: {score_percent}%", 'success')

#     except Exception as e:
#         flash(f"Error saving test results: {e}", 'error')

#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))

# # @app.route('/candidate/submit_test/<int:job_id>', methods=['POST'])
# # def candidate_submit_test(job_id):
# #     if session.get('user_type') != 'candidate' or request.method != 'POST':
# #         return redirect(url_for('candidate_login'))

# #     candidate_id = session['user_id']
# #     print(f"=== SUBMIT TEST CALLED for job_id: {job_id} ===")

# #     print("Form data received:")
# #     for key, value in request.form.items():
# #         print(f"  {key}: {value}")

# #     conn = get_db_connection()
# #     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

# #     if not test:
# #         conn.close()
# #         flash("Test configuration not found.", 'error')
# #         return redirect(url_for('candidate_jobs'))

# #     submitted_answers = dict(request.form)

# #     existing_result = conn.execute('SELECT id FROM test_results WHERE candidate_id = ? AND job_id = ?', (candidate_id, job_id)).fetchone()
# #     if existing_result:
# #         conn.close()
# #         flash("You have already submitted this test.", 'error')
# #         return redirect(url_for('candidate_jobs'))

# #     score, rationale = grade_test_ai(test, submitted_answers)
# #     log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Score: {score}")

# #     try:
# #         conn.execute(
# #             '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json) VALUES (?, ?, ?, ?)''',
# #             (candidate_id, job_id, score, json.dumps(submitted_answers))
# #         )
# #         conn.execute("UPDATE applications SET status = ? WHERE candidate_id = ? AND job_id = ?", ('Test Completed', candidate_id, job_id))
# #         conn.commit()
# #         flash(f"Test submitted successfully! Final Score: {score}. Rationale: {rationale}", 'success')
# #     except Exception as e:
# #         flash(f"Error saving test results: {e}", 'error')
# #     finally:
# #         conn.close()

# #     return redirect(url_for('candidate_jobs'))


# # --- ADMIN ROUTES ---

# @app.route('/admin/login', methods=('GET', 'POST'))
# def admin_login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
#             session['user_id'] = 'admin'
#             session['user_type'] = 'admin'
#             flash("Admin logged in successfully.", 'success')
#             return redirect(url_for('admin_dashboard'))
#         else:
#             flash("Invalid Admin Credentials.", 'error')
#             return render_template('admin_login.html')

#     return render_template('admin_login.html')


# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     jobs = conn.execute('SELECT * FROM jobs ORDER BY posted_date DESC').fetchall()

#     jobs_with_counts = []
#     for job in jobs:
#         count = conn.execute(
#             'SELECT COUNT(*) FROM applications WHERE job_id = ?',
#             (job['id'],)
#         ).fetchone()[0]

#         job_dict = dict(job)
#         job_dict['applicant_count'] = count
#         jobs_with_counts.append(job_dict)

#     conn.close()
#     return render_template('admin_dashboard.html', jobs=jobs_with_counts,
#                            now=datetime.now().strftime('%Y-%m-%d'))


# @app.route('/admin/create_job', methods=('GET', 'POST'))
# def admin_create_job():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#         requirements = request.form['requirements']
#         deadline = request.form['deadline']

#         if not all([title, description, deadline]):
#             flash("Missing job title, description, or deadline.", 'error')
#             return render_template('admin_create_job.html')

#         conn = get_db_connection()
#         try:
#             conn.execute(
#                 'INSERT INTO jobs (title, description, requirements, deadline) VALUES (?, ?, ?, ?)',
#                 (title, description, requirements, deadline)
#             )
#             conn.commit()
#             flash(f"Job '{title}' posted successfully!", 'success')
#             return redirect(url_for('admin_dashboard'))
#         except Exception as e:
#             flash(f"Database error while creating job: {e}", 'error')
#             return render_template('admin_create_job.html')
#         finally:
#             conn.close()

#     return render_template('admin_create_job.html')


# @app.route('/admin/view_applicants/<int:job_id>')
# def admin_view_applicants(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = None
#     try:
#         conn = get_db_connection()
#         if not conn:
#             flash("Database connection error", 'error')
#             return redirect(url_for('admin_dashboard'))

#         job = conn.execute('SELECT title, requirements FROM jobs WHERE id = ?', (job_id,)).fetchone()
#         if not job:
#             conn.close()
#             flash("Job not found.", 'error')
#             return redirect(url_for('admin_dashboard'))

#         job_title = job['title']
#         job_requirements = job['requirements'] or ""

#         applicants = conn.execute('''
#             SELECT 
#                 c.id AS candidate_id, c.name, c.email, c.phone, c.address,
#                 c.resume_path, c.profile_image_path,
#                 a.applied_date, a.status,
#                 r.score AS test_score
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             LEFT JOIN test_results r ON a.candidate_id = r.candidate_id AND a.job_id = r.job_id
#             WHERE a.job_id = ?
#             ORDER BY a.applied_date DESC
#         ''', (job_id,)).fetchall()

#         scored_applicants = []

#         for applicant_row in applicants:
#             applicant = dict(applicant_row)

#             if applicant['resume_path']:
#                 full_resume_path = os.path.join(app.config['UPLOAD_FOLDER'], applicant['resume_path'])
#             else:
#                 full_resume_path = None

#             resume_text = extract_text_from_resume(full_resume_path)
#             score, explanation = score_resume(resume_text, job_requirements)

#             applicant['resume_score'] = score
#             applicant['score_explanation'] = explanation
#             scored_applicants.append(applicant)

#             try:
#                 update_conn = get_db_connection()
#                 if update_conn:
#                     update_conn.execute("""
#                         UPDATE applications 
#                         SET resume_score = ?, score_explanation = ? 
#                         WHERE candidate_id = ? AND job_id = ?
#                     """, (score, explanation, applicant['candidate_id'], job_id))
#                     update_conn.commit()
#                     update_conn.close()
#             except Exception as e:
#                 print(f"Error saving score for candidate {applicant['candidate_id']}: {e}")

#         return render_template('admin_view_applicants.html',
#                                job_title=job_title,
#                                applicants=scored_applicants,
#                                job_id=job_id)
#     except Exception as e:
#         print(f"Error in admin_view_applicants: {e}")
#         flash(f"Error loading applicants: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         if conn:
#             conn.close()


# @app.route('/admin/update_status/<int:job_id>/<int:candidate_id>/<string:action>')
# def admin_update_status(job_id, candidate_id, action):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     if action == 'accept':
#         new_status = 'Selected for Test'
#         subject = "Congratulations! You've been Shortlisted"
#         body = "Congratulations! Your application has been shortlisted. Please check the 'Tests' section on your portal for the next steps."
#     elif action == 'reject':
#         new_status = 'Rejected'
#         subject = "Update Regarding Your Application"
#         body = "Thank you for your interest. After careful consideration, we have decided not to move forward with your application at this time."
#     else:
#         flash("Invalid action.", 'error')
#         conn.close()
#         return redirect(url_for('admin_view_applicants', job_id=job_id))

#     try:
#         conn.execute("UPDATE applications SET status = ? WHERE candidate_id = ? AND job_id = ?", (new_status, candidate_id, job_id))
#         conn.commit()
#         send_message(candidate_id, job_id, subject, body)
#         flash(f"Candidate status updated to '{new_status}' and notification sent.", 'success')
#     except Exception as e:
#         flash(f"Error updating status: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('admin_view_applicants', job_id=job_id))


# @app.route('/admin/delete_application/<int:job_id>/<int:candidate_id>')
# def admin_delete_application(job_id, candidate_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     try:
#         conn.execute('DELETE FROM applications WHERE job_id = ? AND candidate_id = ?', (job_id, candidate_id))
#         conn.commit()
#         flash("Candidate application deleted successfully.", 'success')
#     except Exception as e:
#         flash(f"Error deleting application: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('admin_view_applicants', job_id=job_id))


# @app.route('/admin/delete_job/<int:job_id>')
# def admin_delete_job(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     try:
#         conn.execute('DELETE FROM applications WHERE job_id = ?', (job_id,))
#         conn.execute('DELETE FROM tests WHERE job_id = ?', (job_id,))
#         conn.execute('DELETE FROM test_results WHERE job_id = ?', (job_id,))
#         conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
#         conn.commit()
#         flash("Job posting and all associated data deleted successfully.", 'success')
#     except Exception as e:
#         flash(f"Error deleting job: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('admin_dashboard'))


# # --- ADMIN TEST MANAGEMENT ROUTES ---

# @app.route('/admin/manage_test/<int:job_id>', methods=['GET', 'POST'])
# def admin_manage_test(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#     existing_test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if request.method == 'POST':
#         title = request.form['title']
#         duration = request.form['duration']
#         start_date = request.form['start_date']
#         start_time = request.form['start_time']
#         questions_json = request.form['questions_json']

#         start_datetime_str = f"{start_date} {start_time}:00"

#         try:
#             if existing_test:
#                 conn.execute('''
#                     UPDATE tests SET title=?, questions_json=?, duration_minutes=?, start_time=? WHERE job_id=?
#                 ''', (title, questions_json, duration, start_datetime_str, job_id))
#                 flash("Manual test updated successfully!", 'success')
#             else:
#                 conn.execute('''
#                     INSERT INTO tests (job_id, title, questions_json, duration_minutes, start_time) VALUES (?, ?, ?, ?, ?)
#                 ''', (job_id, title, questions_json, duration, start_datetime_str))
#                 flash("Manual test created successfully!", 'success')
#             conn.commit()
#             return redirect(url_for('admin_dashboard'))
#         except Exception as e:
#             flash(f"Error managing test: {e}", 'error')
#         finally:
#             conn.close()

#     conn.close()
#     return render_template('admin_manage_test.html',
#                            job=job,
#                            test=existing_test,
#                            job_id=job_id)


# @app.route('/admin/create_ai_test/<int:job_id>', methods=['GET', 'POST'])
# def admin_create_ai_test(job_id):
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
#     test_link = None

#     if request.method == "POST":
#         test_name = request.form.get("test_name")
#         domain_text = request.form.get("domain_text")
#         question_type = request.form.get("question_type")
#         num_questions = int(request.form.get("num_questions", 5))
#         marks_per_question = int(request.form.get("marks_per_question", 10))
#         duration = int(request.form.get("duration", 30))
#         start_datetime = request.form.get("start_datetime")

#         start_datetime_db = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')

#         if question_type == 'softskills':
#             from softskills_routes import generate_softskills_questions
#             questions, error, test_link = generate_softskills_questions(
#                 role_context=domain_text,
#                 num_questions=num_questions,
#                 marks_per_question=marks_per_question,
#                 job_id=job_id
#             )
#         else:
#             questions, error = generate_ai_test(domain_text, num_questions)
#             if not error:
#                 test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)

#         if error:
#             flash(f"Test generation failed: {error}", 'error')
#         else:
#             questions_json = json.dumps(questions)

#             if question_type == 'softskills':
#                 title = f"Soft Skills Interview - {domain_text}"
#             elif question_type == 'audio_text':
#                 title = f"Scenario Test - {domain_text}"
#             else:
#                 title = f"Technical Test - {domain_text}"

#             existing_test = conn.execute("SELECT id FROM tests WHERE job_id = ?", (job_id,)).fetchone()

#             if existing_test:
#                 conn.execute("""
#                     UPDATE tests 
#                     SET title = ?, questions_json = ?, duration_minutes = ?, start_time = ?
#                     WHERE job_id = ?
#                 """, (title, questions_json, duration, start_datetime_db, job_id))
#             else:
#                 conn.execute("""
#                     INSERT INTO tests (job_id, title, questions_json, duration_minutes, start_time)
#                     VALUES (?, ?, ?, ?, ?)
#                 """, (job_id, title, questions_json, duration, start_datetime_db))

#             conn.commit()
#             flash("Test created successfully!", 'success')

#     conn.close()
#     return render_template("admin_create_ai_test.html", job=job, test_link=test_link, job_id=job_id)


# @app.route('/admin/send_test_to_selected/<int:job_id>', methods=['POST'])
# def admin_send_test_to_selected(job_id):
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     global RESUME_THRESHOLD

#     data = request.get_json()
#     test_link = data.get('test_link')

#     if not test_link:
#         return jsonify({'success': False, 'message': 'No test link provided'}), 400

#     conn = get_db_connection()

#     try:
#         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#         if not job:
#             return jsonify({'success': False, 'message': 'Job not found'}), 404

#         threshold = RESUME_THRESHOLD
#         print(f"Using threshold: {threshold}")

#         candidates = conn.execute("""
#             SELECT c.id, c.name, c.email, a.resume_score, a.status
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             WHERE a.job_id = ? AND a.resume_score >= ?
#             ORDER BY a.resume_score DESC
#         """, (job_id, threshold)).fetchall()

#         print(f"Found {len(candidates)} eligible candidates")

#         if not candidates:
#             return jsonify({
#                 'success': False,
#                 'message': f'No candidates found with resume score >= {threshold}'
#             }), 404

#         sent_count = 0
#         failed_count = 0
#         already_selected_count = 0
#         failed_details = []

#         for candidate in candidates:
#             try:
#                 if candidate['status'] == 'Selected for Test' or candidate['status'] == 'Test Completed':
#                     already_selected_count += 1
#                     print(f"⏭️ {candidate['name']} already has status: {candidate['status']}")
#                     continue

#                 success = send_test_link_email(
#                     candidate['email'],
#                     candidate['name'],
#                     job['title'],
#                     test_link
#                 )

#                 if success:
#                     conn.execute("""
#                         UPDATE applications 
#                         SET status = 'Selected for Test' 
#                         WHERE candidate_id = ? AND job_id = ?
#                     """, (candidate['id'], job_id))
#                     sent_count += 1
#                     print(f"✅ Selected {candidate['name']} for test and email sent")
#                 else:
#                     failed_count += 1
#                     failed_details.append(f"{candidate['name']} ({candidate['email']})")

#             except Exception as e:
#                 print(f"❌ Error for {candidate['name']}: {e}")
#                 failed_count += 1
#                 failed_details.append(f"{candidate['name']} - {str(e)[:50]}")

#         conn.commit()

#         message = f"✅ Selected for Test: {sent_count}, Failed: {failed_count}, Already Selected: {already_selected_count}"

#         return jsonify({
#             'success': True,
#             'message': message,
#             'sent_count': sent_count,
#             'failed_count': failed_count,
#             'already_selected_count': already_selected_count,
#             'total_found': len(candidates)
#         })

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @app.route('/admin/check_selected_candidates/<int:job_id>')
# def check_selected_candidates(job_id):
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     global RESUME_THRESHOLD

#     conn = get_db_connection()

#     try:
#         threshold = RESUME_THRESHOLD
#         print(f"Preview using threshold: {threshold}")

#         candidates = conn.execute("""
#             SELECT c.name, c.email, a.resume_score, a.status
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             WHERE a.job_id = ? AND a.resume_score >= ?
#             ORDER BY a.resume_score DESC
#         """, (job_id, threshold)).fetchall()

#         result = []
#         for c in candidates:
#             result.append({
#                 'name': c['name'],
#                 'email': c['email'],
#                 'score': c['resume_score'],
#                 'status': c['status']
#             })

#         return jsonify({
#             'success': True,
#             'threshold': threshold,
#             'total': len(result),
#             'candidates': result
#         })
#     except Exception as e:
#         print(f"Error in check_selected_candidates: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @app.route('/update_threshold', methods=['POST'])
# def update_threshold():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     global RESUME_THRESHOLD
#     new_threshold = request.form.get('threshold')

#     try:
#         RESUME_THRESHOLD = int(new_threshold)
#         flash(f"Resume threshold updated to {RESUME_THRESHOLD}", 'success')
#         print(f"Threshold updated to: {RESUME_THRESHOLD}")
#     except:
#         flash("Invalid threshold value", 'error')

#     return redirect(request.referrer or url_for('admin_dashboard'))


# # @app.route('/admin/view_test_results/<int:job_id>')
# # def admin_view_test_results(job_id):
# #     if session.get('user_type') != 'admin':
# #         flash("Unauthorized access.", 'warning')
# #         return redirect(url_for('admin_login'))

# #     conn = get_db_connection()
# #     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()

# #     results = conn.execute('''
# #         SELECT 
# #             c.id AS candidate_id, c.name, c.email, 
# #             r.score, r.submission_time, 
# #             a.status
# #         FROM test_results r
# #         JOIN candidates c ON r.candidate_id = c.id
# #         JOIN applications a ON r.candidate_id = a.candidate_id AND r.job_id = a.job_id
# #         WHERE r.job_id = ?
# #         ORDER BY r.score DESC
# #     ''', (job_id,)).fetchall()

# #     conn.close()

# #     return render_template('admin_view_test_results.html', job=job, results=results)

# @app.route('/admin/view_test_results/<int:job_id>')
# def admin_view_test_results(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()

#     # Query uses LEFT JOIN so it doesn't drop candidates who only have soft skills
#     results = conn.execute('''
#         SELECT 
#             c.id AS candidate_id, c.name, c.email, 
#             COALESCE(r.score, 0) AS score, 
#             COALESCE(r.submission_time, CURRENT_TIMESTAMP) AS submission_time, 
#             a.status
#         FROM applications a
#         JOIN candidates c ON a.candidate_id = c.id
#         LEFT JOIN test_results r ON a.candidate_id = r.candidate_id AND a.job_id = r.job_id
#         WHERE a.job_id = ? AND a.status = 'Test Completed'
#         ORDER BY submission_time DESC
#     ''', (job_id,)).fetchall()

#     conn.close()
#     return render_template('admin_view_test_results.html', job=job, results=results, job_id=job_id)



# import time

# @app.route('/api/submit_softskills/<int:job_id>', methods=['POST'])
# def api_submit_softskills(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     try:
#         # 1. Create the folder if it doesn't exist
#         upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)

#         # 2. Process and save each audio file
#         saved_count = 0
#         for key in request.files:
#             if key.startswith('audio_'):
#                 q_num = key.split('_')[1]
#                 audio_file = request.files[key]
#                 answer_text = request.form.get(f'answer_{q_num}', 'Audio Response')

#                 if audio_file.filename:
#                     # Generate a unique filename
#                     filename = f"cand_{candidate_id}_job_{job_id}_q{q_num}_{int(time.time())}.webm"
#                     filepath = os.path.join(upload_folder, filename)
#                     audio_file.save(filepath)

#                     # Insert into softskills_responses table
#                     conn.execute('''
#                         INSERT INTO softskills_responses
#                         (candidate_id, job_id, question_number, question_text, audio_path, answer_text)
#                         VALUES (?, ?, ?, ?, ?, ?)
#                     ''', (candidate_id, job_id, q_num, answer_text, filename, answer_text))
#                     saved_count += 1

#         # 3. CRITICAL FIX: Update the main applications table to 'Test Completed'
#         conn.execute("UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#                      (candidate_id, job_id))

#         # 4. CRITICAL FIX: Create an entry in test_results so the Recruiter's dashboard sees it
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results (candidate_id, job_id, score, submission_time)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

#         conn.commit()
#         return jsonify({'success': True, 'message': f'Successfully saved {saved_count} recordings.'})

#     except Exception as e:
#         print(f"Error saving softskills: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @app.route('/hr/all_applicants')
# def hr_all_applicants():
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     # Fetch all applicants with job and test info
#     applicants = conn.execute("""
#         SELECT 
#             c.name,
#             c.email,
#             j.title AS job_role,
#             a.status,
#             a.applied_date,
#             tr.score,
#             tr.submission_time
#         FROM applications a
#         JOIN candidates c ON a.candidate_id = c.id
#         JOIN jobs j ON a.job_id = j.id
#         LEFT JOIN test_results tr 
#             ON a.candidate_id = tr.candidate_id 
#             AND a.job_id = tr.job_id
#         ORDER BY a.applied_date DESC
#     """).fetchall()

#     conn.close()

#     return render_template('hr_all_applicants.html', applicants=applicants)


# @app.route('/admin/view_analysis')
# def admin_view_analysis():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     # 1. Applicant status breakdown
#     status_rows = conn.execute(
#         "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status ORDER BY cnt DESC"
#     ).fetchall()
#     status_labels = [r['status'] for r in status_rows]
#     status_counts = [r['cnt'] for r in status_rows]

#     # 2. Job role popularity (top 8)
#     job_rows = conn.execute("""
#         SELECT j.title, COUNT(a.id) as cnt
#         FROM applications a
#         JOIN jobs j ON a.job_id = j.id
#         GROUP BY j.title ORDER BY cnt DESC LIMIT 8
#     """).fetchall()
#     job_labels = [r['title'] for r in job_rows]
#     job_counts  = [r['cnt']   for r in job_rows]

#     # 3. Key summary numbers
#     total_applicants  = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
#     test_completed    = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Test Completed'").fetchone()[0]
#     selected_for_test = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Selected for Test'").fetchone()[0]
#     just_applied      = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Applied'").fetchone()[0]

#     # 4. Score distribution buckets
#     score_rows = conn.execute("SELECT score FROM test_results WHERE score IS NOT NULL").fetchall()
#     scores = [r['score'] for r in score_rows]
#     bucket_labels = ['0-20', '21-40', '41-60', '61-80', '81-100']
#     bucket_counts = [0, 0, 0, 0, 0]
#     for s in scores:
#         if   s <= 20:  bucket_counts[0] += 1
#         elif s <= 40:  bucket_counts[1] += 1
#         elif s <= 60:  bucket_counts[2] += 1
#         elif s <= 80:  bucket_counts[3] += 1
#         else:          bucket_counts[4] += 1

#     conn.close()

#     return render_template('admin_view_analysis.html',
#         status_labels     = json.dumps(status_labels),
#         status_counts     = json.dumps(status_counts),
#         job_labels        = json.dumps(job_labels),
#         job_counts        = json.dumps(job_counts),
#         score_labels      = json.dumps(bucket_labels),
#         score_counts      = json.dumps(bucket_counts),
#         total_applicants  = total_applicants,
#         test_completed    = test_completed,
#         selected_for_test = selected_for_test,
#         just_applied      = just_applied,
#     )


# # ============================================================
# # REPLACE the existing admin_view_past_tests route in app.py
# # (find the lines that say):
# #
# #   @app.route('/admin/view-past-tests')
# #   def admin_view_past_tests():
# #       return render_template('admin_view_past_tests.html')
# #
# # and replace with the block below:
# # ============================================================

# @app.route('/admin/view-past-tests')
# def admin_view_past_tests():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     # Fetch every job that has at least one candidate selected for test or who completed it
#     jobs = conn.execute("""
#         SELECT DISTINCT j.id, j.title
#         FROM jobs j
#         JOIN applications a ON a.job_id = j.id
#         WHERE a.status IN ('Selected for Test', 'Test Completed')
#         ORDER BY j.id DESC
#     """).fetchall()

#     jobs_map = {}
#     for job in jobs:
#         job_id = job['id']

#         # Build the test link for this job
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)

#         # Fetch all candidates for this job who were selected or completed
#         candidates = conn.execute("""
#             SELECT c.name, a.status
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             WHERE a.job_id = ? AND a.status IN ('Selected for Test', 'Test Completed')
#             ORDER BY a.applied_date ASC
#         """, (job_id,)).fetchall()

#         jobs_map[job_id] = {
#             'job_title': job['title'],
#             'test_link': test_link,
#             'candidates': [{'name': c['name'], 'status': c['status']} for c in candidates]
#         }

#     conn.close()
#     return render_template('admin_view_past_tests.html', jobs_map=jobs_map)




# # --- REGISTER SOFT SKILLS BLUEPRINT ---
# from softskills_routes import softskills_bp, register_db, create_softskills_table
# register_db(get_db_connection)
# app.register_blueprint(softskills_bp)

# if __name__ == '__main__':
#     with app.app_context():
#         create_softskills_table()
#     print(f"--- ADMIN TEST CREDENTIALS: {ADMIN_USERNAME} / admin123 ---")
#     print("Ensure GROQ_API_KEY is set as an environment variable.")
#     app.run(host='0.0.0.0', port=8000, debug=True)













































































# import os
# import sqlite3
# import json
# import base64
# from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
# from werkzeug.security import generate_password_hash, check_password_hash
# from datetime import datetime
# from PIL import Image
# from io import BytesIO
# import time
# import docx
# import pdfplumber
# import re
# import cv2
# import numpy as np
# from groq import Groq


# app = Flask(__name__)
# app.secret_key = 'your_super_secret_key_hr_portal_2025'
# DATABASE = 'hr_portal.db'
# UPLOAD_FOLDER = 'uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# # Resume scoring threshold
# RESUME_THRESHOLD = 60

# # Email configuration
# from flask_mail import Mail, Message

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'shahjhalak0412@gmail.com'
# app.config['MAIL_PASSWORD'] = 'uwiw nufh yhgq vzmn'
# app.config['MAIL_DEFAULT_SENDER'] = 'shahjhalak0412@gmail.com'

# mail = Mail(app)


# def send_test_link_email(candidate_email, candidate_name, job_title, test_link):
#     """Send test link email to a candidate"""
#     try:
#         print(f"📧 Attempting to send email to: {candidate_email}")
#         print(f"   Name: {candidate_name}")
#         print(f"   Job: {job_title}")
#         print(f"   Link: {test_link}")

#         msg = Message(
#             subject=f"🎯 Test Invitation: {job_title}",
#             recipients=[candidate_email]
#         )

#         msg.body = f"""
# Dear {candidate_name},

# Congratulations! Based on your resume screening, you have been selected for the next round - the online assessment for {job_title}.

# Your Test Link: {test_link}

# Important Instructions:
# ✅ Complete the test before the deadline
# ✅ Ensure stable internet connection
# ✅ Face verification will be required
# ✅ You cannot retake the test once submitted
# ✅ Find a quiet place with good lighting for face verification

# Best of luck!
# HR Team
#         """

#         msg.html = f"""
# <!DOCTYPE html>
# <html>
# <head>
#     <style>
#         body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
#         .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
#         .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
#         .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; }}
#         .button {{ display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
#         .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; text-align: center; }}
#     </style>
# </head>
# <body>
#     <div class="container">
#         <div class="header">
#             <h2>Test Invitation</h2>
#         </div>
#         <div class="content">
#             <p>Dear <strong>{candidate_name}</strong>,</p>
#             <p>Congratulations! Based on your resume screening, you have been selected for the next round - the online assessment for <strong>{job_title}</strong>.</p>
#             <p><strong>Your Test Link:</strong></p>
#             <p style="text-align: center;">
#                 <a href="{test_link}" class="button">Start Your Test</a>
#             </p>
#             <p><strong>Important Instructions:</strong></p>
#             <ul>
#                 <li>Complete the test before the deadline</li>
#                 <li>Ensure stable internet connection</li>
#                 <li>Face verification will be required</li>
#                 <li>You cannot retake the test once submitted</li>
#             </ul>
#             <p>Best of luck!</p>
#             <p><strong>HR Team</strong></p>
#         </div>
#         <div class="footer">
#             <p>This is an automated message. Please do not reply to this email.</p>
#         </div>
#     </div>
# </body>
# </html>
#         """

#         mail.send(msg)
#         print(f"✅ Email successfully sent to {candidate_name} at {candidate_email}")
#         return True

#     except Exception as e:
#         print(f"❌ Failed to send email to {candidate_email}: {str(e)}")
#         print(f"   Error type: {type(e).__name__}")
#         return False


# def get_db_connection():
#     """Get database connection with timeout and error handling"""
#     try:
#         conn = sqlite3.connect(DATABASE, timeout=10)
#         conn.row_factory = sqlite3.Row
#         conn.execute("PRAGMA journal_mode=WAL")
#         return conn
#     except sqlite3.Error as e:
#         print(f"Database connection error: {e}")
#         return None


# # Register Jinja filter for JSON loading in templates
# def json_load(value):
#     try:
#         return json.loads(value)
#     except (TypeError, json.JSONDecodeError):
#         return {}

# app.jinja_env.filters['from_json'] = json_load

# # Internal Admin credentials
# ADMIN_USERNAME = 'hr_admin'
# ADMIN_PASSWORD_HASH = generate_password_hash('admin123')


# # Groq Client
# GROQ_CLIENT = None
# try:
#     GROQ_API_KEY = os.getenv("GROQ_API_KEY")
#     if not GROQ_API_KEY:
#         print("WARNING: GROQ_API_KEY not found in environment variables.")
#     else:
#         GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)
#         print("Groq API Client loaded successfully.")
# except Exception as e:
#     print(f"Groq Client failed to load: {e}")


# # --- GENERAL UTILITY FUNCTIONS ---

# def send_message(candidate_id, job_id, subject, body):
#     conn = get_db_connection()
#     try:
#         conn.execute(
#             'INSERT INTO messages (candidate_id, job_id, subject, body) VALUES (?, ?, ?, ?)',
#             (candidate_id, job_id, subject, body)
#         )
#         conn.commit()
#     except Exception as e:
#         print(f"Error sending message: {e}")
#     finally:
#         conn.close()


# def log_proctor_event(candidate_id, job_id, event_type, details=""):
#     conn = get_db_connection()
#     try:
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (candidate_id, job_id, event_type, details)
#         )
#         conn.commit()
#     except Exception as e:
#         print(f"Error logging event: {e}")
#     finally:
#         conn.close()


# # --- GROQ RESUME SCORING & AUTH UTILITY FUNCTIONS ---

# def extract_text_from_resume(resume_path):
#     """Extracts text from PDF or DOCX file."""
#     if not resume_path or not os.path.exists(resume_path):
#         return None

#     file_extension = os.path.splitext(resume_path)[1].lower()
#     text = ""

#     try:
#         if file_extension == '.pdf':
#             with pdfplumber.open(resume_path) as pdf:
#                 for page in pdf.pages:
#                     text += page.extract_text() or ""
#         elif file_extension == '.docx':
#             doc = docx.Document(resume_path)
#             text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
#         return text
#     except Exception as e:
#         return None


# def score_resume(resume_text, job_requirements_text):
#     """Scores the resume against job requirements using Groq API (llama-3.3-70b-versatile)."""
#     if not GROQ_CLIENT:
#         return 0, "Groq API Client not initialised. Check GROQ_API_KEY environment variable."

#     if not resume_text or not job_requirements_text:
#         return 0, "Missing resume or job requirements."

#     try:
#         prompt = f"""You are an expert HR recruitment analyst. Your task is to objectively score a candidate's
# resume against the provided job requirements. The score must reflect skill relevance,
# experience level, and domain expertise. You MUST respond with a single JSON object and nothing else.

# --- JOB REQUIREMENTS ---
# {job_requirements_text}

# --- CANDIDATE RESUME TEXT ---
# {resume_text}

# Based solely on the provided text, generate a score between 0 and 100 and a detailed, neutral rationale.
# Respond ONLY with this exact JSON format (no markdown, no extra text):
# {{"score": <integer 0-100>, "rationale": "<string>"}}"""

#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are an expert HR resume scoring assistant. "
#                         "Always respond with valid JSON only — no markdown fences, no prose, no explanation."
#                     )
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.1,
#         )

#         response_text = completion.choices[0].message.content.strip()

#         # Strip markdown fences if present
#         if response_text.startswith("```"):
#             response_text = re.sub(r"^```[a-zA-Z]*\n?", "", response_text)
#             response_text = re.sub(r"\n?```$", "", response_text).strip()

#         result = json.loads(response_text)
#         score = max(0, min(100, int(result.get('score', 0))))
#         rationale = result.get('rationale', "Score generated by Groq AI.")
#         return score, rationale

#     except json.JSONDecodeError as e:
#         return 0, f"Groq returned invalid JSON for resume scoring: {e}"
#     except Exception as e:
#         return 0, f"Error calling Groq API for resume scoring: {e}"


# # FaceNet setup
# try:
#     from keras_facenet import FaceNet
#     _facenet_embedder = FaceNet()
#     _face_detector_proto = os.path.join("models", "deploy.prototxt")
#     _face_detector_model = os.path.join("models", "res10_300x300_ssd_iter_140000_fp16.caffemodel")
#     if os.path.exists(_face_detector_proto) and os.path.exists(_face_detector_model):
#         _face_net_cv = cv2.dnn.readNetFromCaffe(_face_detector_proto, _face_detector_model)
#         FACENET_READY = True
#         print("FaceNet + OpenCV face detector loaded successfully.")
#     else:
#         FACENET_READY = False
#         print("WARNING: Caffe face detector model files not found in ./models/. Face verification disabled.")
# except Exception as _e:
#     FACENET_READY = False
#     print(f"WARNING: FaceNet not available ({_e}). Face verification disabled.")


# def _cv2_extract_face(img_bgr, size=(160, 160)):
#     """Detect and crop the largest confident face from a BGR image."""
#     h, w = img_bgr.shape[:2]
#     blob = cv2.dnn.blobFromImage(
#         cv2.resize(img_bgr, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
#     )
#     _face_net_cv.setInput(blob)
#     detections = _face_net_cv.forward()
#     if detections.shape[2] == 0:
#         return None
#     i = int(np.argmax(detections[0, 0, :, 2]))
#     conf = float(detections[0, 0, i, 2])
#     if conf < 0.5:
#         return None
#     box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
#     x1, y1, x2, y2 = box.astype(int)
#     face_crop = img_bgr[max(0, y1):y2, max(0, x1):x2]
#     if face_crop.size == 0:
#         return None
#     face_rgb = cv2.cvtColor(cv2.resize(face_crop, size), cv2.COLOR_BGR2RGB)
#     return face_rgb


# def _facenet_embedding(face_rgb):
#     """Return an L2-normalised FaceNet embedding for a (160,160,3) RGB array."""
#     emb = _facenet_embedder.embeddings(
#         np.expand_dims(face_rgb.astype("float32"), axis=0)
#     )[0]
#     return emb / np.linalg.norm(emb)


# def generate_ai_test(domain, num_questions):
#     """Generate test questions using Groq AI"""
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized"

#     try:
#         prompt = f"""
# Generate {num_questions} multiple choice questions about {domain}.
# Each question must have 4 options with exactly one correct answer.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "radio",
#     "options": ["Option A", "Option B", "Option C", "Option D"],
#     "answer": "Option A",
#     "category": "technical"
#   }}
# ]
# """
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.3
#         )

#         response_text = completion.choices[0].message.content.strip()

#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)

#         questions = json.loads(response_text)
#         return questions, None

#     except Exception as e:
#         return None, str(e)


# def verify_faces(stored_image_path, live_image_data_uri):
#     """
#     Compare a stored profile photo against a live webcam capture.
#     Uses local FaceNet embeddings — no external API required.
#     Falls back to a permissive pass if FaceNet is not available.
#     """
#     if not FACENET_READY:
#         return True, "Face verification skipped (FaceNet not available)."

#     full_stored_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_image_path)
#     if not os.path.exists(full_stored_path):
#         return False, "Reference photo not found in profile."

#     try:
#         stored_bgr = cv2.imread(full_stored_path)
#         if stored_bgr is None:
#             return False, "Could not read stored profile photo."
#         stored_face = _cv2_extract_face(stored_bgr)
#         if stored_face is None:
#             return False, "No face detected in stored profile photo."

#         _, encoded = live_image_data_uri.split(',', 1)
#         live_bytes = base64.b64decode(encoded)
#         live_pil = Image.open(BytesIO(live_bytes)).convert('RGB')
#         live_bgr = cv2.cvtColor(np.array(live_pil), cv2.COLOR_RGB2BGR)
#         live_face = _cv2_extract_face(live_bgr)
#         if live_face is None:
#             return False, "No face detected in live camera image. Ensure good lighting and look directly at the camera."

#         stored_emb = _facenet_embedding(stored_face)
#         live_emb = _facenet_embedding(live_face)
#         distance = float(np.linalg.norm(stored_emb - live_emb))

#         THRESHOLD = 0.55
#         if distance < THRESHOLD:
#             return True, f"Verification successful (distance={distance:.3f})."
#         else:
#             return False, f"Face mismatch (distance={distance:.3f}). Try better lighting or re-upload your profile photo."

#     except Exception as e:
#         return False, f"Verification error: {e}"


# # --- GROQ: QUESTION GENERATION & TEST GRADING ---

# def generate_assessment_json(test_name, domain_text, num_questions, question_type):
#     """Generate test questions using Groq AI."""
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized. Please set the GROQ_API_KEY environment variable."

#     try:
#         if question_type == "audio":
#             type_instruction = (
#                 "Create scenario-based questions that require a verbal/written response. "
#                 "Set 'type' to 'audio_text' for every question. "
#                 "Set 'options' to an empty array []. "
#                 "The 'answer' field should contain a sample ideal response."
#             )
#         else:
#             type_instruction = (
#                 "Create multiple-choice questions (MCQ). "
#                 "Set 'type' to 'radio' for every question. "
#                 "Provide exactly 4 distinct strings in 'options'. "
#                 "The 'answer' field must exactly match one of the 4 options."
#             )

#         prompt = f"""You are an expert HR assessment creator.

# Generate a recruitment test with the details below and return ONLY a valid JSON array — no markdown, no explanation, no extra text.

# Test Name     : {test_name}
# Topic / Domain: {domain_text}
# Total Questions: {num_questions}
# Question Type : {question_type}

# Instructions:
# {type_instruction}

# Required JSON schema for every question object:
# {{
#   "q"      : "<question text>",
#   "type"   : "<radio | audio_text>",
#   "options": ["<opt1>", "<opt2>", "<opt3>", "<opt4>"],
#   "answer" : "<correct answer or ideal response>"
# }}

# Return a JSON array of exactly {num_questions} question objects."""

#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a professional HR assessment generator. "
#                         "Always respond with valid JSON only — no markdown fences, no prose."
#                     )
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.3,
#         )

#         response_text = completion.choices[0].message.content.strip()

#         if response_text.startswith("```"):
#             response_text = re.sub(r"^```[a-zA-Z]*\n?", "", response_text)
#             response_text = re.sub(r"\n?```$", "", response_text).strip()

#         questions = json.loads(response_text)

#         if not isinstance(questions, list):
#             return None, "Groq returned an unexpected format (expected a JSON array)."

#         return questions, None

#     except json.JSONDecodeError as e:
#         return None, f"Groq returned invalid JSON: {e}"
#     except Exception as e:
#         return None, f"AI Question Generation failed: {str(e)}"


# def grade_test_ai(test, submitted_answers):
#     """
#     Hybrid grader:
#     - MCQ (radio)    : local exact-match using 0-based key  q_{idx}
#     - Scenario (audio_text): scored by Groq AI.

#     Form keys sent by the frontend:
#         q_0  → questions[0]
#         q_1  → questions[1]
#         ...
#         q_N  → questions[N]
#     This 0-based scheme is fixed in candidate_view_test.html (loop.index0).
#     Never use idx+1 here — that was the root cause of the one-position shift.
#     """

#     # ── 1. Parse questions ───────────────────────────────────────────────
#     try:
#         questions = json.loads(test['questions_json'])
#         print(f"Grading test with {len(questions)} questions")
#         print(f"Submitted answers: {submitted_answers}")
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         return 0, f"Could not parse test questions: {e}"

#     if not questions:
#         return 0, "No questions found in test."

#     # ── 2. Single normaliser (defined ONCE, never re-defined inside the loop) ──
#     def _norm(s):
#         """Strip, lowercase, collapse whitespace — makes comparison robust."""
#         return " ".join(str(s).strip().lower().split()) if s else ""

#     # ── 3. Grade each question ───────────────────────────────────────────
#     total_q        = len(questions)
#     points_earned  = 0.0
#     rationale_parts = []
#     correct_count  = 0
#     audio_text_qs  = []   # [(idx, q, candidate_ans), ...]

#     for idx, q in enumerate(questions):
#         # Form key is ALWAYS 0-based — q_0, q_1, q_2 …
#         form_key = f"q_{idx}"

#         raw_answer = submitted_answers.get(form_key, "")
#         if isinstance(raw_answer, list):
#             raw_answer = raw_answer[0] if raw_answer else ""

#         candidate_ans = _norm(raw_answer)
#         correct_ans   = _norm(q.get("answer", ""))
#         q_type        = q.get("type", "radio")

#         print(f"Q{idx} (display Q{idx+1}): key={form_key} | "
#               f"type={q_type} | candidate='{candidate_ans}' | correct='{correct_ans}'")

#         if q_type == "radio":
#             if candidate_ans and candidate_ans == correct_ans:
#                 points_earned += 1
#                 correct_count += 1
#                 rationale_parts.append(f"Q{idx+1}: Correct ✓")
#                 print(f"  ✅ Correct")
#             else:
#                 if not candidate_ans:
#                     rationale_parts.append(f"Q{idx+1}: No answer provided")
#                     print(f"  ❌ No answer submitted")
#                 else:
#                     rationale_parts.append(
#                         f"Q{idx+1}: Wrong (answered '{raw_answer}', correct '{q.get('answer','')}')"
#                     )
#                     print(f"  ❌ Wrong answer")
#         else:
#             # audio_text or any future open-ended type → send to Groq
#             audio_text_qs.append((idx, q, candidate_ans))

#     mcq_total = len([q for q in questions if q.get("type") == "radio"])
#     print(f"MCQ Results: {correct_count}/{mcq_total} correct")

#     # ── 4. AI grading for open-ended / audio questions ───────────────────
#     if audio_text_qs and GROQ_CLIENT:
#         try:
#             batch_items = "\n\n".join([
#                 f"[Q{idx+1}]\n"
#                 f"Question: {q['q']}\n"
#                 f"Ideal answer: {q.get('answer', '')}\n"
#                 f"Candidate answer: {ans}"
#                 for idx, q, ans in audio_text_qs
#             ])

#             prompt = f"""You are grading written scenario answers.
# For each question below, award a score from 0 to 10 based on relevance and quality vs the ideal answer.
# Return ONLY a JSON array with one object per question, in order:
# [{{"q": 1, "score": <0-10>, "comment": "<one sentence>"}}, ...]

# {batch_items}"""

#             completion = GROQ_CLIENT.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=[
#                     {"role": "system", "content": "You are an exam evaluator. Reply with valid JSON only."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0,
#             )
#             result_text = completion.choices[0].message.content.strip()
#             if result_text.startswith("```"):
#                 result_text = re.sub(r"^```[a-zA-Z]*\n?", "", result_text)
#                 result_text = re.sub(r"\n?```$", "", result_text).strip()

#             ai_scores = json.loads(result_text)

#             for i, (idx, q, ans) in enumerate(audio_text_qs):
#                 raw     = ai_scores[i] if i < len(ai_scores) else {}
#                 ai_pts  = max(0, min(10, int(raw.get("score", 0))))
#                 points_earned += ai_pts / 10.0
#                 rationale_parts.append(
#                     f"Q{idx+1} (scenario): {ai_pts}/10 — {raw.get('comment', '')}"
#                 )

#         except Exception as e:
#             print(f"Groq grading error: {e}")
#             for idx, q, ans in audio_text_qs:
#                 points_earned += 0.5
#                 rationale_parts.append(
#                     f"Q{idx+1} (scenario): AI grading failed, partial credit awarded."
#                 )

#     elif audio_text_qs:
#         for idx, q, ans in audio_text_qs:
#             points_earned += 0.5
#             rationale_parts.append(
#                 f"Q{idx+1} (scenario): Groq unavailable, partial credit awarded."
#             )

#     # ── 5. Final score ───────────────────────────────────────────────────
#     final_score = max(0, min(100, round((points_earned / total_q) * 100)))
#     rationale   = " | ".join(rationale_parts)
#     print(f"Final score: {final_score}% ({points_earned}/{total_q} points)")
#     return final_score, rationale


# # --- AUTHENTICATION & GLOBAL ROUTES ---

# @app.route('/')
# def index():
#     return render_template('index.html')


# @app.route('/logout')
# def logout():
#     session.clear()
#     flash("You have been logged out successfully.", 'info')
#     return redirect(url_for('index'))


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# # --- CANDIDATE ROUTES ---

# @app.route('/signup', methods=('GET', 'POST'))
# def candidate_signup():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email']
#         password = request.form['password']

#         if not all([name, email, password]):
#             flash("Missing required fields (Name, Email, Password).", 'error')
#             return redirect(url_for('candidate_signup'))

#         conn = get_db_connection()
#         try:
#             conn.execute(
#                 'INSERT INTO candidates (name, email, password_hash) VALUES (?, ?, ?)',
#                 (name, email, generate_password_hash(password))
#             )
#             conn.commit()
#             flash("Account created! Log in and complete your profile before applying.", 'success')
#             return redirect(url_for('candidate_login'))
#         except sqlite3.IntegrityError:
#             flash("Email already registered.", 'error')
#             return redirect(url_for('candidate_signup'))
#         finally:
#             conn.close()

#     return render_template('candidate_signup.html')


# @app.route('/login', methods=('GET', 'POST'))
# def candidate_login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']

#         conn = get_db_connection()
#         user = conn.execute('SELECT * FROM candidates WHERE email = ?', (email,)).fetchone()
#         conn.close()

#         if user and check_password_hash(user['password_hash'], password):
#             session['user_id'] = user['id']
#             session['user_type'] = 'candidate'
#             flash(f"Welcome back, {user['name']}!", 'success')
#             return redirect(url_for('candidate_jobs'))
#         else:
#             flash("Invalid email or password.", 'error')
#             return render_template('candidate_login.html')

#     return render_template('candidate_login.html')


# @app.route('/candidate/profile', methods=('GET', 'POST'))
# def candidate_profile():
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to manage your profile.", 'warning')
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()
#     candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

#     if request.method == 'POST':
#         name = request.form['name']
#         dob = request.form['dob']
#         phone = request.form['phone']
#         address = request.form['address']
#         profile_image_data = request.form.get('profile_image_data')

#         resume_path = candidate['resume_path']
#         resume_file = request.files.get('resume')
#         db_resume_path = resume_path
#         db_image_path = candidate['profile_image_path']

#         if resume_file and resume_file.filename != '':
#             if resume_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], resume_path)):
#                 os.remove(os.path.join(app.config['UPLOAD_FOLDER'], resume_path))
#             filename = f"resume_{candidate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume_file.filename}"
#             resume_path_full = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             resume_file.save(resume_path_full)
#             db_resume_path = filename

#         if profile_image_data:
#             if db_image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], db_image_path)):
#                 os.remove(os.path.join(app.config['UPLOAD_FOLDER'], db_image_path))

#             header, encoded = profile_image_data.split(',', 1)
#             image_bytes = base64.b64decode(encoded)
#             img = Image.open(BytesIO(image_bytes))

#             image_filename = f"face_{candidate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
#             image_path_full = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
#             img.save(image_path_full, 'jpeg')
#             db_image_path = image_filename

#         try:
#             conn.execute(
#                 '''UPDATE candidates SET name=?, dob=?, phone=?, address=?, resume_path=?, profile_image_path=? WHERE id=?''',
#                 (name, dob, phone, address, db_resume_path, db_image_path, candidate_id)
#             )
#             conn.commit()
#             flash("Profile updated successfully!", 'success')
#             candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
#         except Exception as e:
#             flash(f"Error updating profile: {e}", 'error')
#         finally:
#             conn.close()

#     return render_template('candidate_profile.html', candidate=candidate)


# @app.route('/candidate/messages')
# def candidate_messages():
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     messages = conn.execute('''
#         SELECT 
#             m.*, j.title AS job_title 
#         FROM messages m 
#         LEFT JOIN jobs j ON m.job_id = j.id
#         WHERE m.candidate_id = ? 
#         ORDER BY m.created_at DESC
#     ''', (candidate_id,)).fetchall()

#     conn.execute('UPDATE messages SET is_read = 1 WHERE candidate_id = ? AND is_read = 0', (candidate_id,))
#     conn.commit()
#     conn.close()

#     return render_template('candidate_messages.html', messages=messages)


# @app.route('/candidate/jobs')
# def candidate_jobs():
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to view job postings.", 'warning')
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     candidate = conn.execute('SELECT resume_path, phone, address FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

#     can_apply = all([
#         candidate,
#         candidate['resume_path'],
#         candidate['phone'],
#         candidate['address']
#     ])

#     if not can_apply:
#         flash("Warning: You must complete all profile details (including resume, phone, and address) to apply.", 'warning')

#     jobs = conn.execute('''
#         SELECT j.*, a.status,
#                t.questions_json AS test_questions_json
#         FROM jobs j 
#         LEFT JOIN applications a 
#             ON j.id = a.job_id AND a.candidate_id = ?
#         LEFT JOIN tests t
#             ON j.id = t.job_id
#         WHERE j.deadline >= date('now') 
#         ORDER BY j.posted_date DESC
#     ''', (candidate_id,)).fetchall()

#     jobs_list = []
#     for job in jobs:
#         job_dict = dict(job)
#         is_softskills = False
#         try:
#             qs = json.loads(job_dict.get('test_questions_json') or '[]')
#             if qs and all(q.get('type') == 'audio_text' for q in qs):
#                 is_softskills = True
#         except Exception:
#             pass
#         job_dict['is_softskills'] = is_softskills
#         jobs_list.append(job_dict)

#     conn.close()

#     return render_template('candidate_jobs.html',
#                            jobs=jobs_list,
#                            can_apply=can_apply)


# @app.route('/candidate/apply/<int:job_id>')
# def candidate_apply(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()
#     candidate = conn.execute('SELECT resume_path, phone, address FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

#     if not all([candidate['resume_path'], candidate['phone'], candidate['address']]):
#         flash("Application failed: Please complete all profile details before applying.", 'error')
#         conn.close()
#         return redirect(url_for('candidate_jobs'))

#     try:
#         conn.execute(
#             'INSERT INTO applications (job_id, candidate_id, status) VALUES (?, ?, ?)',
#             (job_id, candidate_id, 'Applied')
#         )
#         conn.commit()
#         flash("Application submitted successfully!", 'success')
#     except sqlite3.IntegrityError:
#         flash("You have already applied for this job.", 'info')
#     except Exception as e:
#         flash(f"An error occurred during application: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))


# # --- CANDIDATE TESTING/AUTH ROUTES ---

# @app.route('/candidate/test/auth/<int:job_id>')
# def candidate_auth_start(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()
#     candidate = conn.execute('SELECT profile_image_path FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
#     test = conn.execute('SELECT title, questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     application = conn.execute('SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?', (job_id, candidate_id)).fetchone()
#     conn.close()

#     if not test or application['status'] != 'Selected for Test':
#         flash("You are not authorized for this test.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     if not candidate['profile_image_path']:
#         flash("Profile image required for authentication. Please update your profile.", 'warning')
#         return redirect(url_for('candidate_profile'))

#     is_softskills = False
#     try:
#         title_lower = (test['title'] or '').lower()
#         questions = json.loads(test['questions_json'] or '[]')
#         if 'soft skill' in title_lower or 'soft skills' in title_lower:
#             is_softskills = True
#         elif questions and all(q.get('type') == 'audio_text' for q in questions):
#             is_softskills = True
#     except Exception:
#         pass

#     session[f'test_type_{job_id}'] = 'softskills' if is_softskills else 'standard'

#     return render_template('candidate_auth_start.html', job_id=job_id, job_title=test['title'])


# @app.route('/candidate/test/verify/<int:job_id>', methods=['POST'])
# def candidate_test_verify(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

#     candidate_id = session['user_id']
#     live_image_data_uri = request.json.get('image')

#     conn = get_db_connection()
#     candidate = conn.execute('SELECT profile_image_path FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
#     conn.close()

#     stored_path = candidate['profile_image_path']

#     if not stored_path or not live_image_data_uri:
#         log_proctor_event(candidate_id, job_id, 'Face Auth Failed', 'Missing image data.')
#         return jsonify({'success': False, 'message': 'Authentication failed: Missing image data.'}), 400

#     is_verified, message = verify_faces(stored_path, live_image_data_uri)

#     if is_verified:
#         log_proctor_event(candidate_id, job_id, 'Face Auth Success', message)

#         conn2 = get_db_connection()
#         test_row = conn2.execute('SELECT title, questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#         conn2.close()

#         is_softskills = False
#         if test_row:
#             try:
#                 title_lower = (test_row['title'] or '').lower()
#                 qs = json.loads(test_row['questions_json'] or '[]')
#                 if 'soft skill' in title_lower:
#                     is_softskills = True
#                 elif qs and all(q.get('type') == 'audio_text' for q in qs):
#                     is_softskills = True
#             except Exception:
#                 pass

#         if is_softskills:
#             redirect_url = url_for('softskills.candidate_softskills_view', job_id=job_id)
#         else:
#             redirect_url = url_for('candidate_view_test', job_id=job_id)

#         return jsonify({'success': True, 'message': 'Verification successful.', 'redirect': redirect_url})
#     else:
#         log_proctor_event(candidate_id, job_id, 'Face Auth Failed', message)
#         return jsonify({'success': False, 'message': f'Verification failed. {message}'}), 401


# @app.route('/candidate/test/<int:job_id>')
# def candidate_view_test(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     # Check if test already submitted
#     existing_result = conn.execute(
#         'SELECT * FROM test_results WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()

#     if existing_result:
#         conn.close()
#         flash("You have already completed this test.", 'info')
#         return redirect(url_for('candidate_jobs'))

#     # Get test details
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     application = conn.execute('SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?',
#                                (job_id, candidate_id)).fetchone()
#     conn.close()

#     # Validate test access
#     if not test:
#         flash("Test not found. Please contact the administrator.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     if not application or application['status'] != 'Selected for Test':
#         flash("You are not authorized to take this test.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     # Parse questions with better error handling
#     questions = []
#     try:
#         if test['questions_json']:
#             # Clean up any potential markdown formatting
#             questions_json_str = test['questions_json'].strip()
            
#             # Remove markdown code blocks if present
#             if questions_json_str.startswith('```'):
#                 questions_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', questions_json_str)
#                 questions_json_str = re.sub(r'\n?```$', '', questions_json_str)
            
#             questions = json.loads(questions_json_str)
            
#             # Validate questions structure
#             if not isinstance(questions, list):
#                 print(f"❌ Questions is not a list, got: {type(questions)}")
#                 questions = []
#             elif len(questions) == 0:
#                 print("❌ Questions list is empty")
#                 flash("No questions found in the test. Please contact administrator.", 'error')
#                 return redirect(url_for('candidate_jobs'))
#             else:
#                 print(f"✅ Successfully loaded {len(questions)} questions")
#                 print(f"First question: {questions[0].get('q', 'No question text')[:100]}")
#         else:
#             print("❌ No questions_json found in test")
#             flash("Test questions are missing. Please contact administrator.", 'error')
#             return redirect(url_for('candidate_jobs'))
            
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON decode error: {e}")
#         print(f"Raw JSON: {test['questions_json'][:200] if test['questions_json'] else 'None'}")
#         flash("Error loading test questions. The test format is invalid. Please contact administrator.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     except Exception as e:
#         print(f"❌ Unexpected error parsing questions: {e}")
#         flash("Error loading test questions. Please contact administrator.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     # Handle start time - ensure it's valid
#     can_start = True
#     time_status = ""
#     try:
#         if test['start_time']:
#             start_time = datetime.strptime(test['start_time'], '%Y-%m-%d %H:%M:%S')
#             current_time = datetime.now()
            
#             if current_time < start_time:
#                 time_status = f"Test opens on {start_time.strftime('%B %d, %Y at %I:%M %p')}"
#                 can_start = False
#             else:
#                 time_status = f"Test duration: {test['duration_minutes']} minutes. Best of luck!"
#                 can_start = True
#         else:
#             time_status = f"Test duration: {test['duration_minutes']} minutes. You can start now!"
#             can_start = True
#     except (ValueError, TypeError) as e:
#         print(f"⚠️ Error parsing start_time: {e}, allowing test to start")
#         time_status = f"Test duration: {test['duration_minutes']} minutes."
#         can_start = True

#     # Debug information
#     print(f"=== Test Debug Info ===")
#     print(f"Job ID: {job_id}")
#     print(f"Test Title: {test['title']}")
#     print(f"Duration: {test['duration_minutes']} minutes")
#     print(f"Start Time: {test['start_time']}")
#     print(f"Number of Questions: {len(questions)}")
#     print(f"Can Start: {can_start}")
#     print(f"======================")

#     return render_template('candidate_view_test.html',
#                            test=test,
#                            questions=questions,
#                            time_status=time_status,
#                            can_start=can_start,
#                            job_id=job_id,
#                            questions_json=json.dumps(questions))  # Pass JSON string to template

# @app.route('/admin/test_email_config')
# def test_email_config():
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     try:
#         msg = Message(
#             subject="Test Email from HR Portal",
#             recipients=['shahjhalak0412@gmail.com'],
#             body="This is a test email to verify SMTP configuration is working."
#         )
#         mail.send(msg)
#         return "✅ Test email sent successfully! Check your inbox."
#     except Exception as e:
#         return f"❌ Email failed: {str(e)}"



# # ─────────────────────────────────────────────────────────────────────────────
# # PATCH for app.py  →  replace your existing candidate_submit_test route
# # with the version below.
# #
# # The key fix: when ANY submitted answer is a base64 data URI (audio recording),
# # we route the whole submission through the softskills pipeline so the audio
# # gets saved to disk and the admin can play it back later.
# # ─────────────────────────────────────────────────────────────────────────────


# # Abhi aj ka OG jo chlra 4-4-2026 ka 
# @app.route('/candidate/submit_test/<int:job_id>', methods=['POST'])
# def candidate_submit_test(job_id):
#     if session.get('user_type') != 'candidate' or request.method != 'POST':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     print(f"=== SUBMIT TEST CALLED for job_id: {job_id} ===")

#     conn = get_db_connection()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if not test:
#         conn.close()
#         flash("Test configuration not found.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     # Check duplicate submission
#     existing_result = conn.execute(
#         'SELECT id FROM test_results WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
#     if existing_result:
#         conn.close()
#         flash("You have already submitted this test.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     submitted_answers = dict(request.form)

#     # ── Detect if any answer contains a base64 audio recording ──────────────
#     has_audio_answers = any(
#         str(v[0] if isinstance(v, list) else v).startswith('data:')
#         for v in submitted_answers.values()
#     )

#     if has_audio_answers:
#         # Route through softskills pipeline to save audio files properly
#         conn.close()
#         print("  → Detected audio answers, routing to softskills submission")

#         # Build a proper answer_N / audio_N mapping expected by softskills submit
#         import re as _re
#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)

#         # Fetch questions so we can store question_text
#         questions = []
#         try:
#             questions = json.loads(test['questions_json'] or '[]')
#         except Exception:
#             pass

#         conn2 = get_db_connection()
#         try:
#             # Guard: check softskills_responses too
#             existing_ss = conn2.execute(
#                 'SELECT id FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#                 (candidate_id, job_id)
#             ).fetchone()
#             if existing_ss:
#                 flash("You have already submitted this interview.", 'info')
#                 return redirect(url_for('candidate_jobs'))

#             saved = 0
#             for key, val in submitted_answers.items():
#                 m = _re.match(r'^q_(\d+)$', key)
#                 if not m:
#                     continue
#                 question_num = int(m.group(1))
#                 raw_val = val[0] if isinstance(val, list) else val

#                 audio_path_db = None
#                 answer_text = ''

#                 if raw_val and raw_val.startswith('data:'):
#                     try:
#                         _, encoded = raw_val.split(',', 1)
#                         audio_bytes = base64.b64decode(encoded)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(audio_bytes)
#                         audio_path_db = filename
#                         saved += 1
#                         print(f"  ✅ Saved audio Q{question_num}: {filename} ({len(audio_bytes)} bytes)")
#                     except Exception as e:
#                         print(f"  ⚠️ Audio decode failed Q{question_num}: {e}")
#                         answer_text = raw_val
#                 else:
#                     answer_text = raw_val

#                 # Also grab optional typed text (q_N_text)
#                 text_fallback = submitted_answers.get(f'q_{question_num}_text', '')
#                 if isinstance(text_fallback, list):
#                     text_fallback = text_fallback[0]
#                 if text_fallback and not answer_text:
#                     answer_text = text_fallback

#                 q_text = ''
#                 if question_num <= len(questions):
#                     q_text = questions[question_num - 1].get('q', '')

#                 conn2.execute('''
#                     INSERT INTO softskills_responses
#                     (candidate_id, job_id, question_number, question_text, audio_path, answer_text)
#                     VALUES (?, ?, ?, ?, ?, ?)
#                 ''', (candidate_id, job_id, question_num, q_text, audio_path_db, answer_text))

#             conn2.execute(
#                 "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#                 (candidate_id, job_id)
#             )
#             conn2.execute('''
#                 INSERT OR REPLACE INTO test_results
#                 (candidate_id, job_id, score, submitted_answers_json)
#                 VALUES (?, ?, ?, ?)
#             ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills audio interview completed'})))
#             conn2.commit()

#             log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Audio interview, {saved} files saved")
#             flash(f"Interview submitted successfully! Your {saved} audio recording(s) have been saved.", 'success')

#         except Exception as e:
#             print(f"❌ Error saving audio answers: {e}")
#             import traceback; traceback.print_exc()
#             flash(f"Error saving your answers: {e}", 'error')
#         finally:
#             conn2.close()

#         return redirect(url_for('candidate_jobs'))

#     # ── Standard MCQ / text test grading ────────────────────────────────────
#     # score, rationale = grade_test_ai(test, submitted_answers)
#     # log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Score: {score}")

#     # try:
#     #     conn.execute(
#     #         '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json) VALUES (?, ?, ?, ?)''',
#     #         (candidate_id, job_id, score, json.dumps(submitted_answers))
#     #     )
#     #     conn.execute(
#     #         "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#     #         (candidate_id, job_id)
#     #     )
#     #     conn.commit()
#     #     flash(f"Test submitted successfully! Final Score: {score}. Rationale: {rationale}", 'success')
#     # except Exception as e:
#     #     flash(f"Error saving test results: {e}", 'error')
#     # finally:
#     #     conn.close()

#     # return redirect(url_for('candidate_jobs'))


   
#     # ───────────── MCQ GRADING (FINAL FIXED) ─────────────
#     print("=== QUESTIONS JSON FROM DB ===")
#     print(test['questions_json'])   # 🔥 DEBUG

#     questions = []
#     try:
#         questions = json.loads(test['questions_json'] or '[]')
#     except Exception as e:
#         print("Error loading questions:", e)

#     def normalize(text):
#         return str(text).strip().lower().replace(".", "").replace("'", "")

#     score = 0
#     total_questions = len(questions)

#     print(f"Grading test with {total_questions} questions")
#     print("Submitted answers:", submitted_answers)

#     for idx, q in enumerate(questions, start=1):
#         key = f"q_{idx}"

#         candidate_answer = submitted_answers.get(key, "")
#         if isinstance(candidate_answer, list):
#             candidate_answer = candidate_answer[0]

#         candidate_answer = normalize(candidate_answer)
#         correct_answer = normalize(q.get('answer', ''))

#         options = q.get('options', [])

#         # Handle A/B/C/D answers
#         if candidate_answer in ['a', 'b', 'c', 'd'] and options:
#             option_index = ord(candidate_answer) - ord('a')
#             if option_index < len(options):
#                 candidate_answer = normalize(options[option_index])

#         print(f"Q{idx}: Candidate='{candidate_answer}' | Correct='{correct_answer}'")

#         if candidate_answer == correct_answer:
#             score += 1
#             print("  ✅ Correct")
#         else:
#             print("  ❌ Wrong")

#     score_percent = (score / total_questions) * 100 if total_questions > 0 else 0
#     score_percent = round(score_percent, 2)

#     print(f"Final Score: {score_percent}%")

#     # Save result
#     try:
#         conn.execute(
#             '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json)
#                VALUES (?, ?, ?, ?)''',
#             (candidate_id, job_id, score_percent, json.dumps(submitted_answers))
#         )

#         conn.execute(
#             "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#             (candidate_id, job_id)
#         )

#         conn.commit()
#         flash(f"Test submitted successfully! Score: {score_percent}%", 'success')

#     except Exception as e:
#         flash(f"Error saving test results: {e}", 'error')

#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))

# # @app.route('/candidate/submit_test/<int:job_id>', methods=['POST'])
# # def candidate_submit_test(job_id):
# #     if session.get('user_type') != 'candidate' or request.method != 'POST':
# #         return redirect(url_for('candidate_login'))

# #     candidate_id = session['user_id']
# #     print(f"=== SUBMIT TEST CALLED for job_id: {job_id} ===")

# #     print("Form data received:")
# #     for key, value in request.form.items():
# #         print(f"  {key}: {value}")

# #     conn = get_db_connection()
# #     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

# #     if not test:
# #         conn.close()
# #         flash("Test configuration not found.", 'error')
# #         return redirect(url_for('candidate_jobs'))

# #     submitted_answers = dict(request.form)

# #     existing_result = conn.execute('SELECT id FROM test_results WHERE candidate_id = ? AND job_id = ?', (candidate_id, job_id)).fetchone()
# #     if existing_result:
# #         conn.close()
# #         flash("You have already submitted this test.", 'error')
# #         return redirect(url_for('candidate_jobs'))

# #     score, rationale = grade_test_ai(test, submitted_answers)
# #     log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Score: {score}")

# #     try:
# #         conn.execute(
# #             '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json) VALUES (?, ?, ?, ?)''',
# #             (candidate_id, job_id, score, json.dumps(submitted_answers))
# #         )
# #         conn.execute("UPDATE applications SET status = ? WHERE candidate_id = ? AND job_id = ?", ('Test Completed', candidate_id, job_id))
# #         conn.commit()
# #         flash(f"Test submitted successfully! Final Score: {score}. Rationale: {rationale}", 'success')
# #     except Exception as e:
# #         flash(f"Error saving test results: {e}", 'error')
# #     finally:
# #         conn.close()

# #     return redirect(url_for('candidate_jobs'))


# # --- ADMIN ROUTES ---

# @app.route('/admin/login', methods=('GET', 'POST'))
# def admin_login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
#             session['user_id'] = 'admin'
#             session['user_type'] = 'admin'
#             flash("Admin logged in successfully.", 'success')
#             return redirect(url_for('admin_dashboard'))
#         else:
#             flash("Invalid Admin Credentials.", 'error')
#             return render_template('admin_login.html')

#     return render_template('admin_login.html')


# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     jobs = conn.execute('SELECT * FROM jobs ORDER BY posted_date DESC').fetchall()

#     jobs_with_counts = []
#     for job in jobs:
#         count = conn.execute(
#             'SELECT COUNT(*) FROM applications WHERE job_id = ?',
#             (job['id'],)
#         ).fetchone()[0]

#         job_dict = dict(job)
#         job_dict['applicant_count'] = count
#         jobs_with_counts.append(job_dict)

#     conn.close()
#     return render_template('admin_dashboard.html', jobs=jobs_with_counts,
#                            now=datetime.now().strftime('%Y-%m-%d'))


# @app.route('/admin/create_job', methods=('GET', 'POST'))
# def admin_create_job():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#         requirements = request.form['requirements']
#         deadline = request.form['deadline']

#         if not all([title, description, deadline]):
#             flash("Missing job title, description, or deadline.", 'error')
#             return render_template('admin_create_job.html')

#         conn = get_db_connection()
#         try:
#             conn.execute(
#                 'INSERT INTO jobs (title, description, requirements, deadline) VALUES (?, ?, ?, ?)',
#                 (title, description, requirements, deadline)
#             )
#             conn.commit()
#             flash(f"Job '{title}' posted successfully!", 'success')
#             return redirect(url_for('admin_dashboard'))
#         except Exception as e:
#             flash(f"Database error while creating job: {e}", 'error')
#             return render_template('admin_create_job.html')
#         finally:
#             conn.close()

#     return render_template('admin_create_job.html')


# @app.route('/admin/view_applicants/<int:job_id>')
# def admin_view_applicants(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = None
#     try:
#         conn = get_db_connection()
#         if not conn:
#             flash("Database connection error", 'error')
#             return redirect(url_for('admin_dashboard'))

#         job = conn.execute('SELECT title, requirements FROM jobs WHERE id = ?', (job_id,)).fetchone()
#         if not job:
#             conn.close()
#             flash("Job not found.", 'error')
#             return redirect(url_for('admin_dashboard'))

#         job_title = job['title']
#         job_requirements = job['requirements'] or ""

#         applicants = conn.execute('''
#             SELECT 
#                 c.id AS candidate_id, c.name, c.email, c.phone, c.address,
#                 c.resume_path, c.profile_image_path,
#                 a.applied_date, a.status,
#                 r.score AS test_score
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             LEFT JOIN test_results r ON a.candidate_id = r.candidate_id AND a.job_id = r.job_id
#             WHERE a.job_id = ?
#             ORDER BY a.applied_date DESC
#         ''', (job_id,)).fetchall()

#         scored_applicants = []

#         for applicant_row in applicants:
#             applicant = dict(applicant_row)

#             if applicant['resume_path']:
#                 full_resume_path = os.path.join(app.config['UPLOAD_FOLDER'], applicant['resume_path'])
#             else:
#                 full_resume_path = None

#             resume_text = extract_text_from_resume(full_resume_path)
#             score, explanation = score_resume(resume_text, job_requirements)

#             applicant['resume_score'] = score
#             applicant['score_explanation'] = explanation
#             scored_applicants.append(applicant)

#             try:
#                 update_conn = get_db_connection()
#                 if update_conn:
#                     update_conn.execute("""
#                         UPDATE applications 
#                         SET resume_score = ?, score_explanation = ? 
#                         WHERE candidate_id = ? AND job_id = ?
#                     """, (score, explanation, applicant['candidate_id'], job_id))
#                     update_conn.commit()
#                     update_conn.close()
#             except Exception as e:
#                 print(f"Error saving score for candidate {applicant['candidate_id']}: {e}")

#         return render_template('admin_view_applicants.html',
#                                job_title=job_title,
#                                applicants=scored_applicants,
#                                job_id=job_id)
#     except Exception as e:
#         print(f"Error in admin_view_applicants: {e}")
#         flash(f"Error loading applicants: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         if conn:
#             conn.close()


# @app.route('/admin/update_status/<int:job_id>/<int:candidate_id>/<string:action>')
# def admin_update_status(job_id, candidate_id, action):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     if action == 'accept':
#         new_status = 'Selected for Test'
#         subject = "Congratulations! You've been Shortlisted"
#         body = "Congratulations! Your application has been shortlisted. Please check the 'Tests' section on your portal for the next steps."
#     elif action == 'reject':
#         new_status = 'Rejected'
#         subject = "Update Regarding Your Application"
#         body = "Thank you for your interest. After careful consideration, we have decided not to move forward with your application at this time."
#     else:
#         flash("Invalid action.", 'error')
#         conn.close()
#         return redirect(url_for('admin_view_applicants', job_id=job_id))

#     try:
#         conn.execute("UPDATE applications SET status = ? WHERE candidate_id = ? AND job_id = ?", (new_status, candidate_id, job_id))
#         conn.commit()
#         send_message(candidate_id, job_id, subject, body)
#         flash(f"Candidate status updated to '{new_status}' and notification sent.", 'success')
#     except Exception as e:
#         flash(f"Error updating status: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('admin_view_applicants', job_id=job_id))


# @app.route('/admin/delete_application/<int:job_id>/<int:candidate_id>')
# def admin_delete_application(job_id, candidate_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     try:
#         conn.execute('DELETE FROM applications WHERE job_id = ? AND candidate_id = ?', (job_id, candidate_id))
#         conn.commit()
#         flash("Candidate application deleted successfully.", 'success')
#     except Exception as e:
#         flash(f"Error deleting application: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('admin_view_applicants', job_id=job_id))


# @app.route('/admin/delete_job/<int:job_id>')
# def admin_delete_job(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     try:
#         conn.execute('DELETE FROM applications WHERE job_id = ?', (job_id,))
#         conn.execute('DELETE FROM tests WHERE job_id = ?', (job_id,))
#         conn.execute('DELETE FROM test_results WHERE job_id = ?', (job_id,))
#         conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
#         conn.commit()
#         flash("Job posting and all associated data deleted successfully.", 'success')
#     except Exception as e:
#         flash(f"Error deleting job: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('admin_dashboard'))


# # --- ADMIN TEST MANAGEMENT ROUTES ---

# @app.route('/admin/manage_test/<int:job_id>', methods=['GET', 'POST'])
# def admin_manage_test(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#     existing_test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if request.method == 'POST':
#         title = request.form['title']
#         duration = request.form['duration']
#         start_date = request.form['start_date']
#         start_time = request.form['start_time']
#         questions_json = request.form['questions_json']

#         start_datetime_str = f"{start_date} {start_time}:00"

#         try:
#             if existing_test:
#                 conn.execute('''
#                     UPDATE tests SET title=?, questions_json=?, duration_minutes=?, start_time=? WHERE job_id=?
#                 ''', (title, questions_json, duration, start_datetime_str, job_id))
#                 flash("Manual test updated successfully!", 'success')
#             else:
#                 conn.execute('''
#                     INSERT INTO tests (job_id, title, questions_json, duration_minutes, start_time) VALUES (?, ?, ?, ?, ?)
#                 ''', (job_id, title, questions_json, duration, start_datetime_str))
#                 flash("Manual test created successfully!", 'success')
#             conn.commit()
#             return redirect(url_for('admin_dashboard'))
#         except Exception as e:
#             flash(f"Error managing test: {e}", 'error')
#         finally:
#             conn.close()

#     conn.close()
#     return render_template('admin_manage_test.html',
#                            job=job,
#                            test=existing_test,
#                            job_id=job_id)


# @app.route('/admin/create_ai_test/<int:job_id>', methods=['GET', 'POST'])
# def admin_create_ai_test(job_id):
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
#     test_link = None

#     if request.method == "POST":
#         test_name = request.form.get("test_name")
#         domain_text = request.form.get("domain_text")
#         question_type = request.form.get("question_type")
#         num_questions = int(request.form.get("num_questions", 5))
#         marks_per_question = int(request.form.get("marks_per_question", 10))
#         duration = int(request.form.get("duration", 30))
#         start_datetime = request.form.get("start_datetime")

#         start_datetime_db = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')

#         if question_type == 'softskills':
#             from softskills_routes import generate_softskills_questions
#             questions, error, test_link = generate_softskills_questions(
#                 role_context=domain_text,
#                 num_questions=num_questions,
#                 marks_per_question=marks_per_question,
#                 job_id=job_id
#             )
#         else:
#             questions, error = generate_ai_test(domain_text, num_questions)
#             if not error:
#                 test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)

#         if error:
#             flash(f"Test generation failed: {error}", 'error')
#         else:
#             questions_json = json.dumps(questions)

#             if question_type == 'softskills':
#                 title = f"Soft Skills Interview - {domain_text}"
#             elif question_type == 'audio_text':
#                 title = f"Scenario Test - {domain_text}"
#             else:
#                 title = f"Technical Test - {domain_text}"

#             existing_test = conn.execute("SELECT id FROM tests WHERE job_id = ?", (job_id,)).fetchone()

#             if existing_test:
#                 conn.execute("""
#                     UPDATE tests 
#                     SET title = ?, questions_json = ?, duration_minutes = ?, start_time = ?
#                     WHERE job_id = ?
#                 """, (title, questions_json, duration, start_datetime_db, job_id))
#             else:
#                 conn.execute("""
#                     INSERT INTO tests (job_id, title, questions_json, duration_minutes, start_time)
#                     VALUES (?, ?, ?, ?, ?)
#                 """, (job_id, title, questions_json, duration, start_datetime_db))

#             conn.commit()
#             flash("Test created successfully!", 'success')

#     conn.close()
#     return render_template("admin_create_ai_test.html", job=job, test_link=test_link, job_id=job_id)


# @app.route('/admin/send_test_to_selected/<int:job_id>', methods=['POST'])
# def admin_send_test_to_selected(job_id):
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     global RESUME_THRESHOLD

#     data = request.get_json()
#     test_link = data.get('test_link')

#     if not test_link:
#         return jsonify({'success': False, 'message': 'No test link provided'}), 400

#     conn = get_db_connection()

#     try:
#         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#         if not job:
#             return jsonify({'success': False, 'message': 'Job not found'}), 404

#         threshold = RESUME_THRESHOLD
#         print(f"Using threshold: {threshold}")

#         candidates = conn.execute("""
#             SELECT c.id, c.name, c.email, a.resume_score, a.status
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             WHERE a.job_id = ? AND a.resume_score >= ?
#             ORDER BY a.resume_score DESC
#         """, (job_id, threshold)).fetchall()

#         print(f"Found {len(candidates)} eligible candidates")

#         if not candidates:
#             return jsonify({
#                 'success': False,
#                 'message': f'No candidates found with resume score >= {threshold}'
#             }), 404

#         sent_count = 0
#         failed_count = 0
#         already_selected_count = 0
#         failed_details = []

#         for candidate in candidates:
#             try:
#                 if candidate['status'] == 'Selected for Test' or candidate['status'] == 'Test Completed':
#                     already_selected_count += 1
#                     print(f"⏭️ {candidate['name']} already has status: {candidate['status']}")
#                     continue

#                 success = send_test_link_email(
#                     candidate['email'],
#                     candidate['name'],
#                     job['title'],
#                     test_link
#                 )

#                 if success:
#                     conn.execute("""
#                         UPDATE applications 
#                         SET status = 'Selected for Test' 
#                         WHERE candidate_id = ? AND job_id = ?
#                     """, (candidate['id'], job_id))
#                     sent_count += 1
#                     print(f"✅ Selected {candidate['name']} for test and email sent")
#                 else:
#                     failed_count += 1
#                     failed_details.append(f"{candidate['name']} ({candidate['email']})")

#             except Exception as e:
#                 print(f"❌ Error for {candidate['name']}: {e}")
#                 failed_count += 1
#                 failed_details.append(f"{candidate['name']} - {str(e)[:50]}")

#         conn.commit()

#         message = f"✅ Selected for Test: {sent_count}, Failed: {failed_count}, Already Selected: {already_selected_count}"

#         return jsonify({
#             'success': True,
#             'message': message,
#             'sent_count': sent_count,
#             'failed_count': failed_count,
#             'already_selected_count': already_selected_count,
#             'total_found': len(candidates)
#         })

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @app.route('/admin/check_selected_candidates/<int:job_id>')
# def check_selected_candidates(job_id):
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     global RESUME_THRESHOLD

#     conn = get_db_connection()

#     try:
#         threshold = RESUME_THRESHOLD
#         print(f"Preview using threshold: {threshold}")

#         candidates = conn.execute("""
#             SELECT c.name, c.email, a.resume_score, a.status
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             WHERE a.job_id = ? AND a.resume_score >= ?
#             ORDER BY a.resume_score DESC
#         """, (job_id, threshold)).fetchall()

#         result = []
#         for c in candidates:
#             result.append({
#                 'name': c['name'],
#                 'email': c['email'],
#                 'score': c['resume_score'],
#                 'status': c['status']
#             })

#         return jsonify({
#             'success': True,
#             'threshold': threshold,
#             'total': len(result),
#             'candidates': result
#         })
#     except Exception as e:
#         print(f"Error in check_selected_candidates: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @app.route('/update_threshold', methods=['POST'])
# def update_threshold():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     global RESUME_THRESHOLD
#     new_threshold = request.form.get('threshold')

#     try:
#         RESUME_THRESHOLD = int(new_threshold)
#         flash(f"Resume threshold updated to {RESUME_THRESHOLD}", 'success')
#         print(f"Threshold updated to: {RESUME_THRESHOLD}")
#     except:
#         flash("Invalid threshold value", 'error')

#     return redirect(request.referrer or url_for('admin_dashboard'))


# # @app.route('/admin/view_test_results/<int:job_id>')
# # def admin_view_test_results(job_id):
# #     if session.get('user_type') != 'admin':
# #         flash("Unauthorized access.", 'warning')
# #         return redirect(url_for('admin_login'))

# #     conn = get_db_connection()
# #     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()

# #     results = conn.execute('''
# #         SELECT 
# #             c.id AS candidate_id, c.name, c.email, 
# #             r.score, r.submission_time, 
# #             a.status
# #         FROM test_results r
# #         JOIN candidates c ON r.candidate_id = c.id
# #         JOIN applications a ON r.candidate_id = a.candidate_id AND r.job_id = a.job_id
# #         WHERE r.job_id = ?
# #         ORDER BY r.score DESC
# #     ''', (job_id,)).fetchall()

# #     conn.close()

# #     return render_template('admin_view_test_results.html', job=job, results=results)

# @app.route('/admin/view_test_results/<int:job_id>')
# def admin_view_test_results(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()

#     # Query uses LEFT JOIN so it doesn't drop candidates who only have soft skills
#     results = conn.execute('''
#         SELECT 
#             c.id AS candidate_id, c.name, c.email, 
#             COALESCE(r.score, 0) AS score, 
#             COALESCE(r.submission_time, CURRENT_TIMESTAMP) AS submission_time, 
#             a.status
#         FROM applications a
#         JOIN candidates c ON a.candidate_id = c.id
#         LEFT JOIN test_results r ON a.candidate_id = r.candidate_id AND a.job_id = r.job_id
#         WHERE a.job_id = ? AND a.status = 'Test Completed'
#         ORDER BY submission_time DESC
#     ''', (job_id,)).fetchall()

#     conn.close()
#     return render_template('admin_view_test_results.html', job=job, results=results, job_id=job_id)



# import time

# @app.route('/api/submit_softskills/<int:job_id>', methods=['POST'])
# def api_submit_softskills(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     candidate_id = session['user_id']
#     conn = get_db_connection()

#     try:
#         # 1. Create the folder if it doesn't exist
#         upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)

#         # 2. Process and save each audio file
#         saved_count = 0
#         for key in request.files:
#             if key.startswith('audio_'):
#                 q_num = key.split('_')[1]
#                 audio_file = request.files[key]
#                 answer_text = request.form.get(f'answer_{q_num}', 'Audio Response')

#                 if audio_file.filename:
#                     # Generate a unique filename
#                     filename = f"cand_{candidate_id}_job_{job_id}_q{q_num}_{int(time.time())}.webm"
#                     filepath = os.path.join(upload_folder, filename)
#                     audio_file.save(filepath)

#                     # Insert into softskills_responses table
#                     conn.execute('''
#                         INSERT INTO softskills_responses
#                         (candidate_id, job_id, question_number, question_text, audio_path, answer_text)
#                         VALUES (?, ?, ?, ?, ?, ?)
#                     ''', (candidate_id, job_id, q_num, answer_text, filename, answer_text))
#                     saved_count += 1

#         # 3. CRITICAL FIX: Update the main applications table to 'Test Completed'
#         conn.execute("UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#                      (candidate_id, job_id))

#         # 4. CRITICAL FIX: Create an entry in test_results so the Recruiter's dashboard sees it
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results (candidate_id, job_id, score, submission_time)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

#         conn.commit()
#         return jsonify({'success': True, 'message': f'Successfully saved {saved_count} recordings.'})

#     except Exception as e:
#         print(f"Error saving softskills: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @app.route('/hr/all_applicants')
# def hr_all_applicants():
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     # Fetch all applicants with job and test info
#     applicants = conn.execute("""
#         SELECT 
#             c.name,
#             c.email,
#             j.title AS job_role,
#             a.status,
#             a.applied_date,
#             tr.score,
#             tr.submission_time
#         FROM applications a
#         JOIN candidates c ON a.candidate_id = c.id
#         JOIN jobs j ON a.job_id = j.id
#         LEFT JOIN test_results tr 
#             ON a.candidate_id = tr.candidate_id 
#             AND a.job_id = tr.job_id
#         ORDER BY a.applied_date DESC
#     """).fetchall()

#     conn.close()

#     return render_template('hr_all_applicants.html', applicants=applicants)


# @app.route('/admin/view_analysis')
# def admin_view_analysis():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     # 1. Applicant status breakdown
#     status_rows = conn.execute(
#         "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status ORDER BY cnt DESC"
#     ).fetchall()
#     status_labels = [r['status'] for r in status_rows]
#     status_counts = [r['cnt'] for r in status_rows]

#     # 2. Job role popularity (top 8)
#     job_rows = conn.execute("""
#         SELECT j.title, COUNT(a.id) as cnt
#         FROM applications a
#         JOIN jobs j ON a.job_id = j.id
#         GROUP BY j.title ORDER BY cnt DESC LIMIT 8
#     """).fetchall()
#     job_labels = [r['title'] for r in job_rows]
#     job_counts  = [r['cnt']   for r in job_rows]

#     # 3. Key summary numbers
#     total_applicants  = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
#     test_completed    = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Test Completed'").fetchone()[0]
#     selected_for_test = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Selected for Test'").fetchone()[0]
#     just_applied      = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Applied'").fetchone()[0]

#     # 4. Score distribution buckets
#     score_rows = conn.execute("SELECT score FROM test_results WHERE score IS NOT NULL").fetchall()
#     scores = [r['score'] for r in score_rows]
#     bucket_labels = ['0-20', '21-40', '41-60', '61-80', '81-100']
#     bucket_counts = [0, 0, 0, 0, 0]
#     for s in scores:
#         if   s <= 20:  bucket_counts[0] += 1
#         elif s <= 40:  bucket_counts[1] += 1
#         elif s <= 60:  bucket_counts[2] += 1
#         elif s <= 80:  bucket_counts[3] += 1
#         else:          bucket_counts[4] += 1

#     conn.close()

#     return render_template('admin_view_analysis.html',
#         status_labels     = json.dumps(status_labels),
#         status_counts     = json.dumps(status_counts),
#         job_labels        = json.dumps(job_labels),
#         job_counts        = json.dumps(job_counts),
#         score_labels      = json.dumps(bucket_labels),
#         score_counts      = json.dumps(bucket_counts),
#         total_applicants  = total_applicants,
#         test_completed    = test_completed,
#         selected_for_test = selected_for_test,
#         just_applied      = just_applied,
#     )


# # ============================================================
# # REPLACE the existing admin_view_past_tests route in app.py
# # (find the lines that say):
# #
# #   @app.route('/admin/view-past-tests')
# #   def admin_view_past_tests():
# #       return render_template('admin_view_past_tests.html')
# #
# # and replace with the block below:
# # ============================================================

# @app.route('/admin/view-past-tests')
# def admin_view_past_tests():
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()

#     # Fetch every job that has at least one candidate selected for test or who completed it
#     jobs = conn.execute("""
#         SELECT DISTINCT j.id, j.title
#         FROM jobs j
#         JOIN applications a ON a.job_id = j.id
#         WHERE a.status IN ('Selected for Test', 'Test Completed')
#         ORDER BY j.id DESC
#     """).fetchall()

#     jobs_map = {}
#     for job in jobs:
#         job_id = job['id']

#         # Build the test link for this job
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)

#         # Fetch all candidates for this job who were selected or completed
#         candidates = conn.execute("""
#             SELECT c.name, a.status
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             WHERE a.job_id = ? AND a.status IN ('Selected for Test', 'Test Completed')
#             ORDER BY a.applied_date ASC
#         """, (job_id,)).fetchall()

#         jobs_map[job_id] = {
#             'job_title': job['title'],
#             'test_link': test_link,
#             'candidates': [{'name': c['name'], 'status': c['status']} for c in candidates]
#         }

#     conn.close()
#     return render_template('admin_view_past_tests.html', jobs_map=jobs_map)




# # --- REGISTER SOFT SKILLS BLUEPRINT ---
# from softskills_routes import softskills_bp, register_db, create_softskills_table
# register_db(get_db_connection)
# app.register_blueprint(softskills_bp)

# if __name__ == '__main__':
#     with app.app_context():
#         create_softskills_table()
#     print(f"--- ADMIN TEST CREDENTIALS: {ADMIN_USERNAME} / admin123 ---")
#     print("Ensure GROQ_API_KEY is set as an environment variable.")
#     app.run(host='0.0.0.0', port=8000, debug=True)


























































































































import os
import sqlite3
import json
import base64
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from PIL import Image
from io import BytesIO
import time
import docx
import pdfplumber
import re
import cv2
import numpy as np
from groq import Groq


app = Flask(__name__)
app.secret_key = 'your_super_secret_key_hr_portal_2025'
DATABASE = 'hr_portal.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Resume scoring threshold
RESUME_THRESHOLD = 60

# Email configuration
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'shahjhalak0412@gmail.com'
app.config['MAIL_PASSWORD'] = 'vwrb tozs mcpe vwmm'
app.config['MAIL_DEFAULT_SENDER'] = 'shahjhalak0412@gmail.com'
app.config['MAIL_TIMEOUT'] = 10


mail = Mail(app)


def send_test_link_email(candidate_email, candidate_name, job_title, test_link):
    """Send test link email to a candidate"""
    try:
        print(f"📧 Attempting to send email to: {candidate_email}")
        print(f"   Name: {candidate_name}")
        print(f"   Job: {job_title}")
        print(f"   Link: {test_link}")

        msg = Message(
            subject=f"🎯 Test Invitation: {job_title}",
            recipients=[candidate_email]
        )

        msg.body = f"""
Dear {candidate_name},

Congratulations! Based on your resume screening, you have been selected for the next round - the online assessment for {job_title}.

Your Test Link: {test_link}

Important Instructions:
✅ Complete the test before the deadline
✅ Ensure stable internet connection
✅ Face verification will be required
✅ You cannot retake the test once submitted
✅ Find a quiet place with good lighting for face verification

Best of luck!
HR Team
        """

        msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; }}
        .button {{ display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Test Invitation</h2>
        </div>
        <div class="content">
            <p>Dear <strong>{candidate_name}</strong>,</p>
            <p>Congratulations! Based on your resume screening, you have been selected for the next round - the online assessment for <strong>{job_title}</strong>.</p>
            <p><strong>Your Test Link:</strong></p>
            <p style="text-align: center;">
                <a href="{test_link}" class="button">Start Your Test</a>
            </p>
            <p><strong>Important Instructions:</strong></p>
            <ul>
                <li>Complete the test before the deadline</li>
                <li>Ensure stable internet connection</li>
                <li>Face verification will be required</li>
                <li>You cannot retake the test once submitted</li>
            </ul>
            <p>Best of luck!</p>
            <p><strong>HR Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
        """

        mail.send(msg)
        print(f"✅ Email successfully sent to {candidate_name} at {candidate_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email to {candidate_email}: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False


def get_db_connection():
    """Get database connection with timeout and error handling"""
    try:
        conn = sqlite3.connect(DATABASE, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None


# Register Jinja filter for JSON loading in templates
def json_load(value):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}

app.jinja_env.filters['from_json'] = json_load

# Internal Admin credentials
ADMIN_USERNAME = 'hr_admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')


# Groq Client
GROQ_CLIENT = None
try:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY not found in environment variables.")
    else:
        GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)
        print("Groq API Client loaded successfully.")
except Exception as e:
    print(f"Groq Client failed to load: {e}")


# --- GENERAL UTILITY FUNCTIONS ---

def send_message(candidate_id, job_id, subject, body):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO messages (candidate_id, job_id, subject, body) VALUES (?, ?, ?, ?)',
            (candidate_id, job_id, subject, body)
        )
        conn.commit()
    except Exception as e:
        print(f"Error sending message: {e}")
    finally:
        conn.close()


def log_proctor_event(candidate_id, job_id, event_type, details=""):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
            (candidate_id, job_id, event_type, details)
        )
        conn.commit()
    except Exception as e:
        print(f"Error logging event: {e}")
    finally:
        conn.close()


# --- GROQ RESUME SCORING & AUTH UTILITY FUNCTIONS ---

def extract_text_from_resume(resume_path):
    """Extracts text from PDF or DOCX file."""
    if not resume_path or not os.path.exists(resume_path):
        return None

    file_extension = os.path.splitext(resume_path)[1].lower()
    text = ""

    try:
        if file_extension == '.pdf':
            with pdfplumber.open(resume_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif file_extension == '.docx':
            doc = docx.Document(resume_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        return None


def score_resume(resume_text, job_requirements_text):
    """Scores the resume against job requirements using Groq API (llama-3.3-70b-versatile)."""
    if not GROQ_CLIENT:
        return 0, "Groq API Client not initialised. Check GROQ_API_KEY environment variable."

    if not resume_text or not job_requirements_text:
        return 0, "Missing resume or job requirements."

    try:
        prompt = f"""You are an expert HR recruitment analyst. Your task is to objectively score a candidate's
resume against the provided job requirements. The score must reflect skill relevance,
experience level, and domain expertise. You MUST respond with a single JSON object and nothing else.

--- JOB REQUIREMENTS ---
{job_requirements_text}

--- CANDIDATE RESUME TEXT ---
{resume_text}

Based solely on the provided text, generate a score between 0 and 100 and a detailed, neutral rationale.
Respond ONLY with this exact JSON format (no markdown, no extra text):
{{"score": <integer 0-100>, "rationale": "<string>"}}"""

        completion = GROQ_CLIENT.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert HR resume scoring assistant. "
                        "Always respond with valid JSON only — no markdown fences, no prose, no explanation."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )

        response_text = completion.choices[0].message.content.strip()

        # Strip markdown fences if present
        if response_text.startswith("```"):
            response_text = re.sub(r"^```[a-zA-Z]*\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text).strip()

        result = json.loads(response_text)
        score = max(0, min(100, int(result.get('score', 0))))
        rationale = result.get('rationale', "Score generated by Groq AI.")
        return score, rationale

    except json.JSONDecodeError as e:
        return 0, f"Groq returned invalid JSON for resume scoring: {e}"
    except Exception as e:
        return 0, f"Error calling Groq API for resume scoring: {e}"


# FaceNet setup
try:
    from keras_facenet import FaceNet
    _facenet_embedder = FaceNet()
    _face_detector_proto = os.path.join("models", "deploy.prototxt")
    _face_detector_model = os.path.join("models", "res10_300x300_ssd_iter_140000_fp16.caffemodel")
    if os.path.exists(_face_detector_proto) and os.path.exists(_face_detector_model):
        _face_net_cv = cv2.dnn.readNetFromCaffe(_face_detector_proto, _face_detector_model)
        FACENET_READY = True
        print("FaceNet + OpenCV face detector loaded successfully.")
    else:
        FACENET_READY = False
        print("WARNING: Caffe face detector model files not found in ./models/. Face verification disabled.")
except Exception as _e:
    FACENET_READY = False
    print(f"WARNING: FaceNet not available ({_e}). Face verification disabled.")


def _cv2_extract_face(img_bgr, size=(160, 160)):
    """Detect and crop the largest confident face from a BGR image."""
    h, w = img_bgr.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(img_bgr, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
    )
    _face_net_cv.setInput(blob)
    detections = _face_net_cv.forward()
    if detections.shape[2] == 0:
        return None
    i = int(np.argmax(detections[0, 0, :, 2]))
    conf = float(detections[0, 0, i, 2])
    if conf < 0.5:
        return None
    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
    x1, y1, x2, y2 = box.astype(int)
    face_crop = img_bgr[max(0, y1):y2, max(0, x1):x2]
    if face_crop.size == 0:
        return None
    face_rgb = cv2.cvtColor(cv2.resize(face_crop, size), cv2.COLOR_BGR2RGB)
    return face_rgb


def _facenet_embedding(face_rgb):
    """Return an L2-normalised FaceNet embedding for a (160,160,3) RGB array."""
    emb = _facenet_embedder.embeddings(
        np.expand_dims(face_rgb.astype("float32"), axis=0)
    )[0]
    return emb / np.linalg.norm(emb)


def generate_ai_test(domain, num_questions):
    """Generate test questions using Groq AI"""
    if not GROQ_CLIENT:
        return None, "Groq client not initialized"

    try:
        prompt = f"""
Generate {num_questions} multiple choice questions about {domain}.
Each question must have 4 options with exactly one correct answer.

Return ONLY a JSON array in this format:
[
  {{
    "q": "Question text?",
    "type": "radio",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A",
    "category": "technical"
  }}
]
"""
        completion = GROQ_CLIENT.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        response_text = completion.choices[0].message.content.strip()

        if response_text.startswith('```'):
            response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        questions = json.loads(response_text)
        return questions, None

    except Exception as e:
        return None, str(e)


def verify_faces(stored_image_path, live_image_data_uri):
    """
    Compare a stored profile photo against a live webcam capture.
    Uses local FaceNet embeddings — no external API required.
    Falls back to a permissive pass if FaceNet is not available.
    """
    if not FACENET_READY:
        return True, "Face verification skipped (FaceNet not available)."

    full_stored_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_image_path)
    if not os.path.exists(full_stored_path):
        return False, "Reference photo not found in profile."

    try:
        stored_bgr = cv2.imread(full_stored_path)
        if stored_bgr is None:
            return False, "Could not read stored profile photo."
        stored_face = _cv2_extract_face(stored_bgr)
        if stored_face is None:
            return False, "No face detected in stored profile photo."

        _, encoded = live_image_data_uri.split(',', 1)
        live_bytes = base64.b64decode(encoded)
        live_pil = Image.open(BytesIO(live_bytes)).convert('RGB')
        live_bgr = cv2.cvtColor(np.array(live_pil), cv2.COLOR_RGB2BGR)
        live_face = _cv2_extract_face(live_bgr)
        if live_face is None:
            return False, "No face detected in live camera image. Ensure good lighting and look directly at the camera."

        stored_emb = _facenet_embedding(stored_face)
        live_emb = _facenet_embedding(live_face)
        distance = float(np.linalg.norm(stored_emb - live_emb))

        THRESHOLD = 0.55
        if distance < THRESHOLD:
            return True, f"Verification successful (distance={distance:.3f})."
        else:
            return False, f"Face mismatch (distance={distance:.3f}). Try better lighting or re-upload your profile photo."

    except Exception as e:
        return False, f"Verification error: {e}"


# --- GROQ: QUESTION GENERATION & TEST GRADING ---

def generate_assessment_json(test_name, domain_text, num_questions, question_type):
    """Generate test questions using Groq AI."""
    if not GROQ_CLIENT:
        return None, "Groq client not initialized. Please set the GROQ_API_KEY environment variable."

    try:
        if question_type == "audio":
            type_instruction = (
                "Create scenario-based questions that require a verbal/written response. "
                "Set 'type' to 'audio_text' for every question. "
                "Set 'options' to an empty array []. "
                "The 'answer' field should contain a sample ideal response."
            )
        else:
            type_instruction = (
                "Create multiple-choice questions (MCQ). "
                "Set 'type' to 'radio' for every question. "
                "Provide exactly 4 distinct strings in 'options'. "
                "The 'answer' field must exactly match one of the 4 options."
            )

        prompt = f"""You are an expert HR assessment creator.

Generate a recruitment test with the details below and return ONLY a valid JSON array — no markdown, no explanation, no extra text.

Test Name     : {test_name}
Topic / Domain: {domain_text}
Total Questions: {num_questions}
Question Type : {question_type}

Instructions:
{type_instruction}

Required JSON schema for every question object:
{{
  "q"      : "<question text>",
  "type"   : "<radio | audio_text>",
  "options": ["<opt1>", "<opt2>", "<opt3>", "<opt4>"],
  "answer" : "<correct answer or ideal response>"
}}

Return a JSON array of exactly {num_questions} question objects."""

        completion = GROQ_CLIENT.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional HR assessment generator. "
                        "Always respond with valid JSON only — no markdown fences, no prose."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        response_text = completion.choices[0].message.content.strip()

        if response_text.startswith("```"):
            response_text = re.sub(r"^```[a-zA-Z]*\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text).strip()

        questions = json.loads(response_text)

        if not isinstance(questions, list):
            return None, "Groq returned an unexpected format (expected a JSON array)."

        return questions, None

    except json.JSONDecodeError as e:
        return None, f"Groq returned invalid JSON: {e}"
    except Exception as e:
        return None, f"AI Question Generation failed: {str(e)}"


def grade_test_ai(test, submitted_answers):
    """
    Hybrid grader:
    - MCQ (radio): exact string match locally.
    - Scenario (audio_text): scored by Groq AI.
    """
    try:
        questions = json.loads(test['questions_json'])
        print(f"Grading test with {len(questions)} questions")
        print(f"Submitted answers: {submitted_answers}")
    except Exception as e:
        print(f"Error parsing questions: {e}")
        return 0, f"Could not parse test questions: {e}"

    if not questions:
        return 0, "No questions found in test."

    def _norm(s):
        """Normalize answer strings for comparison: strip, lowercase, collapse whitespace."""
        return " ".join(str(s).strip().lower().split()) if s else ""

    # Build a lookup: normalized question text → question object
    # This allows matching submitted answers even if question order differs
    q_by_text = {_norm(q.get("q", "")): q for q in questions}

    # Check if the form submitted a q_map (display_index → questions_json_index)
    # e.g., q_map = "2,0,4,1,3" means display q_1 is questions[2], q_2 is questions[0], etc.
    raw_q_map = submitted_answers.get("q_map", "")
    if isinstance(raw_q_map, list):
        raw_q_map = raw_q_map[0] if raw_q_map else ""

    q_map = None
    if raw_q_map:
        try:
            q_map = [int(x) for x in str(raw_q_map).split(",")]
        except Exception:
            q_map = None

    # Also build a lookup: normalized question text submitted per form key (q_N_text)
    # so we can match back to the correct question if q_map is absent
    q_text_by_key = {}
    for key, val in submitted_answers.items():
        if key.endswith("_text") and key.startswith("q_"):
            raw = val[0] if isinstance(val, list) else val
            q_text_by_key[key.replace("_text", "")] = _norm(raw)

    total_q = len(questions)
    points_earned = 0.0
    rationale_parts = []
    correct_count = 0
    audio_text_qs = []

    for idx, q in enumerate(questions):
        form_key = f"q_{idx + 1}"
        print(f"Looking for key: {form_key} in submitted answers")

        # If q_map was submitted, use it to find which form key corresponds to this question
        if q_map and idx < len(q_map):
            # q_map[display_position] = questions_json_index
            # We need: for this question at questions_json_index=idx, which display position?
            display_pos = None
            for disp, json_idx in enumerate(q_map):
                if json_idx == idx:
                    display_pos = disp + 1
                    break
            if display_pos is not None:
                form_key = f"q_{display_pos}"

        raw_answer = submitted_answers.get(form_key, "")

        # Flask's dict(request.form) wraps values in lists; unwrap safely
        if isinstance(raw_answer, list):
            raw_answer = raw_answer[0] if raw_answer else ""

        # Normalize: strip whitespace, collapse internal spaces, lowercase
        # This prevents mismatches caused by extra spaces or apostrophe differences
        def _norm(s):
            return " ".join(str(s).strip().lower().split()) if s else ""

        candidate_ans = _norm(raw_answer)
        correct_ans = _norm(q.get("answer", ""))

        q_type = q.get("type", "radio")

        print(f"Q{idx+1}: Type={q_type}, Candidate='{candidate_ans}', Correct='{correct_ans}'")

        if q_type == "radio":
            if candidate_ans and candidate_ans == correct_ans:
                points_earned += 1
                correct_count += 1
                rationale_parts.append(f"Q{idx+1}: Correct ✓")
                print(f"  ✅ Correct match!")
            else:
                if not candidate_ans:
                    rationale_parts.append(f"Q{idx+1}: No answer provided")
                    print(f"  ❌ No answer")
                else:
                    rationale_parts.append(
                        f"Q{idx+1}: Wrong (answered '{candidate_ans}', correct '{correct_ans}')"
                    )
                    print(f"  ❌ Wrong answer")
        else:
            audio_text_qs.append((idx, q, candidate_ans))

    print(f"MCQ Results: {correct_count}/{len([q for q in questions if q.get('type')=='radio'])} correct")

    if audio_text_qs and GROQ_CLIENT:
        try:
            batch_items = "\n\n".join([
                f"[Q{idx+1}]\nQuestion: {q['q']}\nIdeal answer: {q.get('answer','')}\nCandidate answer: {ans}"
                for idx, q, ans in audio_text_qs
            ])

            prompt = f"""You are grading written scenario answers.
For each question below, award a score from 0 to 10 based on relevance and quality vs the ideal answer.
Return ONLY a JSON array with one object per question, in order:
[{{"q": 1, "score": <0-10>, "comment": "<one sentence>"}}, ...]

{batch_items}"""

            completion = GROQ_CLIENT.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an exam evaluator. Reply with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
            )
            result_text = completion.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = re.sub(r"^```[a-zA-Z]*\n?", "", result_text)
                result_text = re.sub(r"\n?```$", "", result_text).strip()

            ai_scores = json.loads(result_text)

            for i, (idx, q, ans) in enumerate(audio_text_qs):
                raw = ai_scores[i] if i < len(ai_scores) else {}
                ai_pts = max(0, min(10, int(raw.get("score", 0))))
                points_earned += ai_pts / 10.0
                rationale_parts.append(
                    f"Q{idx+1} (scenario): {ai_pts}/10 — {raw.get('comment','')}"
                )

        except Exception as e:
            print(f"Groq grading error: {e}")
            for idx, q, ans in audio_text_qs:
                points_earned += 0.5
                rationale_parts.append(f"Q{idx+1} (scenario): AI grading failed, partial credit awarded.")

    elif audio_text_qs:
        for idx, q, ans in audio_text_qs:
            points_earned += 0.5
            rationale_parts.append(f"Q{idx+1} (scenario): Groq unavailable, partial credit awarded.")

    final_score = round((points_earned / total_q) * 100)
    final_score = max(0, min(100, final_score))
    rationale = " | ".join(rationale_parts)

    print(f"Final score: {final_score}% ({points_earned}/{total_q} points)")

    return final_score, rationale


# --- AUTHENTICATION & GLOBAL ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", 'info')
    return redirect(url_for('index'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- CANDIDATE ROUTES ---

@app.route('/signup', methods=('GET', 'POST'))
def candidate_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if not all([name, email, password]):
            flash("Missing required fields (Name, Email, Password).", 'error')
            return redirect(url_for('candidate_signup'))

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO candidates (name, email, password_hash) VALUES (?, ?, ?)',
                (name, email, generate_password_hash(password))
            )
            conn.commit()
            flash("Account created! Log in and complete your profile before applying.", 'success')
            return redirect(url_for('candidate_login'))
        except sqlite3.IntegrityError:
            flash("Email already registered.", 'error')
            return redirect(url_for('candidate_signup'))
        finally:
            conn.close()

    return render_template('candidate_signup.html')


@app.route('/login', methods=('GET', 'POST'))
def candidate_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM candidates WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_type'] = 'candidate'
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('candidate_jobs'))
        else:
            flash("Invalid email or password.", 'error')
            return render_template('candidate_login.html')

    return render_template('candidate_login.html')


@app.route('/candidate/profile', methods=('GET', 'POST'))
def candidate_profile():
    if session.get('user_type') != 'candidate':
        flash("Please log in to manage your profile.", 'warning')
        return redirect(url_for('candidate_login'))

    candidate_id = session['user_id']
    conn = get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        phone = request.form['phone']
        address = request.form['address']
        profile_image_data = request.form.get('profile_image_data')

        resume_path = candidate['resume_path']
        resume_file = request.files.get('resume')
        db_resume_path = resume_path
        db_image_path = candidate['profile_image_path']

        if resume_file and resume_file.filename != '':
            if resume_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], resume_path)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], resume_path))
            filename = f"resume_{candidate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume_file.filename}"
            resume_path_full = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(resume_path_full)
            db_resume_path = filename

        if profile_image_data:
            if db_image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], db_image_path)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], db_image_path))

            header, encoded = profile_image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            img = Image.open(BytesIO(image_bytes))

            image_filename = f"face_{candidate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpeg"
            image_path_full = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            img.save(image_path_full, 'jpeg')
            db_image_path = image_filename

        try:
            conn.execute(
                '''UPDATE candidates SET name=?, dob=?, phone=?, address=?, resume_path=?, profile_image_path=? WHERE id=?''',
                (name, dob, phone, address, db_resume_path, db_image_path, candidate_id)
            )
            conn.commit()
            flash("Profile updated successfully!", 'success')
            candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
        except Exception as e:
            flash(f"Error updating profile: {e}", 'error')
        finally:
            conn.close()

    return render_template('candidate_profile.html', candidate=candidate)


@app.route('/candidate/messages')
def candidate_messages():
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate_login'))

    candidate_id = session['user_id']
    conn = get_db_connection()

    messages = conn.execute('''
        SELECT 
            m.*, j.title AS job_title 
        FROM messages m 
        LEFT JOIN jobs j ON m.job_id = j.id
        WHERE m.candidate_id = ? 
        ORDER BY m.created_at DESC
    ''', (candidate_id,)).fetchall()

    conn.execute('UPDATE messages SET is_read = 1 WHERE candidate_id = ? AND is_read = 0', (candidate_id,))
    conn.commit()
    conn.close()

    return render_template('candidate_messages.html', messages=messages)


@app.route('/candidate/jobs')
def candidate_jobs():
    if session.get('user_type') != 'candidate':
        flash("Please log in to view job postings.", 'warning')
        return redirect(url_for('candidate_login'))

    candidate_id = session['user_id']
    conn = get_db_connection()

    candidate = conn.execute('SELECT resume_path, phone, address FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

    can_apply = all([
        candidate,
        candidate['resume_path'],
        candidate['phone'],
        candidate['address']
    ])

    if not can_apply:
        flash("Warning: You must complete all profile details (including resume, phone, and address) to apply.", 'warning')

    jobs = conn.execute('''
        SELECT j.*, a.status,
               t.questions_json AS test_questions_json
        FROM jobs j 
        LEFT JOIN applications a 
            ON j.id = a.job_id AND a.candidate_id = ?
        LEFT JOIN tests t
            ON j.id = t.job_id
        WHERE j.deadline >= date('now') 
        ORDER BY j.posted_date DESC
    ''', (candidate_id,)).fetchall()

    jobs_list = []
    for job in jobs:
        job_dict = dict(job)
        is_softskills = False
        try:
            qs = json.loads(job_dict.get('test_questions_json') or '[]')
            if qs and all(q.get('type') == 'audio_text' for q in qs):
                is_softskills = True
        except Exception:
            pass
        job_dict['is_softskills'] = is_softskills
        jobs_list.append(job_dict)

    conn.close()

    return render_template('candidate_jobs.html',
                           jobs=jobs_list,
                           can_apply=can_apply)


@app.route('/candidate/apply/<int:job_id>')
def candidate_apply(job_id):
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate_login'))

    candidate_id = session['user_id']
    conn = get_db_connection()
    candidate = conn.execute('SELECT resume_path, phone, address FROM candidates WHERE id = ?', (candidate_id,)).fetchone()

    if not all([candidate['resume_path'], candidate['phone'], candidate['address']]):
        flash("Application failed: Please complete all profile details before applying.", 'error')
        conn.close()
        return redirect(url_for('candidate_jobs'))

    try:
        conn.execute(
            'INSERT INTO applications (job_id, candidate_id, status) VALUES (?, ?, ?)',
            (job_id, candidate_id, 'Applied')
        )
        conn.commit()
        flash("Application submitted successfully!", 'success')
    except sqlite3.IntegrityError:
        flash("You have already applied for this job.", 'info')
    except Exception as e:
        flash(f"An error occurred during application: {e}", 'error')
    finally:
        conn.close()

    return redirect(url_for('candidate_jobs'))


# --- CANDIDATE TESTING/AUTH ROUTES ---

@app.route('/candidate/test/auth/<int:job_id>')
def candidate_auth_start(job_id):
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate_login'))

    candidate_id = session['user_id']
    conn = get_db_connection()
    candidate = conn.execute('SELECT profile_image_path FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    test = conn.execute('SELECT title, questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
    application = conn.execute('SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?', (job_id, candidate_id)).fetchone()
    conn.close()

    if not test or application['status'] != 'Selected for Test':
        flash("You are not authorized for this test.", 'error')
        return redirect(url_for('candidate_jobs'))

    if not candidate['profile_image_path']:
        flash("Profile image required for authentication. Please update your profile.", 'warning')
        return redirect(url_for('candidate_profile'))

    is_softskills = False
    try:
        title_lower = (test['title'] or '').lower()
        questions = json.loads(test['questions_json'] or '[]')
        if 'soft skill' in title_lower or 'soft skills' in title_lower:
            is_softskills = True
        elif questions and all(q.get('type') == 'audio_text' for q in questions):
            is_softskills = True
    except Exception:
        pass

    session[f'test_type_{job_id}'] = 'softskills' if is_softskills else 'standard'

    return render_template('candidate_auth_start.html', job_id=job_id, job_title=test['title'])


@app.route('/candidate/test/verify/<int:job_id>', methods=['POST'])
def candidate_test_verify(job_id):
    if session.get('user_type') != 'candidate':
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

    candidate_id = session['user_id']
    live_image_data_uri = request.json.get('image')

    conn = get_db_connection()
    candidate = conn.execute('SELECT profile_image_path FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    conn.close()

    stored_path = candidate['profile_image_path']

    if not stored_path or not live_image_data_uri:
        log_proctor_event(candidate_id, job_id, 'Face Auth Failed', 'Missing image data.')
        return jsonify({'success': False, 'message': 'Authentication failed: Missing image data.'}), 400

    is_verified, message = verify_faces(stored_path, live_image_data_uri)

    if is_verified:
        log_proctor_event(candidate_id, job_id, 'Face Auth Success', message)

        conn2 = get_db_connection()
        test_row = conn2.execute('SELECT title, questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
        conn2.close()

        is_softskills = False
        if test_row:
            try:
                title_lower = (test_row['title'] or '').lower()
                qs = json.loads(test_row['questions_json'] or '[]')
                if 'soft skill' in title_lower:
                    is_softskills = True
                elif qs and all(q.get('type') == 'audio_text' for q in qs):
                    is_softskills = True
            except Exception:
                pass

        if is_softskills:
            redirect_url = url_for('softskills.candidate_softskills_view', job_id=job_id)
        else:
            redirect_url = url_for('candidate_view_test', job_id=job_id)

        return jsonify({'success': True, 'message': 'Verification successful.', 'redirect': redirect_url})
    else:
        log_proctor_event(candidate_id, job_id, 'Face Auth Failed', message)
        return jsonify({'success': False, 'message': f'Verification failed. {message}'}), 401


@app.route('/candidate/test/<int:job_id>')
def candidate_view_test(job_id):
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate_login'))

    candidate_id = session['user_id']
    conn = get_db_connection()

    # Check if test already submitted
    existing_result = conn.execute(
        'SELECT * FROM test_results WHERE candidate_id = ? AND job_id = ?',
        (candidate_id, job_id)
    ).fetchone()

    if existing_result:
        conn.close()
        flash("You have already completed this test.", 'info')
        return redirect(url_for('candidate_jobs'))

    # Get test details
    test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
    application = conn.execute('SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?',
                               (job_id, candidate_id)).fetchone()
    conn.close()

    # Validate test access
    if not test:
        flash("Test not found. Please contact the administrator.", 'error')
        return redirect(url_for('candidate_jobs'))
    
    if not application or application['status'] != 'Selected for Test':
        flash("You are not authorized to take this test.", 'error')
        return redirect(url_for('candidate_jobs'))

    # Parse questions with better error handling
    questions = []
    try:
        if test['questions_json']:
            # Clean up any potential markdown formatting
            questions_json_str = test['questions_json'].strip()
            
            # Remove markdown code blocks if present
            if questions_json_str.startswith('```'):
                questions_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', questions_json_str)
                questions_json_str = re.sub(r'\n?```$', '', questions_json_str)
            
            questions = json.loads(questions_json_str)
            
            # Validate questions structure
            if not isinstance(questions, list):
                print(f"❌ Questions is not a list, got: {type(questions)}")
                questions = []
            elif len(questions) == 0:
                print("❌ Questions list is empty")
                flash("No questions found in the test. Please contact administrator.", 'error')
                return redirect(url_for('candidate_jobs'))
            else:
                print(f"✅ Successfully loaded {len(questions)} questions")
                print(f"First question: {questions[0].get('q', 'No question text')[:100]}")
        else:
            print("❌ No questions_json found in test")
            flash("Test questions are missing. Please contact administrator.", 'error')
            return redirect(url_for('candidate_jobs'))
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw JSON: {test['questions_json'][:200] if test['questions_json'] else 'None'}")
        flash("Error loading test questions. The test format is invalid. Please contact administrator.", 'error')
        return redirect(url_for('candidate_jobs'))
    except Exception as e:
        print(f"❌ Unexpected error parsing questions: {e}")
        flash("Error loading test questions. Please contact administrator.", 'error')
        return redirect(url_for('candidate_jobs'))

    # Handle start time - ensure it's valid
    can_start = True
    time_status = ""
    try:
        if test['start_time']:
            start_time = datetime.strptime(test['start_time'], '%Y-%m-%d %H:%M:%S')
            current_time = datetime.now()
            
            if current_time < start_time:
                time_status = f"Test opens on {start_time.strftime('%B %d, %Y at %I:%M %p')}"
                can_start = False
            else:
                time_status = f"Test duration: {test['duration_minutes']} minutes. Best of luck!"
                can_start = True
        else:
            time_status = f"Test duration: {test['duration_minutes']} minutes. You can start now!"
            can_start = True
    except (ValueError, TypeError) as e:
        print(f"⚠️ Error parsing start_time: {e}, allowing test to start")
        time_status = f"Test duration: {test['duration_minutes']} minutes."
        can_start = True

    # Debug information
    print(f"=== Test Debug Info ===")
    print(f"Job ID: {job_id}")
    print(f"Test Title: {test['title']}")
    print(f"Duration: {test['duration_minutes']} minutes")
    print(f"Start Time: {test['start_time']}")
    print(f"Number of Questions: {len(questions)}")
    print(f"Can Start: {can_start}")
    print(f"======================")

    return render_template('candidate_view_test.html',
                           test=test,
                           questions=questions,
                           time_status=time_status,
                           can_start=can_start,
                           job_id=job_id,
                           questions_json=json.dumps(questions))  # Pass JSON string to template

@app.route('/admin/test_email_config')
def test_email_config():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    try:
        msg = Message(
            subject="Test Email from HR Portal",
            recipients=['shahjhalak0412@gmail.com'],
            body="This is a test email to verify SMTP configuration is working."
        )
        mail.send(msg)
        return "✅ Test email sent successfully! Check your inbox."
    except Exception as e:
        return f"❌ Email failed: {str(e)}"



# ─────────────────────────────────────────────────────────────────────────────
# PATCH for app.py  →  replace your existing candidate_submit_test route
# with the version below.
#
# The key fix: when ANY submitted answer is a base64 data URI (audio recording),
# we route the whole submission through the softskills pipeline so the audio
# gets saved to disk and the admin can play it back later.
# ─────────────────────────────────────────────────────────────────────────────


# Abhi aj ka OG jo chlra 4-4-2026 ka 
@app.route('/candidate/submit_test/<int:job_id>', methods=['POST'])
def candidate_submit_test(job_id):
    if session.get('user_type') != 'candidate' or request.method != 'POST':
        return redirect(url_for('candidate_login'))

    candidate_id = session['user_id']
    print(f"=== SUBMIT TEST CALLED for job_id: {job_id} ===")

    conn = get_db_connection()
    test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

    if not test:
        conn.close()
        flash("Test configuration not found.", 'error')
        return redirect(url_for('candidate_jobs'))

    # Check duplicate submission
    existing_result = conn.execute(
        'SELECT id FROM test_results WHERE candidate_id = ? AND job_id = ?',
        (candidate_id, job_id)
    ).fetchone()
    if existing_result:
        conn.close()
        flash("You have already submitted this test.", 'error')
        return redirect(url_for('candidate_jobs'))

    submitted_answers = dict(request.form)

    # ── Detect if any answer contains a base64 audio recording ──────────────
    has_audio_answers = any(
        str(v[0] if isinstance(v, list) else v).startswith('data:')
        for v in submitted_answers.values()
    )

    if has_audio_answers:
        # Route through softskills pipeline to save audio files properly
        conn.close()
        print("  → Detected audio answers, routing to softskills submission")

        # Build a proper answer_N / audio_N mapping expected by softskills submit
        import re as _re
        upload_folder = os.path.join('uploads', 'softskills_audio')
        os.makedirs(upload_folder, exist_ok=True)

        # Fetch questions so we can store question_text
        questions = []
        try:
            questions = json.loads(test['questions_json'] or '[]')
        except Exception:
            pass

        conn2 = get_db_connection()
        try:
            # Guard: check softskills_responses too
            existing_ss = conn2.execute(
                'SELECT id FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
                (candidate_id, job_id)
            ).fetchone()
            if existing_ss:
                flash("You have already submitted this interview.", 'info')
                return redirect(url_for('candidate_jobs'))

            saved = 0
            for key, val in submitted_answers.items():
                m = _re.match(r'^q_(\d+)$', key)
                if not m:
                    continue
                question_num = int(m.group(1))
                raw_val = val[0] if isinstance(val, list) else val

                audio_path_db = None
                answer_text = ''

                if raw_val and raw_val.startswith('data:'):
                    try:
                        _, encoded = raw_val.split(',', 1)
                        audio_bytes = base64.b64decode(encoded)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
                        filepath = os.path.join(upload_folder, filename)
                        with open(filepath, 'wb') as fh:
                            fh.write(audio_bytes)
                        audio_path_db = filename
                        saved += 1
                        print(f"  ✅ Saved audio Q{question_num}: {filename} ({len(audio_bytes)} bytes)")
                    except Exception as e:
                        print(f"  ⚠️ Audio decode failed Q{question_num}: {e}")
                        answer_text = raw_val
                else:
                    answer_text = raw_val

                # Also grab optional typed text (q_N_text)
                text_fallback = submitted_answers.get(f'q_{question_num}_text', '')
                if isinstance(text_fallback, list):
                    text_fallback = text_fallback[0]
                if text_fallback and not answer_text:
                    answer_text = text_fallback

                q_text = ''
                if question_num <= len(questions):
                    q_text = questions[question_num - 1].get('q', '')

                conn2.execute('''
                    INSERT INTO softskills_responses
                    (candidate_id, job_id, question_number, question_text, audio_path, answer_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (candidate_id, job_id, question_num, q_text, audio_path_db, answer_text))

            conn2.execute(
                "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
                (candidate_id, job_id)
            )
            conn2.execute('''
                INSERT OR REPLACE INTO test_results
                (candidate_id, job_id, score, submitted_answers_json)
                VALUES (?, ?, ?, ?)
            ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills audio interview completed'})))
            conn2.commit()

            log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Audio interview, {saved} files saved")
            flash(f"Interview submitted successfully! Your {saved} audio recording(s) have been saved.", 'success')

        except Exception as e:
            print(f"❌ Error saving audio answers: {e}")
            import traceback; traceback.print_exc()
            flash(f"Error saving your answers: {e}", 'error')
        finally:
            conn2.close()

        return redirect(url_for('candidate_jobs'))

    # ── Standard MCQ / text test grading ────────────────────────────────────
    # score, rationale = grade_test_ai(test, submitted_answers)
    # log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Score: {score}")

    # try:
    #     conn.execute(
    #         '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json) VALUES (?, ?, ?, ?)''',
    #         (candidate_id, job_id, score, json.dumps(submitted_answers))
    #     )
    #     conn.execute(
    #         "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
    #         (candidate_id, job_id)
    #     )
    #     conn.commit()
    #     flash(f"Test submitted successfully! Final Score: {score}. Rationale: {rationale}", 'success')
    # except Exception as e:
    #     flash(f"Error saving test results: {e}", 'error')
    # finally:
    #     conn.close()

    # return redirect(url_for('candidate_jobs'))


   
    # ───────────── GROQ AI GRADING ─────────────────────────────────────────
    # Groq grades every MCQ answer. No local string matching — no index bugs.
    # The frontend sends ans_bundle_N (JSON with chosen + correct + question text).
    # If bundles are present we use them; otherwise we fall back to reading
    # questions from the DB and matching submitted q_N keys (0-based).
    # ────────────────────────────────────────────────────────────────────────

    print("=== GROQ AI GRADING ===")

    questions = []
    try:
        questions = json.loads(test['questions_json'] or '[]')
    except Exception as e:
        print("Error loading questions:", e)

    total_questions = len(questions)
    score_percent   = 0
    rationale       = ""

    if not GROQ_CLIENT:
        print("⚠️ Groq not available — falling back to 0-based local grading")
        # Simple local fallback (0-based keys)
        correct = 0
        for idx, q in enumerate(questions):
            raw = submitted_answers.get(f"q_{idx}", "")
            if isinstance(raw, list): raw = raw[0] if raw else ""
            norm = lambda s: " ".join(str(s).strip().lower().split())
            if norm(raw) == norm(q.get("answer", "")):
                correct += 1
        score_percent = round((correct / total_questions) * 100, 2) if total_questions else 0
        rationale = f"Local grading (Groq unavailable): {correct}/{total_questions} correct"

    else:
        # ── Build Q&A pairs from bundles (new template) OR from DB+form (old template) ──
        qa_pairs = []

        # Check if new bundle fields were submitted
        bundles = {}
        for key, val in submitted_answers.items():
            if key.startswith("ans_bundle_"):
                raw = val[0] if isinstance(val, list) else val
                try:
                    bundles[key] = json.loads(raw)
                except Exception:
                    pass

        if bundles:
            print(f"  Using bundle method — {len(bundles)} bundles")
            for i in range(len(bundles)):
                b = bundles.get(f"ans_bundle_{i}", {})
                qa_pairs.append({
                    "question": b.get("q", f"Question {i+1}"),
                    "options":  [],          # not needed for Groq grading
                    "correct":  b.get("correct", ""),
                    "chosen":   b.get("chosen", ""),
                    "type":     b.get("type", "radio"),
                })
        else:
            print("  Using 0-based key fallback")
            for idx, q in enumerate(questions):
                raw = submitted_answers.get(f"q_{idx}", "")
                if isinstance(raw, list): raw = raw[0] if raw else ""
                qa_pairs.append({
                    "question": q.get("q", f"Question {idx+1}"),
                    "options":  q.get("options", []),
                    "correct":  q.get("answer", ""),
                    "chosen":   raw,
                    "type":     q.get("type", "radio"),
                })

        if not qa_pairs:
            print("  ⚠️ No Q&A pairs found")
            score_percent = 0
            rationale = "No answers found to grade."
        else:
            # ── Send everything to Groq in one call ──────────────────────────
            qa_block = ""
            for i, pair in enumerate(qa_pairs):
                qa_block += f"""
Question {i+1}: {pair['question']}
Correct Answer: {pair['correct']}
Candidate's Answer: {pair['chosen'] or '(no answer given)'}
"""

            prompt = f"""You are an expert exam evaluator. Grade the following MCQ test answers.

For each question, compare the candidate's answer with the correct answer.
Consider the answer CORRECT if it conveys the same meaning, even with minor wording differences.
Consider it WRONG if blank or clearly different.

{qa_block}

Respond ONLY with a valid JSON array — no markdown, no explanation:
[
  {{"q": 1, "correct": true, "comment": "one short sentence"}},
  {{"q": 2, "correct": false, "comment": "one short sentence"}},
  ...
]
Return exactly {len(qa_pairs)} objects."""

            print(f"  Sending {len(qa_pairs)} questions to Groq for grading...")

            try:
                completion = GROQ_CLIENT.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a strict but fair exam grader. "
                                "Reply with valid JSON only — no markdown fences, no prose."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                )

                result_text = completion.choices[0].message.content.strip()
                if result_text.startswith("```"):
                    result_text = re.sub(r"^```[a-zA-Z]*\n?", "", result_text)
                    result_text = re.sub(r"\n?```$", "", result_text).strip()

                print(f"  Groq raw response: {result_text[:300]}")

                grading_results = json.loads(result_text)

                correct_count   = 0
                rationale_parts = []

                for i, result in enumerate(grading_results):
                    is_correct = result.get("correct", False)
                    comment    = result.get("comment", "")
                    if is_correct:
                        correct_count += 1
                        rationale_parts.append(f"Q{i+1}: ✓ {comment}")
                        print(f"  Q{i+1}: ✅ Correct")
                    else:
                        rationale_parts.append(f"Q{i+1}: ✗ {comment}")
                        print(f"  Q{i+1}: ❌ Wrong")

                score_percent = round((correct_count / len(qa_pairs)) * 100, 2)
                rationale     = " | ".join(rationale_parts)
                print(f"  Groq grading complete: {correct_count}/{len(qa_pairs)} correct → {score_percent}%")

            except Exception as e:
                print(f"  ❌ Groq grading error: {e}")
                # Last-resort local fallback
                correct = 0
                for pair in qa_pairs:
                    norm = lambda s: " ".join(str(s).strip().lower().split())
                    if norm(pair["chosen"]) == norm(pair["correct"]):
                        correct += 1
                score_percent = round((correct / len(qa_pairs)) * 100, 2) if qa_pairs else 0
                rationale = f"Local fallback (Groq error: {e}): {correct}/{len(qa_pairs)} correct"

    print(f"=== FINAL SCORE: {score_percent}% ===")

    # ── Save result ──────────────────────────────────────────────────────────
    try:
        conn.execute(
            '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json)
               VALUES (?, ?, ?, ?)''',
            (candidate_id, job_id, score_percent, json.dumps({"score": score_percent, "rationale": rationale}))
        )
        conn.execute(
            "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
            (candidate_id, job_id)
        )
        conn.commit()
        flash(f"Test submitted! Your score: {score_percent}%", 'success')

    except Exception as e:
        flash(f"Error saving test results: {e}", 'error')

    finally:
        conn.close()

    return redirect(url_for('candidate_jobs'))

# @app.route('/candidate/submit_test/<int:job_id>', methods=['POST'])
# def candidate_submit_test(job_id):
#     if session.get('user_type') != 'candidate' or request.method != 'POST':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     print(f"=== SUBMIT TEST CALLED for job_id: {job_id} ===")

#     print("Form data received:")
#     for key, value in request.form.items():
#         print(f"  {key}: {value}")

#     conn = get_db_connection()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if not test:
#         conn.close()
#         flash("Test configuration not found.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     submitted_answers = dict(request.form)

#     existing_result = conn.execute('SELECT id FROM test_results WHERE candidate_id = ? AND job_id = ?', (candidate_id, job_id)).fetchone()
#     if existing_result:
#         conn.close()
#         flash("You have already submitted this test.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     score, rationale = grade_test_ai(test, submitted_answers)
#     log_proctor_event(candidate_id, job_id, 'Test Submitted', f"Score: {score}")

#     try:
#         conn.execute(
#             '''INSERT INTO test_results (candidate_id, job_id, score, submitted_answers_json) VALUES (?, ?, ?, ?)''',
#             (candidate_id, job_id, score, json.dumps(submitted_answers))
#         )
#         conn.execute("UPDATE applications SET status = ? WHERE candidate_id = ? AND job_id = ?", ('Test Completed', candidate_id, job_id))
#         conn.commit()
#         flash(f"Test submitted successfully! Final Score: {score}. Rationale: {rationale}", 'success')
#     except Exception as e:
#         flash(f"Error saving test results: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))


# --- ADMIN ROUTES ---

@app.route('/admin/login', methods=('GET', 'POST'))
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['user_id'] = 'admin'
            session['user_type'] = 'admin'
            flash("Admin logged in successfully.", 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid Admin Credentials.", 'error')
            return render_template('admin_login.html')

    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY posted_date DESC').fetchall()

    jobs_with_counts = []
    for job in jobs:
        count = conn.execute(
            'SELECT COUNT(*) FROM applications WHERE job_id = ?',
            (job['id'],)
        ).fetchone()[0]

        job_dict = dict(job)
        job_dict['applicant_count'] = count
        jobs_with_counts.append(job_dict)

    conn.close()
    return render_template('admin_dashboard.html', jobs=jobs_with_counts,
                           now=datetime.now().strftime('%Y-%m-%d'))


@app.route('/admin/create_job', methods=('GET', 'POST'))
def admin_create_job():
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form['requirements']
        deadline = request.form['deadline']

        if not all([title, description, deadline]):
            flash("Missing job title, description, or deadline.", 'error')
            return render_template('admin_create_job.html')

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO jobs (title, description, requirements, deadline) VALUES (?, ?, ?, ?)',
                (title, description, requirements, deadline)
            )
            conn.commit()
            flash(f"Job '{title}' posted successfully!", 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Database error while creating job: {e}", 'error')
            return render_template('admin_create_job.html')
        finally:
            conn.close()

    return render_template('admin_create_job.html')


@app.route('/admin/view_applicants/<int:job_id>')
def admin_view_applicants(job_id):
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            flash("Database connection error", 'error')
            return redirect(url_for('admin_dashboard'))

        job = conn.execute('SELECT title, requirements FROM jobs WHERE id = ?', (job_id,)).fetchone()
        if not job:
            conn.close()
            flash("Job not found.", 'error')
            return redirect(url_for('admin_dashboard'))

        job_title = job['title']
        job_requirements = job['requirements'] or ""

        applicants = conn.execute('''
            SELECT 
                c.id AS candidate_id, c.name, c.email, c.phone, c.address,
                c.resume_path, c.profile_image_path,
                a.applied_date, a.status,
                r.score AS test_score
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN test_results r ON a.candidate_id = r.candidate_id AND a.job_id = r.job_id
            WHERE a.job_id = ?
            ORDER BY a.applied_date DESC
        ''', (job_id,)).fetchall()

        scored_applicants = []

        for applicant_row in applicants:
            applicant = dict(applicant_row)

            if applicant['resume_path']:
                full_resume_path = os.path.join(app.config['UPLOAD_FOLDER'], applicant['resume_path'])
            else:
                full_resume_path = None

            resume_text = extract_text_from_resume(full_resume_path)
            score, explanation = score_resume(resume_text, job_requirements)

            applicant['resume_score'] = score
            applicant['score_explanation'] = explanation
            scored_applicants.append(applicant)

            try:
                update_conn = get_db_connection()
                if update_conn:
                    update_conn.execute("""
                        UPDATE applications 
                        SET resume_score = ?, score_explanation = ? 
                        WHERE candidate_id = ? AND job_id = ?
                    """, (score, explanation, applicant['candidate_id'], job_id))
                    update_conn.commit()
                    update_conn.close()
            except Exception as e:
                print(f"Error saving score for candidate {applicant['candidate_id']}: {e}")

        return render_template('admin_view_applicants.html',
                               job_title=job_title,
                               applicants=scored_applicants,
                               job_id=job_id)
    except Exception as e:
        print(f"Error in admin_view_applicants: {e}")
        flash(f"Error loading applicants: {e}", 'error')
        return redirect(url_for('admin_dashboard'))
    finally:
        if conn:
            conn.close()


@app.route('/admin/update_status/<int:job_id>/<int:candidate_id>/<string:action>')
def admin_update_status(job_id, candidate_id, action):
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()

    if action == 'accept':
        new_status = 'Selected for Test'
        subject = "Congratulations! You've been Shortlisted"
        body = "Congratulations! Your application has been shortlisted. Please check the 'Tests' section on your portal for the next steps."
    elif action == 'reject':
        new_status = 'Rejected'
        subject = "Update Regarding Your Application"
        body = "Thank you for your interest. After careful consideration, we have decided not to move forward with your application at this time."
    else:
        flash("Invalid action.", 'error')
        conn.close()
        return redirect(url_for('admin_view_applicants', job_id=job_id))

    try:
        conn.execute("UPDATE applications SET status = ? WHERE candidate_id = ? AND job_id = ?", (new_status, candidate_id, job_id))
        conn.commit()
        send_message(candidate_id, job_id, subject, body)
        flash(f"Candidate status updated to '{new_status}' and notification sent.", 'success')
    except Exception as e:
        flash(f"Error updating status: {e}", 'error')
    finally:
        conn.close()

    return redirect(url_for('admin_view_applicants', job_id=job_id))


@app.route('/admin/delete_application/<int:job_id>/<int:candidate_id>')
def admin_delete_application(job_id, candidate_id):
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM applications WHERE job_id = ? AND candidate_id = ?', (job_id, candidate_id))
        conn.commit()
        flash("Candidate application deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting application: {e}", 'error')
    finally:
        conn.close()

    return redirect(url_for('admin_view_applicants', job_id=job_id))


@app.route('/admin/delete_job/<int:job_id>')
def admin_delete_job(job_id):
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM applications WHERE job_id = ?', (job_id,))
        conn.execute('DELETE FROM tests WHERE job_id = ?', (job_id,))
        conn.execute('DELETE FROM test_results WHERE job_id = ?', (job_id,))
        conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
        conn.commit()
        flash("Job posting and all associated data deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting job: {e}", 'error')
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))


# --- ADMIN TEST MANAGEMENT ROUTES ---

@app.route('/admin/manage_test/<int:job_id>', methods=['GET', 'POST'])
def admin_manage_test(job_id):
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
    existing_test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        duration = request.form['duration']
        start_date = request.form['start_date']
        start_time = request.form['start_time']
        questions_json = request.form['questions_json']

        start_datetime_str = f"{start_date} {start_time}:00"

        try:
            if existing_test:
                conn.execute('''
                    UPDATE tests SET title=?, questions_json=?, duration_minutes=?, start_time=? WHERE job_id=?
                ''', (title, questions_json, duration, start_datetime_str, job_id))
                flash("Manual test updated successfully!", 'success')
            else:
                conn.execute('''
                    INSERT INTO tests (job_id, title, questions_json, duration_minutes, start_time) VALUES (?, ?, ?, ?, ?)
                ''', (job_id, title, questions_json, duration, start_datetime_str))
                flash("Manual test created successfully!", 'success')
            conn.commit()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Error managing test: {e}", 'error')
        finally:
            conn.close()

    conn.close()
    return render_template('admin_manage_test.html',
                           job=job,
                           test=existing_test,
                           job_id=job_id)


@app.route('/admin/create_ai_test/<int:job_id>', methods=['GET', 'POST'])
def admin_create_ai_test(job_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    test_link = None

    if request.method == "POST":
        test_name = request.form.get("test_name")
        domain_text = request.form.get("domain_text")
        question_type = request.form.get("question_type")
        num_questions = int(request.form.get("num_questions", 5))
        marks_per_question = int(request.form.get("marks_per_question", 10))
        duration = int(request.form.get("duration", 30))
        start_datetime = request.form.get("start_datetime")

        start_datetime_db = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')

        if question_type == 'softskills':
            from softskills_routes import generate_softskills_questions
            questions, error, test_link = generate_softskills_questions(
                role_context=domain_text,
                num_questions=num_questions,
                marks_per_question=marks_per_question,
                job_id=job_id
            )
        else:
            questions, error = generate_ai_test(domain_text, num_questions)
            if not error:
                test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)

        if error:
            flash(f"Test generation failed: {error}", 'error')
        else:
            questions_json = json.dumps(questions)

            if question_type == 'softskills':
                title = f"Soft Skills Interview - {domain_text}"
            elif question_type == 'audio_text':
                title = f"Scenario Test - {domain_text}"
            else:
                title = f"Technical Test - {domain_text}"

            existing_test = conn.execute("SELECT id FROM tests WHERE job_id = ?", (job_id,)).fetchone()

            if existing_test:
                conn.execute("""
                    UPDATE tests 
                    SET title = ?, questions_json = ?, duration_minutes = ?, start_time = ?
                    WHERE job_id = ?
                """, (title, questions_json, duration, start_datetime_db, job_id))
            else:
                conn.execute("""
                    INSERT INTO tests (job_id, title, questions_json, duration_minutes, start_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (job_id, title, questions_json, duration, start_datetime_db))

            conn.commit()
            flash("Test created successfully!", 'success')

    conn.close()
    return render_template("admin_create_ai_test.html", job=job, test_link=test_link, job_id=job_id)


# @app.route('/admin/send_test_to_selected/<int:job_id>', methods=['POST'])
# def admin_send_test_to_selected(job_id):
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     global RESUME_THRESHOLD

#     data = request.get_json()
#     test_link = data.get('test_link')

#     if not test_link:
#         return jsonify({'success': False, 'message': 'No test link provided'}), 400

#     conn = get_db_connection()

#     try:
#         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#         if not job:
#             return jsonify({'success': False, 'message': 'Job not found'}), 404

#         threshold = RESUME_THRESHOLD
#         print(f"Using threshold: {threshold}")

#         candidates = conn.execute("""
#             SELECT c.id, c.name, c.email, a.resume_score, a.status
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             WHERE a.job_id = ? AND a.resume_score >= ?
#             ORDER BY a.resume_score DESC
#         """, (job_id, threshold)).fetchall()

#         print(f"Found {len(candidates)} eligible candidates")

#         if not candidates:
#             return jsonify({
#                 'success': False,
#                 'message': f'No candidates found with resume score >= {threshold}'
#             }), 404

#         sent_count = 0
#         failed_count = 0
#         already_selected_count = 0
#         failed_details = []

#         for candidate in candidates:
#             try:
#                 if candidate['status'] == 'Selected for Test' or candidate['status'] == 'Test Completed':
#                     already_selected_count += 1
#                     print(f"⏭️ {candidate['name']} already has status: {candidate['status']}")
#                     continue

#                 success = send_test_link_email(
#                     candidate['email'],
#                     candidate['name'],
#                     job['title'],
#                     test_link
#                 )

#                 if success:
#                     conn.execute("""
#                         UPDATE applications 
#                         SET status = 'Selected for Test' 
#                         WHERE candidate_id = ? AND job_id = ?
#                     """, (candidate['id'], job_id))
#                     sent_count += 1
#                     print(f"✅ Selected {candidate['name']} for test and email sent")
#                 else:
#                     failed_count += 1
#                     failed_details.append(f"{candidate['name']} ({candidate['email']})")

#             except Exception as e:
#                 print(f"❌ Error for {candidate['name']}: {e}")
#                 failed_count += 1
#                 failed_details.append(f"{candidate['name']} - {str(e)[:50]}")

#         conn.commit()

#         message = f"✅ Selected for Test: {sent_count}, Failed: {failed_count}, Already Selected: {already_selected_count}"

#         return jsonify({
#             'success': True,
#             'message': message,
#             'sent_count': sent_count,
#             'failed_count': failed_count,
#             'already_selected_count': already_selected_count,
#             'total_found': len(candidates)
#         })

#     except Exception as e:
#         print(f"Error: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


@app.route('/admin/send_test_to_selected/<int:job_id>', methods=['POST'])
def admin_send_test_to_selected(job_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    global RESUME_THRESHOLD

    # Safely parse JSON or Form data in case frontend headers are inconsistent
    data = request.get_json(silent=True) or {}
    test_link = data.get('test_link') or request.form.get('test_link')

    if not test_link:
        return jsonify({'success': False, 'message': 'No test link provided'}), 400

    conn = get_db_connection()

    try:
        job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404

        threshold = RESUME_THRESHOLD
        print(f"Using threshold: {threshold}")

        # Modified query: Fetch candidates who met the score threshold OR were manually selected
        candidates = conn.execute("""
            SELECT c.id, c.name, c.email, a.resume_score, a.status
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.job_id = ? AND (a.resume_score >= ? OR a.status = 'Selected for Test')
            ORDER BY a.resume_score DESC
        """, (job_id, threshold)).fetchall()

        print(f"Found {len(candidates)} eligible candidates")

        if not candidates:
            return jsonify({
                'success': False,
                'message': f'No eligible candidates found (Threshold: {threshold})'
            }), 404

        sent_count = 0
        failed_count = 0
        already_completed_count = 0
        failed_details = []

        for candidate in candidates:
            try:
                # FIX: We WANT to send emails to 'Selected for Test' candidates.
                # Only skip them if they have already finished the test entirely.
                if candidate['status'] == 'Test Completed':
                    already_completed_count += 1
                    print(f"⏭️ {candidate['name']} already completed test.")
                    continue

                success = send_test_link_email(
                    candidate['email'],
                    candidate['name'],
                    job['title'],
                    test_link
                )

                if success:
                    # Only update the DB if they weren't already in the "Selected" status
                    if candidate['status'] != 'Selected for Test':
                        conn.execute("""
                            UPDATE applications 
                            SET status = 'Selected for Test' 
                            WHERE candidate_id = ? AND job_id = ?
                        """, (candidate['id'], job_id))
                    sent_count += 1
                    print(f"✅ Selected {candidate['name']} for test and email sent")
                else:
                    failed_count += 1
                    failed_details.append(f"{candidate['name']} ({candidate['email']})")

            except Exception as e:
                print(f"❌ Error for {candidate['name']}: {e}")
                failed_count += 1
                failed_details.append(f"{candidate['name']} - {str(e)[:50]}")

        conn.commit()

        message = f"✅ Emails Sent: {sent_count}, Failed: {failed_count}, Already Completed: {already_completed_count}"

        return jsonify({
            'success': True,
            'message': message,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'already_completed_count': already_completed_count,
            'total_found': len(candidates)
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/admin/check_selected_candidates/<int:job_id>')
def check_selected_candidates(job_id):
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    global RESUME_THRESHOLD

    conn = get_db_connection()

    try:
        threshold = RESUME_THRESHOLD
        print(f"Preview using threshold: {threshold}")

        candidates = conn.execute("""
            SELECT c.name, c.email, a.resume_score, a.status
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.job_id = ? AND a.resume_score >= ?
            ORDER BY a.resume_score DESC
        """, (job_id, threshold)).fetchall()

        result = []
        for c in candidates:
            result.append({
                'name': c['name'],
                'email': c['email'],
                'score': c['resume_score'],
                'status': c['status']
            })

        return jsonify({
            'success': True,
            'threshold': threshold,
            'total': len(result),
            'candidates': result
        })
    except Exception as e:
        print(f"Error in check_selected_candidates: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/update_threshold', methods=['POST'])
def update_threshold():
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    global RESUME_THRESHOLD
    new_threshold = request.form.get('threshold')

    try:
        RESUME_THRESHOLD = int(new_threshold)
        flash(f"Resume threshold updated to {RESUME_THRESHOLD}", 'success')
        print(f"Threshold updated to: {RESUME_THRESHOLD}")
    except:
        flash("Invalid threshold value", 'error')

    return redirect(request.referrer or url_for('admin_dashboard'))


# @app.route('/admin/view_test_results/<int:job_id>')
# def admin_view_test_results(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = get_db_connection()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()

#     results = conn.execute('''
#         SELECT 
#             c.id AS candidate_id, c.name, c.email, 
#             r.score, r.submission_time, 
#             a.status
#         FROM test_results r
#         JOIN candidates c ON r.candidate_id = c.id
#         JOIN applications a ON r.candidate_id = a.candidate_id AND r.job_id = a.job_id
#         WHERE r.job_id = ?
#         ORDER BY r.score DESC
#     ''', (job_id,)).fetchall()

#     conn.close()

#     return render_template('admin_view_test_results.html', job=job, results=results)

@app.route('/admin/view_test_results/<int:job_id>')
def admin_view_test_results(job_id):
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()

    # Query uses LEFT JOIN so it doesn't drop candidates who only have soft skills
    results = conn.execute('''
        SELECT 
            c.id AS candidate_id, c.name, c.email, 
            COALESCE(r.score, 0) AS score, 
            COALESCE(r.submission_time, CURRENT_TIMESTAMP) AS submission_time, 
            a.status
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        LEFT JOIN test_results r ON a.candidate_id = r.candidate_id AND a.job_id = r.job_id
        WHERE a.job_id = ? AND a.status = 'Test Completed'
        ORDER BY submission_time DESC
    ''', (job_id,)).fetchall()

    conn.close()
    return render_template('admin_view_test_results.html', job=job, results=results, job_id=job_id)



import time

@app.route('/api/submit_softskills/<int:job_id>', methods=['POST'])
def api_submit_softskills(job_id):
    if session.get('user_type') != 'candidate':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    candidate_id = session['user_id']
    conn = get_db_connection()

    try:
        # 1. Create the folder if it doesn't exist
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'softskills_audio')
        os.makedirs(upload_folder, exist_ok=True)

        # 2. Process and save each audio file
        saved_count = 0
        for key in request.files:
            if key.startswith('audio_'):
                q_num = key.split('_')[1]
                audio_file = request.files[key]
                answer_text = request.form.get(f'answer_{q_num}', 'Audio Response')

                if audio_file.filename:
                    # Generate a unique filename
                    filename = f"cand_{candidate_id}_job_{job_id}_q{q_num}_{int(time.time())}.webm"
                    filepath = os.path.join(upload_folder, filename)
                    audio_file.save(filepath)

                    # Insert into softskills_responses table
                    conn.execute('''
                        INSERT INTO softskills_responses
                        (candidate_id, job_id, question_number, question_text, audio_path, answer_text)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (candidate_id, job_id, q_num, answer_text, filename, answer_text))
                    saved_count += 1

        # 3. CRITICAL FIX: Update the main applications table to 'Test Completed'
        conn.execute("UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
                     (candidate_id, job_id))

        # 4. CRITICAL FIX: Create an entry in test_results so the Recruiter's dashboard sees it
        conn.execute('''
            INSERT OR REPLACE INTO test_results (candidate_id, job_id, score, submission_time)
            VALUES (?, ?, ?, ?)
        ''', (candidate_id, job_id, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        return jsonify({'success': True, 'message': f'Successfully saved {saved_count} recordings.'})

    except Exception as e:
        print(f"Error saving softskills: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/hr/all_applicants')
def hr_all_applicants():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db_connection()

    # Fetch all applicants with job and test info
    applicants = conn.execute("""
        SELECT 
            c.name,
            c.email,
            j.title AS job_role,
            a.status,
            a.applied_date,
            tr.score,
            tr.submission_time
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
        LEFT JOIN test_results tr 
            ON a.candidate_id = tr.candidate_id 
            AND a.job_id = tr.job_id
        ORDER BY a.applied_date DESC
    """).fetchall()

    conn.close()

    return render_template('hr_all_applicants.html', applicants=applicants)


@app.route('/admin/view_analysis')
def admin_view_analysis():
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()

    # 1. Applicant status breakdown
    status_rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status ORDER BY cnt DESC"
    ).fetchall()
    status_labels = [r['status'] for r in status_rows]
    status_counts = [r['cnt'] for r in status_rows]

    # 2. Job role popularity (top 8)
    job_rows = conn.execute("""
        SELECT j.title, COUNT(a.id) as cnt
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        GROUP BY j.title ORDER BY cnt DESC LIMIT 8
    """).fetchall()
    job_labels = [r['title'] for r in job_rows]
    job_counts  = [r['cnt']   for r in job_rows]

    # 3. Key summary numbers
    total_applicants  = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    test_completed    = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Test Completed'").fetchone()[0]
    selected_for_test = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Selected for Test'").fetchone()[0]
    just_applied      = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Applied'").fetchone()[0]

    # 4. Score distribution buckets
    score_rows = conn.execute("SELECT score FROM test_results WHERE score IS NOT NULL").fetchall()
    scores = [r['score'] for r in score_rows]
    bucket_labels = ['0-20', '21-40', '41-60', '61-80', '81-100']
    bucket_counts = [0, 0, 0, 0, 0]
    for s in scores:
        if   s <= 20:  bucket_counts[0] += 1
        elif s <= 40:  bucket_counts[1] += 1
        elif s <= 60:  bucket_counts[2] += 1
        elif s <= 80:  bucket_counts[3] += 1
        else:          bucket_counts[4] += 1

    conn.close()

    return render_template('admin_view_analysis.html',
        status_labels     = json.dumps(status_labels),
        status_counts     = json.dumps(status_counts),
        job_labels        = json.dumps(job_labels),
        job_counts        = json.dumps(job_counts),
        score_labels      = json.dumps(bucket_labels),
        score_counts      = json.dumps(bucket_counts),
        total_applicants  = total_applicants,
        test_completed    = test_completed,
        selected_for_test = selected_for_test,
        just_applied      = just_applied,
    )


# ============================================================
# REPLACE the existing admin_view_past_tests route in app.py
# (find the lines that say):
#
#   @app.route('/admin/view-past-tests')
#   def admin_view_past_tests():
#       return render_template('admin_view_past_tests.html')
#
# and replace with the block below:
# ============================================================

@app.route('/admin/view-past-tests')
def admin_view_past_tests():
    if session.get('user_type') != 'admin':
        flash("Unauthorized access.", 'warning')
        return redirect(url_for('admin_login'))

    conn = get_db_connection()

    # Fetch every job that has at least one candidate selected for test or who completed it
    jobs = conn.execute("""
        SELECT DISTINCT j.id, j.title
        FROM jobs j
        JOIN applications a ON a.job_id = j.id
        WHERE a.status IN ('Selected for Test', 'Test Completed')
        ORDER BY j.id DESC
    """).fetchall()

    jobs_map = {}
    for job in jobs:
        job_id = job['id']

        # Build the test link for this job
        test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)

        # Fetch all candidates for this job who were selected or completed
        candidates = conn.execute("""
            SELECT c.name, a.status
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.job_id = ? AND a.status IN ('Selected for Test', 'Test Completed')
            ORDER BY a.applied_date ASC
        """, (job_id,)).fetchall()

        jobs_map[job_id] = {
            'job_title': job['title'],
            'test_link': test_link,
            'candidates': [{'name': c['name'], 'status': c['status']} for c in candidates]
        }

    conn.close()
    return render_template('admin_view_past_tests.html', jobs_map=jobs_map)




# --- REGISTER SOFT SKILLS BLUEPRINT ---
from softskills_routes import softskills_bp, register_db, create_softskills_table
register_db(get_db_connection)
app.register_blueprint(softskills_bp)

if __name__ == '__main__':
    with app.app_context():
        create_softskills_table()
    print(f"--- ADMIN TEST CREDENTIALS: {ADMIN_USERNAME} / admin123 ---")
    print("Ensure GROQ_API_KEY is set as an environment variable.")
    app.run(host='0.0.0.0', port=8000, debug=True)