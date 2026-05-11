# # """
# # softskills_routes.py
# # Handles:
# #   - AI question generation  (Groq)
# #   - Candidate interview view
# #   - Recording submission + evaluation pipeline
# #       * AssemblyAI  → speech-to-text + fluency metrics
# #       * LanguageTool → grammar / spelling errors
# #       * Groq AI      → confidence / relevance / tone scoring
# #   - Admin results view
# # """

# # import os, json, re, time, math, requests, tempfile
# # from flask import (Blueprint, render_template, request, redirect,
# #                    url_for, session, flash, jsonify)
# # from datetime import datetime
# # from groq import Groq

# # softskills_bp = Blueprint('softskills', __name__)

# # # ------------------------------------------------------------------ #
# # #  CLIENTS                                                             #
# # # ------------------------------------------------------------------ #
# # GROQ_CLIENT = None
# # try:
# #     _key = os.getenv("GROQ_API_KEY")
# #     if _key:
# #         GROQ_CLIENT = Groq(api_key=_key)
# # except Exception as e:
# #     print(f"Softskills: Groq client failed: {e}")

# # ASSEMBLYAI_KEY   = os.getenv("ASSEMBLYAI_API_KEY", "")
# # LANGUAGETOOL_URL = "https://api.languagetoolplus.com/v2/check"   # free tier works
# # LT_API_KEY       = os.getenv("LANGUAGETOOL_API_KEY", "")         # optional, works without

# # # ------------------------------------------------------------------ #
# # #  DB helper (imported from main app at registration time)           #
# # # ------------------------------------------------------------------ #
# # _get_db = None   # set via register_db(fn) below

# # def register_db(fn):
# #     global _get_db
# #     _get_db = fn

# # def db():
# #     return _get_db()

# # # ------------------------------------------------------------------ #
# # #  QUESTION GENERATION                                                #
# # # ------------------------------------------------------------------ #
# # SOFT_SKILLS_SYSTEM = """You are an expert HR interviewer creating scenario-based spoken interview questions.
# # Questions must require a verbal, conversational answer — NOT multiple choice.
# # Focus on: communication, confidence, teamwork, conflict resolution, leadership, self-awareness.
# # Return ONLY a valid JSON array. No markdown fences, no prose."""

# # def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
# #     if not GROQ_CLIENT:
# #         return None, "Groq client not available."

# #     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# # Each question must:
# # - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# # - Require 60-90 seconds to answer verbally
# # - Test a different soft skill

# # Default marks per question: {marks_per_question}

# # Return a JSON array:
# # [
# #   {{
# #     "q": "<full question text>",
# #     "type": "audio_text",
# #     "skill": "<skill being tested e.g. communication>",
# #     "marks": {marks_per_question},
# #     "options": [],
# #     "answer": "<ideal answer keywords/themes for evaluation>"
# #   }}
# # ]"""

# #     try:
# #         resp = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
# #                 {"role": "user",   "content": prompt}
# #             ],
# #             temperature=0.6,
# #         )
# #         text = resp.choices[0].message.content.strip()
# #         if text.startswith("```"):
# #             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
# #             text = re.sub(r"\n?```$", "", text).strip()
# #         questions = json.loads(text)
# #         if not isinstance(questions, list):
# #             return None, "Unexpected format from Groq."
# #         return questions, None
# #     except Exception as e:
# #         return None, f"Question generation failed: {e}"

# # # ------------------------------------------------------------------ #
# # #  ASSEMBLYAI — speech to text + fluency                              #
# # # ------------------------------------------------------------------ #
# # def transcribe_with_assemblyai(audio_path: str) -> dict:
# #     """Upload audio file to AssemblyAI, poll for result, return metrics."""
# #     base = {"transcript": "", "filler_count": 0, "pause_count": 0,
# #             "words_per_minute": 0, "confidence": 0.0, "error": None}

# #     if not ASSEMBLYAI_KEY:
# #         base["error"] = "ASSEMBLYAI_API_KEY not set"
# #         return base

# #     headers = {"authorization": ASSEMBLYAI_KEY, "content-type": "application/json"}

# #     try:
# #         # 1. Upload file
# #         with open(audio_path, "rb") as f:
# #             up = requests.post("https://api.assemblyai.com/v2/upload",
# #                                headers={"authorization": ASSEMBLYAI_KEY},
# #                                data=f, timeout=60)
# #         upload_url = up.json()["upload_url"]

# #         # 2. Submit transcription with IAB + auto_chapters disabled, but keep disfluencies
# #         payload = {
# #             "audio_url": upload_url,
# #             "disfluencies": True,       # keeps uh, um in transcript
# #             "auto_highlights": True,    # key phrase extraction
# #             "punctuate": True,
# #             "format_text": True,
# #         }
# #         job = requests.post("https://api.assemblyai.com/v2/transcript",
# #                             headers=headers, json=payload, timeout=30).json()
# #         job_id = job["id"]

# #         # 3. Poll (max 120s)
# #         for _ in range(60):
# #             time.sleep(2)
# #             result = requests.get(f"https://api.assemblyai.com/v2/transcript/{job_id}",
# #                                   headers=headers, timeout=15).json()
# #             if result["status"] == "completed":
# #                 break
# #             if result["status"] == "error":
# #                 base["error"] = result.get("error", "AssemblyAI error")
# #                 return base

# #         transcript_text = result.get("text") or ""
# #         words           = result.get("words") or []
# #         duration_sec    = (result.get("audio_duration") or 1)

# #         # Words per minute
# #         wpm = round(len(words) / (duration_sec / 60)) if duration_sec > 0 else 0

# #         # Filler word count (uh, um, like, you know, basically)
# #         filler_re = re.compile(r'\b(uh+|um+|uhm|like|you know|basically|so|right|okay)\b', re.I)
# #         filler_count = len(filler_re.findall(transcript_text))

# #         # Long pauses (gaps > 1.5s between consecutive words)
# #         pause_count = 0
# #         for i in range(1, len(words)):
# #             gap = (words[i].get("start", 0) - words[i-1].get("end", 0)) / 1000.0
# #             if gap > 1.5:
# #                 pause_count += 1

# #         # Average word confidence
# #         confidences = [w.get("confidence", 0) for w in words if "confidence" in w]
# #         avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

# #         return {
# #             "transcript":    transcript_text,
# #             "filler_count":  filler_count,
# #             "pause_count":   pause_count,
# #             "words_per_minute": wpm,
# #             "confidence":    avg_conf,
# #             "error":         None,
# #         }

# #     except Exception as e:
# #         base["error"] = str(e)
# #         return base

# # # ------------------------------------------------------------------ #
# # #  LANGUAGETOOL — grammar check                                        #
# # # ------------------------------------------------------------------ #
# # def check_grammar(text: str) -> dict:
# #     """Return count of grammar/spelling/style errors + list of issues."""
# #     base = {"error_count": 0, "errors": [], "error": None}
# #     if not text or len(text.strip()) < 10:
# #         return base
# #     try:
# #         params = {
# #             "text": text, "language": "en-US",
# #             "enabledOnly": "false",
# #         }
# #         if LT_API_KEY:
# #             params["apiKey"] = LT_API_KEY

# #         resp = requests.post(LANGUAGETOOL_URL, data=params, timeout=20)
# #         matches = resp.json().get("matches", [])
# #         errors = [
# #             {
# #                 "message": m.get("message", ""),
# #                 "context": m.get("context", {}).get("text", ""),
# #                 "rule":    m.get("rule", {}).get("issueType", ""),
# #             }
# #             for m in matches[:10]   # cap at 10 for display
# #         ]
# #         return {"error_count": len(matches), "errors": errors, "error": None}
# #     except Exception as e:
# #         base["error"] = str(e)
# #         return base

# # # ------------------------------------------------------------------ #
# # #  GROQ — confidence / relevance / tone scoring                        #
# # # ------------------------------------------------------------------ #
# # def score_answer_with_groq(question: str, ideal_themes: str, transcript: str,
# #                             fluency_metrics: dict) -> dict:
# #     """Ask Groq to score confidence, relevance, tone and give explanation."""
# #     base = {"confidence": 50, "relevance": 50, "tone": 50,
# #             "positivity": 50, "explanation": "AI scoring unavailable."}

# #     if not GROQ_CLIENT or not transcript:
# #         return base

# #     prompt = f"""You are an expert HR assessor scoring a spoken interview answer.

# # Question: {question}
# # Ideal answer themes: {ideal_themes}
# # Candidate transcript: {transcript}
# # Fluency metrics: WPM={fluency_metrics.get('words_per_minute',0)}, fillers={fluency_metrics.get('filler_count',0)}, long pauses={fluency_metrics.get('pause_count',0)}

# # Score each dimension from 0-100:
# # - confidence: Does the candidate sound sure and assertive?
# # - relevance: Does the answer address the question and ideal themes?
# # - tone: Is the tone professional and appropriate?
# # - positivity: Is the candidate's attitude positive and constructive?

# # Return ONLY valid JSON:
# # {{
# #   "confidence": <int>,
# #   "relevance": <int>,
# #   "tone": <int>,
# #   "positivity": <int>,
# #   "explanation": "<2-3 sentences explaining the evaluation>"
# # }}"""

# #     try:
# #         resp = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {"role": "system", "content": "You are an HR evaluation expert. Reply with valid JSON only."},
# #                 {"role": "user",   "content": prompt}
# #             ],
# #             temperature=0,
# #         )
# #         text = resp.choices[0].message.content.strip()
# #         if text.startswith("```"):
# #             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
# #             text = re.sub(r"\n?```$", "", text).strip()
# #         result = json.loads(text)
# #         return {
# #             "confidence":  max(0, min(100, int(result.get("confidence",  50)))),
# #             "relevance":   max(0, min(100, int(result.get("relevance",   50)))),
# #             "tone":        max(0, min(100, int(result.get("tone",        50)))),
# #             "positivity":  max(0, min(100, int(result.get("positivity",  50)))),
# #             "explanation": result.get("explanation", ""),
# #         }
# #     except Exception as e:
# #         base["explanation"] = f"AI scoring error: {e}"
# #         return base

# # # ------------------------------------------------------------------ #
# # #  SCORING AGGREGATION                                                 #
# # # ------------------------------------------------------------------ #
# # def compute_fluency_score(metrics: dict) -> int:
# #     """Convert raw fluency metrics to a 0-100 score."""
# #     wpm        = metrics.get("words_per_minute", 0)
# #     fillers    = metrics.get("filler_count", 0)
# #     pauses     = metrics.get("pause_count", 0)
# #     conf       = metrics.get("confidence", 0.5) * 100   # 0-100

# #     # WPM score: ideal 120-160 wpm for spoken English
# #     if   wpm == 0:      wpm_score = 20
# #     elif wpm < 80:      wpm_score = 50
# #     elif wpm < 120:     wpm_score = 75
# #     elif wpm <= 170:    wpm_score = 100
# #     else:               wpm_score = 70   # too fast

# #     # Penalty: each filler -3pts, each long pause -5pts
# #     penalty = min(50, fillers * 3 + pauses * 5)
# #     raw = (wpm_score * 0.4) + (conf * 0.4) - penalty * 0.2
# #     return max(0, min(100, round(raw)))

# # def compute_grammar_score(grammar: dict) -> int:
# #     errors = grammar.get("error_count", 0)
# #     if   errors == 0: return 100
# #     elif errors <= 2: return 85
# #     elif errors <= 5: return 65
# #     elif errors <= 10: return 45
# #     else:              return 25

# # def aggregate_scores(question_results: list, questions: list) -> dict:
# #     """Average all per-question scores into weighted totals using marks per question."""
# #     n = len(question_results)
# #     if n == 0:
# #         return {"fluency": 0, "grammar": 0, "confidence": 0, "relevance": 0, "overall": 0,
# #                 "total_marks": 0, "marks_obtained": 0}

# #     # Total possible marks
# #     total_marks = sum(int(q.get('marks', 5)) for q in questions) if questions else n * 5

# #     def avg(key):
# #         return round(sum(q.get(key, 0) for q in question_results) / n)

# #     fluency    = avg("fluency_score")
# #     grammar    = avg("grammar_score")
# #     confidence = avg("confidence_score")
# #     relevance  = avg("relevance_score")

# #     # Marks obtained = weighted by per-question marks
# #     marks_obtained = 0
# #     for i, qr in enumerate(question_results):
# #         q_marks  = int(questions[i].get('marks', 5)) if i < len(questions) else 5
# #         # Average of 4 dimensions as 0-1 ratio, multiplied by question marks
# #         ratio = (qr.get('fluency_score', 0) + qr.get('grammar_score', 0) +
# #                  qr.get('confidence_score', 0) + qr.get('relevance_score', 0)) / 400.0
# #         marks_obtained += round(ratio * q_marks, 2)

# #     overall = round((marks_obtained / total_marks) * 100) if total_marks > 0 else 0
# #     overall = max(0, min(100, overall))

# #     return {
# #         "fluency":        fluency,
# #         "grammar":        grammar,
# #         "confidence":     confidence,
# #         "relevance":      relevance,
# #         "overall":        overall,
# #         "total_marks":    total_marks,
# #         "marks_obtained": round(marks_obtained, 1),
# #     }

# # # ------------------------------------------------------------------ #
# # #  ROUTES                                                              #
# # # ------------------------------------------------------------------ #

# # @softskills_bp.route('/candidate/softskills/test/<int:job_id>')
# # def candidate_softskills_view(job_id):
# #     if session.get('user_type') != 'candidate':
# #         return redirect(url_for('candidate_login'))

# #     candidate_id = session['user_id']
# #     conn = db()
# #     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
# #     app_row = conn.execute(
# #         'SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?',
# #         (job_id, candidate_id)
# #     ).fetchone()
# #     already = conn.execute(
# #         'SELECT id FROM softskills_results WHERE job_id = ? AND candidate_id = ?',
# #         (job_id, candidate_id)
# #     ).fetchone()
# #     conn.close()

# #     if not test or not app_row or app_row['status'] != 'Selected for Test':
# #         flash("Not authorised for this interview.", 'error')
# #         return redirect(url_for('candidate_jobs'))

# #     if already:
# #         flash("You have already completed this soft skills interview.", 'info')
# #         return redirect(url_for('candidate_jobs'))

# #     questions = json.loads(test['questions_json']) if test['questions_json'] else []
# #     if not questions:
# #         flash("No questions configured for this interview.", 'error')
# #         return redirect(url_for('candidate_jobs'))

# #     return render_template('candidate_softskills_test.html',
# #                            test=test, questions=questions, job_id=job_id)


# # @softskills_bp.route('/candidate/softskills/submit/<int:job_id>', methods=['POST'])
# # def candidate_submit_softskills(job_id):
# #     if session.get('user_type') != 'candidate':
# #         return redirect(url_for('candidate_login'))

# #     candidate_id = session['user_id']
# #     conn = db()
# #     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

# #     if not test:
# #         conn.close()
# #         flash("Test not found.", 'error')
# #         return redirect(url_for('candidate_jobs'))

# #     questions  = json.loads(test['questions_json'])
# #     upload_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
# #     os.makedirs(upload_dir, exist_ok=True)

# #     question_results = []

# #     for idx, q in enumerate(questions):
# #         file_key = f"answer_{idx + 1}"
# #         audio_file = request.files.get(file_key)

# #         q_result = {
# #             "question":      q.get("q", ""),
# #             "skill":         q.get("skill", ""),
# #             "marks":         q.get("marks", 10),
# #             "transcript":    "",
# #             "fluency_score": 50,
# #             "grammar_score": 50,
# #             "confidence_score": 50,
# #             "relevance_score":  50,
# #             "filler_words":  0,
# #             "pauses":        0,
# #             "grammar_errors": 0,
# #             "explanation":   "No recording submitted.",
# #             "recording_path": None,   # ← stored so admin can play it back
# #         }

# #         if audio_file and audio_file.filename:
# #             save_path = os.path.join(upload_dir, f"q{idx+1}.webm")
# #             audio_file.save(save_path)

# #             # Store relative path for later playback
# #             relative_path = os.path.join('softskills', str(job_id), str(candidate_id), f"q{idx+1}.webm")
# #             q_result["recording_path"] = relative_path

# #             # 1. Speech-to-text + fluency (AssemblyAI)
# #             fluency_data = transcribe_with_assemblyai(save_path)
# #             transcript   = fluency_data.get("transcript", "")

# #             # 2. Grammar check (LanguageTool)
# #             grammar_data = check_grammar(transcript)

# #             # 3. AI scoring (Groq)
# #             ai_scores = score_answer_with_groq(
# #                 question     = q.get("q", ""),
# #                 ideal_themes = q.get("answer", ""),
# #                 transcript   = transcript,
# #                 fluency_metrics = fluency_data,
# #             )

# #             fluency_score  = compute_fluency_score(fluency_data)
# #             grammar_score  = compute_grammar_score(grammar_data)

# #             q_result.update({
# #                 "transcript":       transcript,
# #                 "fluency_score":    fluency_score,
# #                 "grammar_score":    grammar_score,
# #                 "confidence_score": ai_scores["confidence"],
# #                 "relevance_score":  ai_scores["relevance"],
# #                 "filler_words":     fluency_data.get("filler_count", 0),
# #                 "pauses":           fluency_data.get("pause_count", 0),
# #                 "grammar_errors":   grammar_data.get("error_count", 0),
# #                 "explanation":      ai_scores.get("explanation", ""),
# #             })

# #         question_results.append(q_result)

# #     # Aggregate with per-question marks
# #     totals = aggregate_scores(question_results, questions)

# #     # Build overall explanation via Groq
# #     overall_explanation = "Evaluation based on fluency, grammar, confidence and answer relevance."
# #     if GROQ_CLIENT:
# #         try:
# #             summary_prompt = f"""Summarise this candidate's overall soft skills interview performance in 3 sentences.
# # Scores: Fluency={totals['fluency']}, Grammar={totals['grammar']}, Confidence={totals['confidence']}, Relevance={totals['relevance']}, Overall={totals['overall']}
# # Per-question notes: {'; '.join([r.get('explanation','') for r in question_results][:3])}
# # Be specific and professional. Mention strengths and areas for improvement."""
# #             r = GROQ_CLIENT.chat.completions.create(
# #                 model="llama-3.3-70b-versatile",
# #                 messages=[{"role": "user", "content": summary_prompt}],
# #                 temperature=0.3,
# #             )
# #             overall_explanation = r.choices[0].message.content.strip()
# #         except Exception:
# #             pass

# #     # Save to DB
# #     try:
# #         conn.execute('''
# #             INSERT INTO softskills_results
# #               (candidate_id, job_id, overall_score, fluency_score, grammar_score,
# #                confidence_score, relevance_score, overall_explanation, question_details)
# #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
# #         ''', (
# #             candidate_id, job_id,
# #             totals['overall'], totals['fluency'], totals['grammar'],
# #             totals['confidence'], totals['relevance'],
# #             overall_explanation,
# #             json.dumps(question_results),
# #         ))
# #         conn.execute(
# #             "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
# #             (candidate_id, job_id)
# #         )
# #         conn.commit()
# #         flash(f"Interview submitted! Score: {totals['overall']}/100 "
# #               f"({totals['marks_obtained']}/{totals['total_marks']} marks)", 'success')
# #     except Exception as e:
# #         flash(f"Error saving results: {e}", 'error')
# #     finally:
# #         conn.close()

# #     return redirect(url_for('candidate_jobs'))


# # @softskills_bp.route('/candidate/softskills/proctor_log/<int:job_id>', methods=['POST'])
# # def softskills_proctor_log(job_id):
# #     if session.get('user_type') != 'candidate':
# #         return jsonify({'ok': False}), 403
# #     event = request.json.get('event', 'unknown')
# #     conn = db()
# #     try:
# #         conn.execute(
# #             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
# #             (session['user_id'], job_id, 'softskills_proctor', event)
# #         )
# #         conn.commit()
# #     except Exception:
# #         pass
# #     finally:
# #         conn.close()
# #     return jsonify({'ok': True})


# # @softskills_bp.route('/admin/softskills_shortlist/<int:job_id>', methods=['POST'])
# # def admin_softskills_shortlist(job_id):
# #     """Send congratulations messages to all candidates above the threshold score."""
# #     if session.get('user_type') != 'admin':
# #         return jsonify({'ok': False, 'message': 'Unauthorised'}), 403

# #     threshold = int(request.json.get('threshold', 60))
# #     conn = db()
# #     try:
# #         # Get all candidates above threshold for this job
# #         rows = conn.execute('''
# #             SELECT r.candidate_id, r.overall_score, c.name
# #             FROM softskills_results r
# #             JOIN candidates c ON r.candidate_id = c.id
# #             WHERE r.job_id = ? AND r.overall_score >= ?
# #         ''', (job_id, threshold)).fetchall()

# #         if not rows:
# #             return jsonify({'ok': False, 'message': f'No candidates scored {threshold} or above.'})

# #         count = 0
# #         for row in rows:
# #             # Check if message already sent to avoid duplicates
# #             existing = conn.execute('''
# #                 SELECT id FROM messages
# #                 WHERE candidate_id = ? AND job_id = ?
# #                 AND subject LIKE '%Selected for Next Round%'
# #             ''', (row['candidate_id'], job_id)).fetchone()

# #             if not existing:
# #                 subject = "🎉 Congratulations! You've Been Selected for the Next Round"
# #                 body = f"""Dear {row['name']},

# # We are thrilled to inform you that you have successfully cleared the Soft Skills Interview round with an impressive score of {row['overall_score']}/100!

# # Your communication, confidence, and overall presentation stood out among all the candidates. We are pleased to invite you to the next stage of our selection process.

# # Our team will be in touch shortly with further details about what's next.

# # Once again, congratulations on this achievement — you should be proud!

# # Warm regards,
# # HR Team"""
# #                 conn.execute(
# #                     'INSERT INTO messages (candidate_id, job_id, subject, body) VALUES (?, ?, ?, ?)',
# #                     (row['candidate_id'], job_id, subject, body)
# #                 )
# #                 # Update application status
# #                 conn.execute(
# #                     "UPDATE applications SET status = 'Shortlisted for Next Round' WHERE candidate_id = ? AND job_id = ?",
# #                     (row['candidate_id'], job_id)
# #                 )
# #                 count += 1

# #         conn.commit()
# #         return jsonify({'ok': True, 'count': count, 'total': len(rows),
# #                         'message': f'{count} new candidates notified (threshold: {threshold}/100).'})
# #     except Exception as e:
# #         return jsonify({'ok': False, 'message': str(e)}), 500
# #     finally:
# #         conn.close()


# # @softskills_bp.route('/admin/softskills_results/<int:job_id>')
# # def admin_softskills_results(job_id):
# #     if session.get('user_type') != 'admin':
# #         flash("Unauthorised.", 'warning')
# #         return redirect(url_for('admin_login'))

# #     conn = db()
# #     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
# #     results = conn.execute('''
# #         SELECT
# #             c.id AS candidate_id,
# #             c.name, c.email,
# #             r.overall_score, r.fluency_score, r.grammar_score,
# #             r.confidence_score, r.relevance_score,
# #             r.overall_explanation, r.question_details,
# #             r.submission_time
# #         FROM softskills_results r
# #         JOIN candidates c ON r.candidate_id = c.id
# #         WHERE r.job_id = ?
# #         ORDER BY r.overall_score DESC
# #     ''', (job_id,)).fetchall()
# #     conn.close()

# #     return render_template('admin_softskills_results.html', job=job, results=results,
# #                            job_id=job_id)


# # @softskills_bp.route('/admin/softskills_video/<int:job_id>/<int:candidate_id>/<int:q_num>')
# # def serve_softskills_video(job_id, candidate_id, q_num):
# #     """Serve a candidate's recorded answer video to the admin."""
# #     if session.get('user_type') != 'admin':
# #         return "Unauthorised", 403
# #     from flask import send_from_directory
# #     video_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
# #     filename   = f"q{q_num}.webm"
# #     full_path  = os.path.join(video_dir, filename)
# #     if not os.path.exists(full_path):
# #         return "Recording not found", 404
# #     return send_from_directory(video_dir, filename, mimetype='video/webm')

# # # Add this function to generate test link
# # def generate_test_link(job_id):
# #     """Generate the full URL for the test"""
# #     from flask import url_for
# #     # This will be set when blueprint is registered
# #     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)

# # # Modify the generate_softskills_questions function to also return a test link
# # # def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
# # #     """
# # #     Generate soft skills questions and return (questions, error, test_link)
# # #     Now returns test_link as third value
# # #     """
# # #     if not GROQ_CLIENT:
# # #         return None, "Groq client not available.", None

# # #     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# # # Each question must:
# # # - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# # # - Require 60-90 seconds to answer verbally
# # # - Test a different soft skill

# # # Default marks per question: {marks_per_question}

# # # Return a JSON array:
# # # [
# # #   {{
# # #     "q": "<full question text>",
# # #     "type": "audio_text",
# # #     "skill": "<skill being tested e.g. communication>",
# # #     "marks": {marks_per_question},
# # #     "options": [],
# # #     "answer": "<ideal answer keywords/themes for evaluation>"
# # #   }}
# # # ]"""

# # #     try:
# # #         resp = GROQ_CLIENT.chat.completions.create(
# # #             model="llama-3.3-70b-versatile",
# # #             messages=[
# # #                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
# # #                 {"role": "user",   "content": prompt}
# # #             ],
# # #             temperature=0.6,
# # #         )
# # #         text = resp.choices[0].message.content.strip()
# # #         if text.startswith("```"):
# # #             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
# # #             text = re.sub(r"\n?```$", "", text).strip()
# # #         questions = json.loads(text)
# # #         if not isinstance(questions, list):
# # #             return None, "Unexpected format from Groq.", None
        
# # #         # Generate test link
# # #         from flask import url_for
# # #         test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
        
# # #         return questions, None, test_link
# # #     except Exception as e:
# # #         return None, f"Question generation failed: {e}", None


# # def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5, job_id: int = None) -> tuple:
# #     """
# #     Generate soft skills questions and return (questions, error, test_link)
# #     Now accepts job_id as parameter
# #     """
# #     if not GROQ_CLIENT:
# #         return None, "Groq client not available.", None

# #     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# # Each question must:
# # - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# # - Require 60-90 seconds to answer verbally
# # - Test a different soft skill

# # Default marks per question: {marks_per_question}

# # Return a JSON array:
# # [
# #   {{
# #     "q": "<full question text>",
# #     "type": "audio_text",
# #     "skill": "<skill being tested e.g. communication>",
# #     "marks": {marks_per_question},
# #     "options": [],
# #     "answer": "<ideal answer keywords/themes for evaluation>"
# #   }}
# # ]"""

# #     try:
# #         resp = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
# #                 {"role": "user",   "content": prompt}
# #             ],
# #             temperature=0.6,
# #         )
# #         text = resp.choices[0].message.content.strip()
# #         if text.startswith("```"):
# #             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
# #             text = re.sub(r"\n?```$", "", text).strip()
# #         questions = json.loads(text)
# #         if not isinstance(questions, list):
# #             return None, "Unexpected format from Groq.", None
        
# #         # Generate test link only if job_id is provided
# #         test_link = None
# #         if job_id:
# #             from flask import url_for
# #             try:
# #                 test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
# #             except Exception as e:
# #                 print(f"Warning: Could not generate test link: {e}")
# #                 test_link = None
        
# #         return questions, None, test_link
# #     except Exception as e:
# #         return None, f"Question generation failed: {e}", None


# # def get_softskills_test_link(job_id):
# #     """Generate the test link for softskills interview"""
# #     from flask import url_for
# #     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)



# # # ------------------------------------------------------------------ #
# # #  DB MIGRATION — call once at startup                                #
# # # ------------------------------------------------------------------ #
# # def create_softskills_table():
# #     """Create the softskills_results table if it doesn't exist."""
# #     conn = db()
# #     conn.execute('''
# #         CREATE TABLE IF NOT EXISTS softskills_results (
# #             id                INTEGER PRIMARY KEY AUTOINCREMENT,
# #             candidate_id      INTEGER NOT NULL,
# #             job_id            INTEGER NOT NULL,
# #             overall_score     INTEGER DEFAULT 0,
# #             fluency_score     INTEGER DEFAULT 0,
# #             grammar_score     INTEGER DEFAULT 0,
# #             confidence_score  INTEGER DEFAULT 0,
# #             relevance_score   INTEGER DEFAULT 0,
# #             overall_explanation TEXT,
# #             question_details  TEXT,
# #             submission_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #         )
# #     ''')
# #     conn.commit()
# #     conn.close()



































































# # from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
# # import json
# # import os
# # from datetime import datetime
# # import sqlite3
# # import re

# # softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

# # # Database connection function (will be set from app)
# # _db_connection = None

# # def register_db(conn_func):
# #     global _db_connection
# #     _db_connection = conn_func

# # def get_db():
# #     if _db_connection:
# #         return _db_connection()
# #     return None

# # def create_softskills_table():
# #     """Create soft skills responses table if it doesn't exist"""
# #     conn = get_db()
# #     if not conn:
# #         return
    
# #     try:
# #         conn.execute('''
# #             CREATE TABLE IF NOT EXISTS softskills_responses (
# #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                 candidate_id INTEGER NOT NULL,
# #                 job_id INTEGER NOT NULL,
# #                 question_number INTEGER NOT NULL,
# #                 question_text TEXT,
# #                 audio_path TEXT,
# #                 answer_text TEXT,
# #                 submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #             )
# #         ''')
# #         conn.commit()
# #         print("✅ Soft skills responses table created/verified")
# #     except Exception as e:
# #         print(f"Error creating softskills table: {e}")
# #     finally:
# #         conn.close()

# # def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
# #     """Generate soft skills interview questions using Groq"""
# #     from app import GROQ_CLIENT
    
# #     if not GROQ_CLIENT:
# #         return None, "Groq client not initialized", None
    
# #     try:
# #         prompt = f"""
# # You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# # Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# # Return ONLY a JSON array in this format:
# # [
# #   {{
# #     "q": "Question text?",
# #     "type": "audio_text",
# #     "options": [],
# #     "answer": "Sample ideal answer guide for evaluation"
# #   }}
# # ]

# # Make the questions professional, relevant, and open-ended to allow detailed responses.
# # """
        
# #         completion = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {
# #                     "role": "system", 
# #                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
# #                 },
# #                 {"role": "user", "content": prompt}
# #             ],
# #             temperature=0.7,
# #         )
        
# #         response_text = completion.choices[0].message.content.strip()
        
# #         # Clean up markdown if present
# #         if response_text.startswith('```'):
# #             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
# #             response_text = re.sub(r'\n?```$', '', response_text)
        
# #         questions = json.loads(response_text)
        
# #         # Generate test link
# #         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
# #         return questions, None, test_link
        
# #     except Exception as e:
# #         print(f"Error generating soft skills questions: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return None, str(e), None

# # @softskills_bp.route('/candidate/view/<int:job_id>')
# # def candidate_softskills_view(job_id):
# #     """Display soft skills interview page"""
# #     if session.get('user_type') != 'candidate':
# #         flash("Please log in to take the interview.", 'warning')
# #         return redirect(url_for('candidate_login'))
    
# #     candidate_id = session['user_id']
# #     conn = get_db()
    
# #     if not conn:
# #         flash("Database connection error", 'error')
# #         return redirect(url_for('candidate_jobs'))
    
# #     # Check if already submitted
# #     existing = conn.execute(
# #         'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
# #         (candidate_id, job_id)
# #     ).fetchone()
    
# #     if existing:
# #         conn.close()
# #         flash("You have already completed this interview.", 'info')
# #         return redirect(url_for('candidate_jobs'))
    
# #     # Get test details
# #     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
# #     conn.close()
    
# #     if not test:
# #         flash("Interview not found.", 'error')
# #         return redirect(url_for('candidate_jobs'))
    
# #     # Parse questions
# #     questions = []
# #     try:
# #         if test['questions_json']:
# #             questions_json_str = test['questions_json'].strip()
# #             if questions_json_str.startswith('```'):
# #                 questions_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', questions_json_str)
# #                 questions_json_str = re.sub(r'\n?```$', '', questions_json_str)
# #             questions = json.loads(questions_json_str)
# #     except Exception as e:
# #         print(f"Error parsing questions: {e}")
# #         flash("Error loading interview questions.", 'error')
# #         return redirect(url_for('candidate_jobs'))
    
# #     return render_template('candidate_softskills_test.html',
# #                          test=test,
# #                          questions=questions,
# #                          job_id=job_id)

# # @softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
# # def candidate_submit_softskills(job_id):
# #     """Submit soft skills interview answers"""
# #     print(f"=== SUBMIT SOFT SKILLS CALLED for job_id: {job_id} ===")
    
# #     if session.get('user_type') != 'candidate':
# #         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
# #     candidate_id = session['user_id']
# #     conn = get_db()
    
# #     if not conn:
# #         return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
# #     try:
# #         # Check if already submitted
# #         existing = conn.execute(
# #             'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
# #             (candidate_id, job_id)
# #         ).fetchone()
        
# #         if existing:
# #             conn.close()
# #             return jsonify({'success': False, 'message': 'You have already submitted this interview'}), 400
        
# #         # Get job ID from form
# #         job_id_from_form = request.form.get('job_id')
# #         if job_id_from_form:
# #             job_id = int(job_id_from_form)
        
# #         # Create uploads folder if not exists
# #         upload_folder = os.path.join('uploads', 'softskills_audio')
# #         os.makedirs(upload_folder, exist_ok=True)
        
# #         # Process all audio files
# #         saved_files = []
# #         for key in request.files:
# #             if key.startswith('audio_'):
# #                 audio_file = request.files[key]
# #                 if audio_file and audio_file.filename:
# #                     # Generate filename
# #                     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
# #                     filename = f"candidate_{candidate_id}_job_{job_id}_{key}_{timestamp}.webm"
# #                     filepath = os.path.join(upload_folder, filename)
                    
# #                     # Save file
# #                     audio_file.save(filepath)
# #                     saved_files.append(filepath)
                    
# #                     # Extract question number from key (audio_1, audio_2, etc.)
# #                     question_num = int(key.split('_')[1])
                    
# #                     # Get answer text
# #                     answer_key = f"answer_{question_num}"
# #                     answer_text = request.form.get(answer_key, '')
                    
# #                     # Save to database
# #                     conn.execute('''
# #                         INSERT INTO softskills_responses 
# #                         (candidate_id, job_id, question_number, audio_path, answer_text)
# #                         VALUES (?, ?, ?, ?, ?)
# #                     ''', (candidate_id, job_id, question_num, filename, answer_text))
        
# #         # Update application status
# #         conn.execute('''
# #             UPDATE applications 
# #             SET status = 'Test Completed' 
# #             WHERE candidate_id = ? AND job_id = ?
# #         ''', (candidate_id, job_id))
        
# #         # Also update test_results table for consistency
# #         conn.execute('''
# #             INSERT OR REPLACE INTO test_results 
# #             (candidate_id, job_id, score, submitted_answers_json)
# #             VALUES (?, ?, ?, ?)
# #         ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
        
# #         conn.commit()
        
# #         print(f"✅ Soft skills interview submitted successfully for candidate {candidate_id}")
# #         print(f"   Saved {len(saved_files)} audio files")
        
# #         return jsonify({
# #             'success': True, 
# #             'message': 'Interview submitted successfully',
# #             'files_saved': len(saved_files)
# #         })
        
# #     except Exception as e:
# #         print(f"❌ Error submitting soft skills: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return jsonify({'success': False, 'message': str(e)}), 500
# #     finally:
# #         if conn:
# #             conn.close()



# # @softskills_bp.route('/admin/results/<int:job_id>')
# # def admin_softskills_results(job_id):
# #     """View soft skills interview results for admin"""
# #     if session.get('user_type') != 'admin':
# #         flash("Unauthorized access.", 'warning')
# #         return redirect(url_for('admin_login'))
    
# #     conn = get_db()
# #     if not conn:
# #         flash("Database connection error", 'error')
# #         return redirect(url_for('admin_dashboard'))
    
# #     try:
# #         # Get job details
# #         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
        
# #         # Get all soft skills responses for this job
# #         responses = conn.execute('''
# #             SELECT 
# #                 sr.*,
# #                 c.name as candidate_name,
# #                 c.email as candidate_email
# #             FROM softskills_responses sr
# #             JOIN candidates c ON sr.candidate_id = c.id
# #             WHERE sr.job_id = ?
# #             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
# #         ''', (job_id,)).fetchall()
        
# #         # Group responses by candidate
# #         candidates_dict = {}
# #         for response in responses:
# #             candidate_id = response['candidate_id']
# #             if candidate_id not in candidates_dict:
# #                 candidates_dict[candidate_id] = {
# #                     'candidate_id': candidate_id,
# #                     'candidate_name': response['candidate_name'],
# #                     'candidate_email': response['candidate_email'],
# #                     'responses': [],
# #                     'submission_time': response['submission_time']
# #                 }
# #             candidates_dict[candidate_id]['responses'].append({
# #                 'question_number': response['question_number'],
# #                 'question_text': response['question_text'],
# #                 'audio_path': response['audio_path'],
# #                 'answer_text': response['answer_text']
# #             })
        
# #         candidates_list = list(candidates_dict.values())
        
# #         return render_template('admin_softskills_results.html', 
# #                              job=job, 
# #                              candidates=candidates_list,
# #                              job_id=job_id)
# #     except Exception as e:
# #         print(f"Error viewing soft skills results: {e}")
# #         flash(f"Error loading results: {e}", 'error')
# #         return redirect(url_for('admin_dashboard'))
# #     finally:
# #         conn.close()



# # @softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
# # def log_proctor_event(job_id):
# #     """Log proctor events for soft skills interview"""
# #     if session.get('user_type') != 'candidate':
# #         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
# #     candidate_id = session['user_id']
# #     data = request.get_json()
# #     event_type = data.get('event_type')
# #     details = data.get('details', '')
    
# #     conn = get_db()
# #     if not conn:
# #         return jsonify({'success': False, 'message': 'Database error'}), 500
    
# #     try:
# #         # Create proctor_logs table if not exists
# #         conn.execute('''
# #             CREATE TABLE IF NOT EXISTS proctor_logs (
# #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                 candidate_id INTEGER,
# #                 job_id INTEGER,
# #                 event_type TEXT,
# #                 details TEXT,
# #                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #             )
# #         ''')
        
# #         conn.execute('''
# #             INSERT INTO proctor_logs (candidate_id, job_id, event_type, details)
# #             VALUES (?, ?, ?, ?)
# #         ''', (candidate_id, job_id, event_type, details))
# #         conn.commit()
# #         return jsonify({'success': True})
# #     except Exception as e:
# #         print(f"Error logging proctor event: {e}")
# #         return jsonify({'success': False, 'message': str(e)}), 500
# #     finally:
# #         conn.close()

# # def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
# #     """Generate soft skills interview questions using Groq"""
# #     from app import GROQ_CLIENT
    
# #     if not GROQ_CLIENT:
# #         return None, "Groq client not initialized", None
    
# #     try:
# #         prompt = f"""
# # You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# # Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# # Return ONLY a JSON array in this format:
# # [
# #   {{
# #     "q": "Question text?",
# #     "type": "audio_text",
# #     "options": [],
# #     "answer": "Sample ideal answer guide for evaluation"
# #   }}
# # ]

# # Make the questions professional, relevant, and open-ended to allow detailed responses.
# # """
        
# #         completion = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {
# #                     "role": "system", 
# #                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
# #                 },
# #                 {"role": "user", "content": prompt}
# #             ],
# #             temperature=0.7,
# #         )
        
# #         response_text = completion.choices[0].message.content.strip()
        
# #         # Clean up markdown if present
# #         if response_text.startswith('```'):
# #             import re
# #             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
# #             response_text = re.sub(r'\n?```$', '', response_text)
        
# #         questions = json.loads(response_text)
        
# #         # Generate test link
# #         from flask import url_for
# #         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
# #         return questions, None, test_link
        
# #     except Exception as e:
# #         print(f"Error generating soft skills questions: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return None, str(e), None












































































































# from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify, send_from_directory
# import json
# import os
# import base64
# from datetime import datetime
# import sqlite3
# import re

# softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

# _db_connection = None

# def register_db(conn_func):
#     global _db_connection
#     _db_connection = conn_func

# def get_db():
#     if _db_connection:
#         return _db_connection()
#     return None

# def create_softskills_table():
#     """Create soft skills responses table if it doesn't exist"""
#     conn = get_db()
#     if not conn:
#         return
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS softskills_responses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER NOT NULL,
#                 job_id INTEGER NOT NULL,
#                 question_number INTEGER NOT NULL,
#                 question_text TEXT,
#                 audio_path TEXT,
#                 answer_text TEXT,
#                 transcript TEXT,
#                 submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Migrate older schema that may not have transcript column
#         try:
#             conn.execute('ALTER TABLE softskills_responses ADD COLUMN transcript TEXT')
#         except Exception:
#             pass  # Column already exists — that's fine
#         conn.commit()
#         print("✅ Soft skills responses table created/verified")
#     except Exception as e:
#         print(f"Error creating softskills table: {e}")
#     finally:
#         conn.close()


# # ── Groq Whisper transcription ────────────────────────────────────────────────
# def transcribe_audio_file(filepath):
#     """
#     Transcribe an audio/video file using Groq Whisper.
#     Returns (transcript_text, error_message).
#     Groq Whisper supports: mp3, mp4, mpeg, mpga, m4a, wav, webm
#     """
#     from app import GROQ_CLIENT
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialised — check GROQ_API_KEY"

#     if not filepath or not os.path.exists(filepath):
#         return None, f"File not found: {filepath}"

#     try:
#         with open(filepath, 'rb') as f:
#             # Pass explicit content-type so Groq knows how to decode the container
#             transcription = GROQ_CLIENT.audio.transcriptions.create(
#                 file=(os.path.basename(filepath), f, 'audio/webm'),
#                 model='whisper-large-v3',
#                 language='en',
#                 response_format='text'   # returns a plain string, not JSON
#             )
#         transcript = str(transcription).strip()
#         return (transcript if transcript else "(No speech detected)"), None
#     except Exception as e:
#         print(f"Whisper transcription error for {filepath}: {e}")
#         return None, str(e)


# # ── Question generation ───────────────────────────────────────────────────────
# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     from app import GROQ_CLIENT
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.
# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.
# Return ONLY a JSON array:
# [{{"q":"Question text?","type":"audio_text","options":[],"answer":"Ideal answer guide"}}]
# """
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": "You are a professional HR assessment generator. Always respond with valid JSON only."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
#         response_text = completion.choices[0].message.content.strip()
#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
#         questions = json.loads(response_text)
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
#         return questions, None, test_link
#     except Exception as e:
#         print(f"Error generating questions: {e}")
#         import traceback; traceback.print_exc()
#         return None, str(e), None


# # ── Candidate routes ──────────────────────────────────────────────────────────
# @softskills_bp.route('/candidate/view/<int:job_id>')
# def candidate_softskills_view(job_id):
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to take the interview.", 'warning')
#         return redirect(url_for('candidate_login'))
#     candidate_id = session['user_id']
#     conn = get_db()
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('candidate_jobs'))
#     existing = conn.execute(
#         'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
#     if existing:
#         conn.close()
#         flash("You have already completed this interview.", 'info')
#         return redirect(url_for('candidate_jobs'))
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     conn.close()
#     if not test:
#         flash("Interview not found.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     questions = []
#     try:
#         if test['questions_json']:
#             qs = test['questions_json'].strip()
#             if qs.startswith('```'):
#                 qs = re.sub(r'^```[a-zA-Z]*\n?', '', qs)
#                 qs = re.sub(r'\n?```$', '', qs)
#             questions = json.loads(qs)
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         flash("Error loading interview questions.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     return render_template('candidate_softskills_test.html', test=test, questions=questions, job_id=job_id)


# @softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     print(f"=== SUBMIT SOFT SKILLS for job_id={job_id} ===")
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
#     candidate_id = session['user_id']
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database connection error'}), 500
#     try:
#         existing = conn.execute(
#             'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#             (candidate_id, job_id)
#         ).fetchone()
#         if existing:
#             conn.close()
#             return jsonify({'success': False, 'message': 'Already submitted'}), 400

#         if request.form.get('job_id'):
#             job_id = int(request.form.get('job_id'))

#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)

#         saved_files = []
#         total_questions = 0

#         all_keys = list(request.form.keys()) + list(request.files.keys())
#         q_indices = set()
#         for key in all_keys:
#             if key.startswith('audio_') or key.startswith('answer_'):
#                 try:
#                     q_indices.add(int(key.split('_')[1]))
#                 except:
#                     pass

#         for question_num in sorted(q_indices):
#             answer_text = request.form.get(f'answer_{question_num}', '')
#             audio_path_db = None

#             # 1) Multipart file upload (from AI interview page)
#             if f'audio_{question_num}' in request.files:
#                 af = request.files[f'audio_{question_num}']
#                 if af and af.filename:
#                     ct = af.content_type or 'video/webm'
#                     ext = 'mp4' if 'mp4' in ct else 'webm'
#                     ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.{ext}"
#                     filepath = os.path.join(upload_folder, filename)
#                     af.save(filepath)
#                     audio_path_db = filename
#                     saved_files.append(filepath)
#                     print(f"  ✅ Saved Q{question_num}: {filename} ({ct})")

#             # 2) Base64 in audio_N form field
#             if not audio_path_db:
#                 b64 = request.form.get(f'audio_{question_num}', '')
#                 if b64.startswith('data:'):
#                     try:
#                         _, enc = b64.split(',', 1)
#                         data = base64.b64decode(enc)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(data)
#                         audio_path_db = filename
#                         saved_files.append(filepath)
#                     except Exception as e:
#                         print(f"  ⚠️ base64 audio_{question_num}: {e}")

#             # 3) Base64 in q_N form field
#             if not audio_path_db:
#                 qv = request.form.get(f'q_{question_num}', '')
#                 if qv.startswith('data:'):
#                     try:
#                         _, enc = qv.split(',', 1)
#                         data = base64.b64decode(enc)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(data)
#                         audio_path_db = filename
#                         saved_files.append(filepath)
#                     except Exception as e:
#                         print(f"  ⚠️ base64 q_{question_num}: {e}")
#                 elif qv:
#                     answer_text = qv

#             conn.execute('''
#                 INSERT INTO softskills_responses
#                 (candidate_id, job_id, question_number, audio_path, answer_text)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (candidate_id, job_id, question_num, audio_path_db, answer_text))
#             total_questions += 1

#         # Standard q_N keys
#         for key in [k for k in request.form.keys() if re.match(r'^q_\d+$', k)]:
#             try:
#                 qn = int(key.split('_')[1])
#             except:
#                 continue
#             if qn in q_indices:
#                 continue
#             val = request.form.get(key, '')
#             apath = None
#             atext = ''
#             if val.startswith('data:'):
#                 try:
#                     _, enc = val.split(',', 1)
#                     data = base64.b64decode(enc)
#                     ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     fn = f"candidate_{candidate_id}_job_{job_id}_q{qn}_{ts}.webm"
#                     fp = os.path.join(upload_folder, fn)
#                     with open(fp, 'wb') as fh:
#                         fh.write(data)
#                     apath = fn
#                     saved_files.append(fp)
#                 except Exception as e:
#                     print(f"  ⚠️ q_{qn}: {e}")
#                     atext = val
#             else:
#                 atext = val
#             conn.execute('''
#                 INSERT INTO softskills_responses
#                 (candidate_id, job_id, question_number, audio_path, answer_text)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (candidate_id, job_id, qn, apath, atext))
#             total_questions += 1

#         conn.execute(
#             "UPDATE applications SET status='Test Completed' WHERE candidate_id=? AND job_id=?",
#             (candidate_id, job_id)
#         )
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results (candidate_id, job_id, score, submitted_answers_json)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
#         conn.commit()
#         print(f"✅ Done: {len(saved_files)} files, {total_questions} questions")
#         return jsonify({'success': True, 'message': 'Interview submitted successfully', 'files_saved': len(saved_files)})
#     except Exception as e:
#         print(f"❌ Submit error: {e}")
#         import traceback; traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         if conn:
#             conn.close()


# # ── Serve video/audio files ───────────────────────────────────────────────────
# @softskills_bp.route('/audio/<path:filename>')
# def serve_softskills_audio(filename):
#     """
#     Serve candidate video recordings to admin.
#     Implements HTTP Range requests so browsers can seek and render video frames.
#     """
#     if session.get('user_type') != 'admin':
#         return jsonify({'error': 'Unauthorized'}), 403

#     import re as _re
#     from flask import Response

#     audio_dir = os.path.join(os.getcwd(), 'uploads', 'softskills_audio')
#     filepath  = os.path.join(audio_dir, filename)

#     if not os.path.exists(filepath):
#         return jsonify({'error': 'File not found'}), 404

#     mimetype  = 'video/mp4' if filename.endswith('.mp4') else 'video/webm'
#     file_size = os.path.getsize(filepath)

#     range_header = request.headers.get('Range', None)

#     if range_header:
#         m = _re.match(r'bytes=(\d+)-(\d*)', range_header)
#         if m:
#             start  = int(m.group(1))
#             end    = int(m.group(2)) if m.group(2) else file_size - 1
#             end    = min(end, file_size - 1)
#             length = end - start + 1

#             with open(filepath, 'rb') as f:
#                 f.seek(start)
#                 chunk = f.read(length)

#             rv = Response(chunk, 206, mimetype=mimetype, direct_passthrough=True)
#             rv.headers['Content-Range']  = f'bytes {start}-{end}/{file_size}'
#             rv.headers['Accept-Ranges']  = 'bytes'
#             rv.headers['Content-Length'] = str(length)
#             rv.headers['Cache-Control']  = 'no-cache'
#             return rv

#     # Full file
#     with open(filepath, 'rb') as f:
#         data = f.read()

#     rv = Response(data, 200, mimetype=mimetype)
#     rv.headers['Accept-Ranges']  = 'bytes'
#     rv.headers['Content-Length'] = str(file_size)
#     rv.headers['Cache-Control']  = 'no-cache'
#     return rv


# # ── On-demand Groq Whisper transcription ─────────────────────────────────────
# @softskills_bp.route('/admin/transcribe/<int:response_id>', methods=['POST'])
# def admin_transcribe(response_id):
#     """Transcribe one response's recording using Groq Whisper. Admin only."""
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
#     try:
#         row = conn.execute(
#             'SELECT id, audio_path, transcript FROM softskills_responses WHERE id = ?',
#             (response_id,)
#         ).fetchone()

#         if not row:
#             return jsonify({'success': False, 'message': 'Response not found'}), 404

#         # Return cached transcript instantly
#         if row['transcript']:
#             return jsonify({'success': True, 'transcript': row['transcript'], 'cached': True})

#         if not row['audio_path']:
#             return jsonify({'success': False, 'message': 'No audio file attached to this response'}), 400

#         filepath = os.path.join('uploads', 'softskills_audio', row['audio_path'])
#         transcript, error = transcribe_audio_file(filepath)

#         if error:
#             return jsonify({'success': False, 'message': f'Transcription failed: {error}'}), 500

#         # Persist so next call is instant
#         conn.execute(
#             'UPDATE softskills_responses SET transcript = ? WHERE id = ?',
#             (transcript, response_id)
#         )
#         conn.commit()
#         return jsonify({'success': True, 'transcript': transcript, 'cached': False})

#     except Exception as e:
#         print(f"Transcription error: {e}")
#         import traceback; traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# # ── Admin results page ────────────────────────────────────────────────────────
# # @softskills_bp.route('/admin/results/<int:job_id>')
# # def admin_softskills_results(job_id):
# #     if session.get('user_type') != 'admin':
# #         flash("Unauthorized access.", 'warning')
# #         return redirect(url_for('admin_login'))
# #     conn = get_db()
# #     if not conn:
# #         flash("Database connection error", 'error')
# #         return redirect(url_for('admin_dashboard'))
# #     try:
# #         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
# #         responses = conn.execute('''
# #             SELECT sr.*, c.name as candidate_name, c.email as candidate_email
# #             FROM softskills_responses sr
# #             JOIN candidates c ON sr.candidate_id = c.id
# #             WHERE sr.job_id = ?
# #             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
# #         ''', (job_id,)).fetchall()

# #         candidates_dict = {}
# #         for r in responses:
# #             cid = r['candidate_id']
# #             if cid not in candidates_dict:
# #                 candidates_dict[cid] = {
# #                     'candidate_id': cid,
# #                     'candidate_name': r['candidate_name'],
# #                     'candidate_email': r['candidate_email'],
# #                     'responses': [],
# #                     'submission_time': r['submission_time']
# #                 }
# #             audio_url = None
# #             if r['audio_path']:
# #                 audio_url = url_for('softskills.serve_softskills_audio', filename=r['audio_path'])

# #             candidates_dict[cid]['responses'].append({
# #                 'id': r['id'],
# #                 'question_number': r['question_number'],
# #                 'question_text': r['question_text'],
# #                 'audio_path': r['audio_path'],
# #                 'audio_url': audio_url,
# #                 'answer_text': r['answer_text'],
# #                 'transcript': r['transcript'] if r['transcript'] else None,
# #             })

# #         return render_template('admin_softskills_results.html',
# #                                job=job,
# #                                candidates=list(candidates_dict.values()),
# #                                job_id=job_id)
# #     except Exception as e:
# #         print(f"Results error: {e}")
# #         flash(f"Error loading results: {e}", 'error')
# #         return redirect(url_for('admin_dashboard'))
# #     finally:
# #         conn.close()



# @softskills_bp.route('/admin/results/<int:job_id>')
# def admin_softskills_results(job_id):
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     conn = get_db() 
#     try:
#         # 1. Fetch the job details for the template header
#         job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()

#         # 2. Fetch candidates and include the submission_time from test_results
#         responses = conn.execute('''
#             SELECT 
#                 c.id AS candidate_id, c.name, c.email, 
#                 r.question_number, r.question_text, r.audio_path, r.answer_text,
#                 tr.submission_time
#             FROM applications a
#             JOIN candidates c ON a.candidate_id = c.id
#             LEFT JOIN softskills_responses r ON a.candidate_id = r.candidate_id AND a.job_id = r.job_id
#             LEFT JOIN test_results tr ON a.candidate_id = tr.candidate_id AND a.job_id = tr.job_id
#             WHERE a.job_id = ? AND a.status = 'Test Completed'
#             ORDER BY c.id, r.question_number
#         ''', (job_id,)).fetchall()
        
#         candidates_dict = {}
#         for row in responses:
#             cid = row['candidate_id']
#             if cid not in candidates_dict:
#                 candidates_dict[cid] = {
#                     'candidate_id': cid,
#                     'name': row['name'],
#                     'email': row['email'],
#                     # 🟢 FIX: Safely add submission_time to the dictionary
#                     'submission_time': row['submission_time'] or 'Recently', 
#                     'answers': []
#                 }
#             # Only append if an audio file actually exists
#             if row['question_number'] is not None:
#                 candidates_dict[cid]['answers'].append(dict(row))
                
#         return render_template('admin_softskills_results.html',
#                                job=job,
#                                candidates=list(candidates_dict.values()),
#                                job_id=job_id)
                               
#     except Exception as e:
#         print(f"Results error: {e}")
#         flash(f"Error loading results: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         conn.close()

# # ── Proctor event logging ─────────────────────────────────────────────────────
# @softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
# def log_proctor_event(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
#     candidate_id = session['user_id']
#     data = request.get_json()
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS proctor_logs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER, job_id INTEGER,
#                 event_type TEXT, details TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (candidate_id, job_id, data.get('event_type'), data.get('details', ''))
#         )
#         conn.commit()
#         return jsonify({'success': True})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()

































































































































# """
# softskills_routes.py
# Handles:
#   - AI question generation  (Groq)
#   - Candidate interview view
#   - Recording submission + evaluation pipeline
#       * AssemblyAI  → speech-to-text + fluency metrics
#       * LanguageTool → grammar / spelling errors
#       * Groq AI      → confidence / relevance / tone scoring
#   - Admin results view
# """

# import os, json, re, time, math, requests, tempfile
# from flask import (Blueprint, render_template, request, redirect,
#                    url_for, session, flash, jsonify)
# from datetime import datetime
# from groq import Groq

# softskills_bp = Blueprint('softskills', __name__)

# # ------------------------------------------------------------------ #
# #  CLIENTS                                                             #
# # ------------------------------------------------------------------ #
# GROQ_CLIENT = None
# try:
#     _key = os.getenv("GROQ_API_KEY")
#     if _key:
#         GROQ_CLIENT = Groq(api_key=_key)
# except Exception as e:
#     print(f"Softskills: Groq client failed: {e}")

# ASSEMBLYAI_KEY   = os.getenv("ASSEMBLYAI_API_KEY", "")
# LANGUAGETOOL_URL = "https://api.languagetoolplus.com/v2/check"   # free tier works
# LT_API_KEY       = os.getenv("LANGUAGETOOL_API_KEY", "")         # optional, works without

# # ------------------------------------------------------------------ #
# #  DB helper (imported from main app at registration time)           #
# # ------------------------------------------------------------------ #
# _get_db = None   # set via register_db(fn) below

# def register_db(fn):
#     global _get_db
#     _get_db = fn

# def db():
#     return _get_db()

# # ------------------------------------------------------------------ #
# #  QUESTION GENERATION                                                #
# # ------------------------------------------------------------------ #
# SOFT_SKILLS_SYSTEM = """You are an expert HR interviewer creating scenario-based spoken interview questions.
# Questions must require a verbal, conversational answer — NOT multiple choice.
# Focus on: communication, confidence, teamwork, conflict resolution, leadership, self-awareness.
# Return ONLY a valid JSON array. No markdown fences, no prose."""

# def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
#     if not GROQ_CLIENT:
#         return None, "Groq client not available."

#     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# Each question must:
# - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# - Require 60-90 seconds to answer verbally
# - Test a different soft skill

# Default marks per question: {marks_per_question}

# Return a JSON array:
# [
#   {{
#     "q": "<full question text>",
#     "type": "audio_text",
#     "skill": "<skill being tested e.g. communication>",
#     "marks": {marks_per_question},
#     "options": [],
#     "answer": "<ideal answer keywords/themes for evaluation>"
#   }}
# ]"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0.6,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         questions = json.loads(text)
#         if not isinstance(questions, list):
#             return None, "Unexpected format from Groq."
#         return questions, None
#     except Exception as e:
#         return None, f"Question generation failed: {e}"

# # ------------------------------------------------------------------ #
# #  ASSEMBLYAI — speech to text + fluency                              #
# # ------------------------------------------------------------------ #
# def transcribe_with_assemblyai(audio_path: str) -> dict:
#     """Upload audio file to AssemblyAI, poll for result, return metrics."""
#     base = {"transcript": "", "filler_count": 0, "pause_count": 0,
#             "words_per_minute": 0, "confidence": 0.0, "error": None}

#     if not ASSEMBLYAI_KEY:
#         base["error"] = "ASSEMBLYAI_API_KEY not set"
#         return base

#     headers = {"authorization": ASSEMBLYAI_KEY, "content-type": "application/json"}

#     try:
#         # 1. Upload file
#         with open(audio_path, "rb") as f:
#             up = requests.post("https://api.assemblyai.com/v2/upload",
#                                headers={"authorization": ASSEMBLYAI_KEY},
#                                data=f, timeout=60)
#         upload_url = up.json()["upload_url"]

#         # 2. Submit transcription with IAB + auto_chapters disabled, but keep disfluencies
#         payload = {
#             "audio_url": upload_url,
#             "disfluencies": True,       # keeps uh, um in transcript
#             "auto_highlights": True,    # key phrase extraction
#             "punctuate": True,
#             "format_text": True,
#         }
#         job = requests.post("https://api.assemblyai.com/v2/transcript",
#                             headers=headers, json=payload, timeout=30).json()
#         job_id = job["id"]

#         # 3. Poll (max 120s)
#         for _ in range(60):
#             time.sleep(2)
#             result = requests.get(f"https://api.assemblyai.com/v2/transcript/{job_id}",
#                                   headers=headers, timeout=15).json()
#             if result["status"] == "completed":
#                 break
#             if result["status"] == "error":
#                 base["error"] = result.get("error", "AssemblyAI error")
#                 return base

#         transcript_text = result.get("text") or ""
#         words           = result.get("words") or []
#         duration_sec    = (result.get("audio_duration") or 1)

#         # Words per minute
#         wpm = round(len(words) / (duration_sec / 60)) if duration_sec > 0 else 0

#         # Filler word count (uh, um, like, you know, basically)
#         filler_re = re.compile(r'\b(uh+|um+|uhm|like|you know|basically|so|right|okay)\b', re.I)
#         filler_count = len(filler_re.findall(transcript_text))

#         # Long pauses (gaps > 1.5s between consecutive words)
#         pause_count = 0
#         for i in range(1, len(words)):
#             gap = (words[i].get("start", 0) - words[i-1].get("end", 0)) / 1000.0
#             if gap > 1.5:
#                 pause_count += 1

#         # Average word confidence
#         confidences = [w.get("confidence", 0) for w in words if "confidence" in w]
#         avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

#         return {
#             "transcript":    transcript_text,
#             "filler_count":  filler_count,
#             "pause_count":   pause_count,
#             "words_per_minute": wpm,
#             "confidence":    avg_conf,
#             "error":         None,
#         }

#     except Exception as e:
#         base["error"] = str(e)
#         return base

# # ------------------------------------------------------------------ #
# #  LANGUAGETOOL — grammar check                                        #
# # ------------------------------------------------------------------ #
# def check_grammar(text: str) -> dict:
#     """Return count of grammar/spelling/style errors + list of issues."""
#     base = {"error_count": 0, "errors": [], "error": None}
#     if not text or len(text.strip()) < 10:
#         return base
#     try:
#         params = {
#             "text": text, "language": "en-US",
#             "enabledOnly": "false",
#         }
#         if LT_API_KEY:
#             params["apiKey"] = LT_API_KEY

#         resp = requests.post(LANGUAGETOOL_URL, data=params, timeout=20)
#         matches = resp.json().get("matches", [])
#         errors = [
#             {
#                 "message": m.get("message", ""),
#                 "context": m.get("context", {}).get("text", ""),
#                 "rule":    m.get("rule", {}).get("issueType", ""),
#             }
#             for m in matches[:10]   # cap at 10 for display
#         ]
#         return {"error_count": len(matches), "errors": errors, "error": None}
#     except Exception as e:
#         base["error"] = str(e)
#         return base

# # ------------------------------------------------------------------ #
# #  GROQ — confidence / relevance / tone scoring                        #
# # ------------------------------------------------------------------ #
# def score_answer_with_groq(question: str, ideal_themes: str, transcript: str,
#                             fluency_metrics: dict) -> dict:
#     """Ask Groq to score confidence, relevance, tone and give explanation."""
#     base = {"confidence": 50, "relevance": 50, "tone": 50,
#             "positivity": 50, "explanation": "AI scoring unavailable."}

#     if not GROQ_CLIENT or not transcript:
#         return base

#     prompt = f"""You are an expert HR assessor scoring a spoken interview answer.

# Question: {question}
# Ideal answer themes: {ideal_themes}
# Candidate transcript: {transcript}
# Fluency metrics: WPM={fluency_metrics.get('words_per_minute',0)}, fillers={fluency_metrics.get('filler_count',0)}, long pauses={fluency_metrics.get('pause_count',0)}

# Score each dimension from 0-100:
# - confidence: Does the candidate sound sure and assertive?
# - relevance: Does the answer address the question and ideal themes?
# - tone: Is the tone professional and appropriate?
# - positivity: Is the candidate's attitude positive and constructive?

# Return ONLY valid JSON:
# {{
#   "confidence": <int>,
#   "relevance": <int>,
#   "tone": <int>,
#   "positivity": <int>,
#   "explanation": "<2-3 sentences explaining the evaluation>"
# }}"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": "You are an HR evaluation expert. Reply with valid JSON only."},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         result = json.loads(text)
#         return {
#             "confidence":  max(0, min(100, int(result.get("confidence",  50)))),
#             "relevance":   max(0, min(100, int(result.get("relevance",   50)))),
#             "tone":        max(0, min(100, int(result.get("tone",        50)))),
#             "positivity":  max(0, min(100, int(result.get("positivity",  50)))),
#             "explanation": result.get("explanation", ""),
#         }
#     except Exception as e:
#         base["explanation"] = f"AI scoring error: {e}"
#         return base

# # ------------------------------------------------------------------ #
# #  SCORING AGGREGATION                                                 #
# # ------------------------------------------------------------------ #
# def compute_fluency_score(metrics: dict) -> int:
#     """Convert raw fluency metrics to a 0-100 score."""
#     wpm        = metrics.get("words_per_minute", 0)
#     fillers    = metrics.get("filler_count", 0)
#     pauses     = metrics.get("pause_count", 0)
#     conf       = metrics.get("confidence", 0.5) * 100   # 0-100

#     # WPM score: ideal 120-160 wpm for spoken English
#     if   wpm == 0:      wpm_score = 20
#     elif wpm < 80:      wpm_score = 50
#     elif wpm < 120:     wpm_score = 75
#     elif wpm <= 170:    wpm_score = 100
#     else:               wpm_score = 70   # too fast

#     # Penalty: each filler -3pts, each long pause -5pts
#     penalty = min(50, fillers * 3 + pauses * 5)
#     raw = (wpm_score * 0.4) + (conf * 0.4) - penalty * 0.2
#     return max(0, min(100, round(raw)))

# def compute_grammar_score(grammar: dict) -> int:
#     errors = grammar.get("error_count", 0)
#     if   errors == 0: return 100
#     elif errors <= 2: return 85
#     elif errors <= 5: return 65
#     elif errors <= 10: return 45
#     else:              return 25

# def aggregate_scores(question_results: list, questions: list) -> dict:
#     """Average all per-question scores into weighted totals using marks per question."""
#     n = len(question_results)
#     if n == 0:
#         return {"fluency": 0, "grammar": 0, "confidence": 0, "relevance": 0, "overall": 0,
#                 "total_marks": 0, "marks_obtained": 0}

#     # Total possible marks
#     total_marks = sum(int(q.get('marks', 5)) for q in questions) if questions else n * 5

#     def avg(key):
#         return round(sum(q.get(key, 0) for q in question_results) / n)

#     fluency    = avg("fluency_score")
#     grammar    = avg("grammar_score")
#     confidence = avg("confidence_score")
#     relevance  = avg("relevance_score")

#     # Marks obtained = weighted by per-question marks
#     marks_obtained = 0
#     for i, qr in enumerate(question_results):
#         q_marks  = int(questions[i].get('marks', 5)) if i < len(questions) else 5
#         # Average of 4 dimensions as 0-1 ratio, multiplied by question marks
#         ratio = (qr.get('fluency_score', 0) + qr.get('grammar_score', 0) +
#                  qr.get('confidence_score', 0) + qr.get('relevance_score', 0)) / 400.0
#         marks_obtained += round(ratio * q_marks, 2)

#     overall = round((marks_obtained / total_marks) * 100) if total_marks > 0 else 0
#     overall = max(0, min(100, overall))

#     return {
#         "fluency":        fluency,
#         "grammar":        grammar,
#         "confidence":     confidence,
#         "relevance":      relevance,
#         "overall":        overall,
#         "total_marks":    total_marks,
#         "marks_obtained": round(marks_obtained, 1),
#     }

# # ------------------------------------------------------------------ #
# #  ROUTES                                                              #
# # ------------------------------------------------------------------ #

# @softskills_bp.route('/candidate/softskills/test/<int:job_id>')
# def candidate_softskills_view(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = db()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     app_row = conn.execute(
#         'SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?',
#         (job_id, candidate_id)
#     ).fetchone()
#     already = conn.execute(
#         'SELECT id FROM softskills_results WHERE job_id = ? AND candidate_id = ?',
#         (job_id, candidate_id)
#     ).fetchone()
#     conn.close()

#     if not test or not app_row or app_row['status'] != 'Selected for Test':
#         flash("Not authorised for this interview.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     if already:
#         flash("You have already completed this soft skills interview.", 'info')
#         return redirect(url_for('candidate_jobs'))

#     questions = json.loads(test['questions_json']) if test['questions_json'] else []
#     if not questions:
#         flash("No questions configured for this interview.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     return render_template('candidate_softskills_test.html',
#                            test=test, questions=questions, job_id=job_id)


# @softskills_bp.route('/candidate/softskills/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = db()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if not test:
#         conn.close()
#         flash("Test not found.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     questions  = json.loads(test['questions_json'])
#     upload_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
#     os.makedirs(upload_dir, exist_ok=True)

#     question_results = []

#     for idx, q in enumerate(questions):
#         file_key = f"answer_{idx + 1}"
#         audio_file = request.files.get(file_key)

#         q_result = {
#             "question":      q.get("q", ""),
#             "skill":         q.get("skill", ""),
#             "marks":         q.get("marks", 10),
#             "transcript":    "",
#             "fluency_score": 50,
#             "grammar_score": 50,
#             "confidence_score": 50,
#             "relevance_score":  50,
#             "filler_words":  0,
#             "pauses":        0,
#             "grammar_errors": 0,
#             "explanation":   "No recording submitted.",
#             "recording_path": None,   # ← stored so admin can play it back
#         }

#         if audio_file and audio_file.filename:
#             save_path = os.path.join(upload_dir, f"q{idx+1}.webm")
#             audio_file.save(save_path)

#             # Store relative path for later playback
#             relative_path = os.path.join('softskills', str(job_id), str(candidate_id), f"q{idx+1}.webm")
#             q_result["recording_path"] = relative_path

#             # 1. Speech-to-text + fluency (AssemblyAI)
#             fluency_data = transcribe_with_assemblyai(save_path)
#             transcript   = fluency_data.get("transcript", "")

#             # 2. Grammar check (LanguageTool)
#             grammar_data = check_grammar(transcript)

#             # 3. AI scoring (Groq)
#             ai_scores = score_answer_with_groq(
#                 question     = q.get("q", ""),
#                 ideal_themes = q.get("answer", ""),
#                 transcript   = transcript,
#                 fluency_metrics = fluency_data,
#             )

#             fluency_score  = compute_fluency_score(fluency_data)
#             grammar_score  = compute_grammar_score(grammar_data)

#             q_result.update({
#                 "transcript":       transcript,
#                 "fluency_score":    fluency_score,
#                 "grammar_score":    grammar_score,
#                 "confidence_score": ai_scores["confidence"],
#                 "relevance_score":  ai_scores["relevance"],
#                 "filler_words":     fluency_data.get("filler_count", 0),
#                 "pauses":           fluency_data.get("pause_count", 0),
#                 "grammar_errors":   grammar_data.get("error_count", 0),
#                 "explanation":      ai_scores.get("explanation", ""),
#             })

#         question_results.append(q_result)

#     # Aggregate with per-question marks
#     totals = aggregate_scores(question_results, questions)

#     # Build overall explanation via Groq
#     overall_explanation = "Evaluation based on fluency, grammar, confidence and answer relevance."
#     if GROQ_CLIENT:
#         try:
#             summary_prompt = f"""Summarise this candidate's overall soft skills interview performance in 3 sentences.
# Scores: Fluency={totals['fluency']}, Grammar={totals['grammar']}, Confidence={totals['confidence']}, Relevance={totals['relevance']}, Overall={totals['overall']}
# Per-question notes: {'; '.join([r.get('explanation','') for r in question_results][:3])}
# Be specific and professional. Mention strengths and areas for improvement."""
#             r = GROQ_CLIENT.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=[{"role": "user", "content": summary_prompt}],
#                 temperature=0.3,
#             )
#             overall_explanation = r.choices[0].message.content.strip()
#         except Exception:
#             pass

#     # Save to DB
#     try:
#         conn.execute('''
#             INSERT INTO softskills_results
#               (candidate_id, job_id, overall_score, fluency_score, grammar_score,
#                confidence_score, relevance_score, overall_explanation, question_details)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             candidate_id, job_id,
#             totals['overall'], totals['fluency'], totals['grammar'],
#             totals['confidence'], totals['relevance'],
#             overall_explanation,
#             json.dumps(question_results),
#         ))
#         conn.execute(
#             "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#             (candidate_id, job_id)
#         )
#         conn.commit()
#         flash(f"Interview submitted! Score: {totals['overall']}/100 "
#               f"({totals['marks_obtained']}/{totals['total_marks']} marks)", 'success')
#     except Exception as e:
#         flash(f"Error saving results: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))


# @softskills_bp.route('/candidate/softskills/proctor_log/<int:job_id>', methods=['POST'])
# def softskills_proctor_log(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'ok': False}), 403
#     event = request.json.get('event', 'unknown')
#     conn = db()
#     try:
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (session['user_id'], job_id, 'softskills_proctor', event)
#         )
#         conn.commit()
#     except Exception:
#         pass
#     finally:
#         conn.close()
#     return jsonify({'ok': True})


# @softskills_bp.route('/admin/softskills_shortlist/<int:job_id>', methods=['POST'])
# def admin_softskills_shortlist(job_id):
#     """Send congratulations messages to all candidates above the threshold score."""
#     if session.get('user_type') != 'admin':
#         return jsonify({'ok': False, 'message': 'Unauthorised'}), 403

#     threshold = int(request.json.get('threshold', 60))
#     conn = db()
#     try:
#         # Get all candidates above threshold for this job
#         rows = conn.execute('''
#             SELECT r.candidate_id, r.overall_score, c.name
#             FROM softskills_results r
#             JOIN candidates c ON r.candidate_id = c.id
#             WHERE r.job_id = ? AND r.overall_score >= ?
#         ''', (job_id, threshold)).fetchall()

#         if not rows:
#             return jsonify({'ok': False, 'message': f'No candidates scored {threshold} or above.'})

#         count = 0
#         for row in rows:
#             # Check if message already sent to avoid duplicates
#             existing = conn.execute('''
#                 SELECT id FROM messages
#                 WHERE candidate_id = ? AND job_id = ?
#                 AND subject LIKE '%Selected for Next Round%'
#             ''', (row['candidate_id'], job_id)).fetchone()

#             if not existing:
#                 subject = "🎉 Congratulations! You've Been Selected for the Next Round"
#                 body = f"""Dear {row['name']},

# We are thrilled to inform you that you have successfully cleared the Soft Skills Interview round with an impressive score of {row['overall_score']}/100!

# Your communication, confidence, and overall presentation stood out among all the candidates. We are pleased to invite you to the next stage of our selection process.

# Our team will be in touch shortly with further details about what's next.

# Once again, congratulations on this achievement — you should be proud!

# Warm regards,
# HR Team"""
#                 conn.execute(
#                     'INSERT INTO messages (candidate_id, job_id, subject, body) VALUES (?, ?, ?, ?)',
#                     (row['candidate_id'], job_id, subject, body)
#                 )
#                 # Update application status
#                 conn.execute(
#                     "UPDATE applications SET status = 'Shortlisted for Next Round' WHERE candidate_id = ? AND job_id = ?",
#                     (row['candidate_id'], job_id)
#                 )
#                 count += 1

#         conn.commit()
#         return jsonify({'ok': True, 'count': count, 'total': len(rows),
#                         'message': f'{count} new candidates notified (threshold: {threshold}/100).'})
#     except Exception as e:
#         return jsonify({'ok': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @softskills_bp.route('/admin/softskills_results/<int:job_id>')
# def admin_softskills_results(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorised.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = db()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#     results = conn.execute('''
#         SELECT
#             c.id AS candidate_id,
#             c.name, c.email,
#             r.overall_score, r.fluency_score, r.grammar_score,
#             r.confidence_score, r.relevance_score,
#             r.overall_explanation, r.question_details,
#             r.submission_time
#         FROM softskills_results r
#         JOIN candidates c ON r.candidate_id = c.id
#         WHERE r.job_id = ?
#         ORDER BY r.overall_score DESC
#     ''', (job_id,)).fetchall()
#     conn.close()

#     return render_template('admin_softskills_results.html', job=job, results=results,
#                            job_id=job_id)


# @softskills_bp.route('/admin/softskills_video/<int:job_id>/<int:candidate_id>/<int:q_num>')
# def serve_softskills_video(job_id, candidate_id, q_num):
#     """Serve a candidate's recorded answer video to the admin."""
#     if session.get('user_type') != 'admin':
#         return "Unauthorised", 403
#     from flask import send_from_directory
#     video_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
#     filename   = f"q{q_num}.webm"
#     full_path  = os.path.join(video_dir, filename)
#     if not os.path.exists(full_path):
#         return "Recording not found", 404
#     return send_from_directory(video_dir, filename, mimetype='video/webm')

# # Add this function to generate test link
# def generate_test_link(job_id):
#     """Generate the full URL for the test"""
#     from flask import url_for
#     # This will be set when blueprint is registered
#     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)

# # Modify the generate_softskills_questions function to also return a test link
# # def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
# #     """
# #     Generate soft skills questions and return (questions, error, test_link)
# #     Now returns test_link as third value
# #     """
# #     if not GROQ_CLIENT:
# #         return None, "Groq client not available.", None

# #     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# # Each question must:
# # - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# # - Require 60-90 seconds to answer verbally
# # - Test a different soft skill

# # Default marks per question: {marks_per_question}

# # Return a JSON array:
# # [
# #   {{
# #     "q": "<full question text>",
# #     "type": "audio_text",
# #     "skill": "<skill being tested e.g. communication>",
# #     "marks": {marks_per_question},
# #     "options": [],
# #     "answer": "<ideal answer keywords/themes for evaluation>"
# #   }}
# # ]"""

# #     try:
# #         resp = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
# #                 {"role": "user",   "content": prompt}
# #             ],
# #             temperature=0.6,
# #         )
# #         text = resp.choices[0].message.content.strip()
# #         if text.startswith("```"):
# #             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
# #             text = re.sub(r"\n?```$", "", text).strip()
# #         questions = json.loads(text)
# #         if not isinstance(questions, list):
# #             return None, "Unexpected format from Groq.", None
        
# #         # Generate test link
# #         from flask import url_for
# #         test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
        
# #         return questions, None, test_link
# #     except Exception as e:
# #         return None, f"Question generation failed: {e}", None


# def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5, job_id: int = None) -> tuple:
#     """
#     Generate soft skills questions and return (questions, error, test_link)
#     Now accepts job_id as parameter
#     """
#     if not GROQ_CLIENT:
#         return None, "Groq client not available.", None

#     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# Each question must:
# - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# - Require 60-90 seconds to answer verbally
# - Test a different soft skill

# Default marks per question: {marks_per_question}

# Return a JSON array:
# [
#   {{
#     "q": "<full question text>",
#     "type": "audio_text",
#     "skill": "<skill being tested e.g. communication>",
#     "marks": {marks_per_question},
#     "options": [],
#     "answer": "<ideal answer keywords/themes for evaluation>"
#   }}
# ]"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0.6,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         questions = json.loads(text)
#         if not isinstance(questions, list):
#             return None, "Unexpected format from Groq.", None
        
#         # Generate test link only if job_id is provided
#         test_link = None
#         if job_id:
#             from flask import url_for
#             try:
#                 test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
#             except Exception as e:
#                 print(f"Warning: Could not generate test link: {e}")
#                 test_link = None
        
#         return questions, None, test_link
#     except Exception as e:
#         return None, f"Question generation failed: {e}", None


# def get_softskills_test_link(job_id):
#     """Generate the test link for softskills interview"""
#     from flask import url_for
#     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)



# # ------------------------------------------------------------------ #
# #  DB MIGRATION — call once at startup                                #
# # ------------------------------------------------------------------ #
# def create_softskills_table():
#     """Create the softskills_results table if it doesn't exist."""
#     conn = db()
#     conn.execute('''
#         CREATE TABLE IF NOT EXISTS softskills_results (
#             id                INTEGER PRIMARY KEY AUTOINCREMENT,
#             candidate_id      INTEGER NOT NULL,
#             job_id            INTEGER NOT NULL,
#             overall_score     INTEGER DEFAULT 0,
#             fluency_score     INTEGER DEFAULT 0,
#             grammar_score     INTEGER DEFAULT 0,
#             confidence_score  INTEGER DEFAULT 0,
#             relevance_score   INTEGER DEFAULT 0,
#             overall_explanation TEXT,
#             question_details  TEXT,
#             submission_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
#     conn.commit()
#     conn.close()



































































# from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
# import json
# import os
# from datetime import datetime
# import sqlite3
# import re

# softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

# # Database connection function (will be set from app)
# _db_connection = None

# def register_db(conn_func):
#     global _db_connection
#     _db_connection = conn_func

# def get_db():
#     if _db_connection:
#         return _db_connection()
#     return None

# def create_softskills_table():
#     """Create soft skills responses table if it doesn't exist"""
#     conn = get_db()
#     if not conn:
#         return
    
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS softskills_responses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER NOT NULL,
#                 job_id INTEGER NOT NULL,
#                 question_number INTEGER NOT NULL,
#                 question_text TEXT,
#                 audio_path TEXT,
#                 answer_text TEXT,
#                 submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.commit()
#         print("✅ Soft skills responses table created/verified")
#     except Exception as e:
#         print(f"Error creating softskills table: {e}")
#     finally:
#         conn.close()

# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     """Generate soft skills interview questions using Groq"""
#     from app import GROQ_CLIENT
    
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
    
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "audio_text",
#     "options": [],
#     "answer": "Sample ideal answer guide for evaluation"
#   }}
# ]

# Make the questions professional, relevant, and open-ended to allow detailed responses.
# """
        
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
        
#         response_text = completion.choices[0].message.content.strip()
        
#         # Clean up markdown if present
#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
        
#         questions = json.loads(response_text)
        
#         # Generate test link
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
#         return questions, None, test_link
        
#     except Exception as e:
#         print(f"Error generating soft skills questions: {e}")
#         import traceback
#         traceback.print_exc()
#         return None, str(e), None

# @softskills_bp.route('/candidate/view/<int:job_id>')
# def candidate_softskills_view(job_id):
#     """Display soft skills interview page"""
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to take the interview.", 'warning')
#         return redirect(url_for('candidate_login'))
    
#     candidate_id = session['user_id']
#     conn = get_db()
    
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     # Check if already submitted
#     existing = conn.execute(
#         'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
    
#     if existing:
#         conn.close()
#         flash("You have already completed this interview.", 'info')
#         return redirect(url_for('candidate_jobs'))
    
#     # Get test details
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     conn.close()
    
#     if not test:
#         flash("Interview not found.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     # Parse questions
#     questions = []
#     try:
#         if test['questions_json']:
#             questions_json_str = test['questions_json'].strip()
#             if questions_json_str.startswith('```'):
#                 questions_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', questions_json_str)
#                 questions_json_str = re.sub(r'\n?```$', '', questions_json_str)
#             questions = json.loads(questions_json_str)
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         flash("Error loading interview questions.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     return render_template('candidate_softskills_test.html',
#                          test=test,
#                          questions=questions,
#                          job_id=job_id)

# @softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     """Submit soft skills interview answers"""
#     print(f"=== SUBMIT SOFT SKILLS CALLED for job_id: {job_id} ===")
    
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
#     candidate_id = session['user_id']
#     conn = get_db()
    
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
#     try:
#         # Check if already submitted
#         existing = conn.execute(
#             'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#             (candidate_id, job_id)
#         ).fetchone()
        
#         if existing:
#             conn.close()
#             return jsonify({'success': False, 'message': 'You have already submitted this interview'}), 400
        
#         # Get job ID from form
#         job_id_from_form = request.form.get('job_id')
#         if job_id_from_form:
#             job_id = int(job_id_from_form)
        
#         # Create uploads folder if not exists
#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)
        
#         # Process all audio files
#         saved_files = []
#         for key in request.files:
#             if key.startswith('audio_'):
#                 audio_file = request.files[key]
#                 if audio_file and audio_file.filename:
#                     # Generate filename
#                     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     filename = f"candidate_{candidate_id}_job_{job_id}_{key}_{timestamp}.webm"
#                     filepath = os.path.join(upload_folder, filename)
                    
#                     # Save file
#                     audio_file.save(filepath)
#                     saved_files.append(filepath)
                    
#                     # Extract question number from key (audio_1, audio_2, etc.)
#                     question_num = int(key.split('_')[1])
                    
#                     # Get answer text
#                     answer_key = f"answer_{question_num}"
#                     answer_text = request.form.get(answer_key, '')
                    
#                     # Save to database
#                     conn.execute('''
#                         INSERT INTO softskills_responses 
#                         (candidate_id, job_id, question_number, audio_path, answer_text)
#                         VALUES (?, ?, ?, ?, ?)
#                     ''', (candidate_id, job_id, question_num, filename, answer_text))
        
#         # Update application status
#         conn.execute('''
#             UPDATE applications 
#             SET status = 'Test Completed' 
#             WHERE candidate_id = ? AND job_id = ?
#         ''', (candidate_id, job_id))
        
#         # Also update test_results table for consistency
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results 
#             (candidate_id, job_id, score, submitted_answers_json)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
        
#         conn.commit()
        
#         print(f"✅ Soft skills interview submitted successfully for candidate {candidate_id}")
#         print(f"   Saved {len(saved_files)} audio files")
        
#         return jsonify({
#             'success': True, 
#             'message': 'Interview submitted successfully',
#             'files_saved': len(saved_files)
#         })
        
#     except Exception as e:
#         print(f"❌ Error submitting soft skills: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         if conn:
#             conn.close()



# @softskills_bp.route('/admin/results/<int:job_id>')
# def admin_softskills_results(job_id):
#     """View soft skills interview results for admin"""
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))
    
#     conn = get_db()
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('admin_dashboard'))
    
#     try:
#         # Get job details
#         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
        
#         # Get all soft skills responses for this job
#         responses = conn.execute('''
#             SELECT 
#                 sr.*,
#                 c.name as candidate_name,
#                 c.email as candidate_email
#             FROM softskills_responses sr
#             JOIN candidates c ON sr.candidate_id = c.id
#             WHERE sr.job_id = ?
#             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
#         ''', (job_id,)).fetchall()
        
#         # Group responses by candidate
#         candidates_dict = {}
#         for response in responses:
#             candidate_id = response['candidate_id']
#             if candidate_id not in candidates_dict:
#                 candidates_dict[candidate_id] = {
#                     'candidate_id': candidate_id,
#                     'candidate_name': response['candidate_name'],
#                     'candidate_email': response['candidate_email'],
#                     'responses': [],
#                     'submission_time': response['submission_time']
#                 }
#             candidates_dict[candidate_id]['responses'].append({
#                 'question_number': response['question_number'],
#                 'question_text': response['question_text'],
#                 'audio_path': response['audio_path'],
#                 'answer_text': response['answer_text']
#             })
        
#         candidates_list = list(candidates_dict.values())
        
#         return render_template('admin_softskills_results.html', 
#                              job=job, 
#                              candidates=candidates_list,
#                              job_id=job_id)
#     except Exception as e:
#         print(f"Error viewing soft skills results: {e}")
#         flash(f"Error loading results: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         conn.close()



# @softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
# def log_proctor_event(job_id):
#     """Log proctor events for soft skills interview"""
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
#     candidate_id = session['user_id']
#     data = request.get_json()
#     event_type = data.get('event_type')
#     details = data.get('details', '')
    
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
    
#     try:
#         # Create proctor_logs table if not exists
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS proctor_logs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER,
#                 job_id INTEGER,
#                 event_type TEXT,
#                 details TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         conn.execute('''
#             INSERT INTO proctor_logs (candidate_id, job_id, event_type, details)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, event_type, details))
#         conn.commit()
#         return jsonify({'success': True})
#     except Exception as e:
#         print(f"Error logging proctor event: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()

# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     """Generate soft skills interview questions using Groq"""
#     from app import GROQ_CLIENT
    
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
    
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "audio_text",
#     "options": [],
#     "answer": "Sample ideal answer guide for evaluation"
#   }}
# ]

# Make the questions professional, relevant, and open-ended to allow detailed responses.
# """
        
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
        
#         response_text = completion.choices[0].message.content.strip()
        
#         # Clean up markdown if present
#         if response_text.startswith('```'):
#             import re
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
        
#         questions = json.loads(response_text)
        
#         # Generate test link
#         from flask import url_for
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
#         return questions, None, test_link
        
#     except Exception as e:
#         print(f"Error generating soft skills questions: {e}")
#         import traceback
#         traceback.print_exc()
#         return None, str(e), None












































































































# from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify, send_from_directory
# import json
# import os
# import base64
# from datetime import datetime
# import sqlite3
# import re

# softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

# _db_connection = None

# def register_db(conn_func):
#     global _db_connection
#     _db_connection = conn_func

# def get_db():
#     if _db_connection:
#         return _db_connection()
#     return None

# def create_softskills_table():
#     """Create soft skills responses table if it doesn't exist"""
#     conn = get_db()
#     if not conn:
#         return
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS softskills_responses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER NOT NULL,
#                 job_id INTEGER NOT NULL,
#                 question_number INTEGER NOT NULL,
#                 question_text TEXT,
#                 audio_path TEXT,
#                 answer_text TEXT,
#                 transcript TEXT,
#                 submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Migrate older schema that may not have transcript column
#         try:
#             conn.execute('ALTER TABLE softskills_responses ADD COLUMN transcript TEXT')
#         except Exception:
#             pass  # Column already exists — that's fine
#         conn.commit()
#         print("✅ Soft skills responses table created/verified")
#     except Exception as e:
#         print(f"Error creating softskills table: {e}")
#     finally:
#         conn.close()


# # ── Groq Whisper transcription ────────────────────────────────────────────────
# def transcribe_audio_file(filepath):
#     """
#     Transcribe an audio/video file using Groq Whisper.
#     Returns (transcript_text, error_message).
#     Groq Whisper supports: mp3, mp4, mpeg, mpga, m4a, wav, webm
#     """
#     from app import GROQ_CLIENT
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialised — check GROQ_API_KEY"

#     if not filepath or not os.path.exists(filepath):
#         return None, f"File not found: {filepath}"

#     try:
#         with open(filepath, 'rb') as f:
#             # Pass explicit content-type so Groq knows how to decode the container
#             transcription = GROQ_CLIENT.audio.transcriptions.create(
#                 file=(os.path.basename(filepath), f, 'audio/webm'),
#                 model='whisper-large-v3',
#                 language='en',
#                 response_format='text'   # returns a plain string, not JSON
#             )
#         transcript = str(transcription).strip()
#         return (transcript if transcript else "(No speech detected)"), None
#     except Exception as e:
#         print(f"Whisper transcription error for {filepath}: {e}")
#         return None, str(e)


# # ── Question generation ───────────────────────────────────────────────────────
# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     from app import GROQ_CLIENT
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.
# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.
# Return ONLY a JSON array:
# [{{"q":"Question text?","type":"audio_text","options":[],"answer":"Ideal answer guide"}}]
# """
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": "You are a professional HR assessment generator. Always respond with valid JSON only."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
#         response_text = completion.choices[0].message.content.strip()
#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
#         questions = json.loads(response_text)
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
#         return questions, None, test_link
#     except Exception as e:
#         print(f"Error generating questions: {e}")
#         import traceback; traceback.print_exc()
#         return None, str(e), None


# # ── Candidate routes ──────────────────────────────────────────────────────────
# @softskills_bp.route('/candidate/view/<int:job_id>')
# def candidate_softskills_view(job_id):
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to take the interview.", 'warning')
#         return redirect(url_for('candidate_login'))
#     candidate_id = session['user_id']
#     conn = get_db()
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('candidate_jobs'))
#     existing = conn.execute(
#         'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
#     if existing:
#         conn.close()
#         flash("You have already completed this interview.", 'info')
#         return redirect(url_for('candidate_jobs'))
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     conn.close()
#     if not test:
#         flash("Interview not found.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     questions = []
#     try:
#         if test['questions_json']:
#             qs = test['questions_json'].strip()
#             if qs.startswith('```'):
#                 qs = re.sub(r'^```[a-zA-Z]*\n?', '', qs)
#                 qs = re.sub(r'\n?```$', '', qs)
#             questions = json.loads(qs)
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         flash("Error loading interview questions.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     return render_template('candidate_softskills_test.html', test=test, questions=questions, job_id=job_id)


# @softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     print(f"=== SUBMIT SOFT SKILLS for job_id={job_id} ===")
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
#     candidate_id = session['user_id']
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database connection error'}), 500
#     try:
#         existing = conn.execute(
#             'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#             (candidate_id, job_id)
#         ).fetchone()
#         if existing:
#             conn.close()
#             return jsonify({'success': False, 'message': 'Already submitted'}), 400

#         if request.form.get('job_id'):
#             job_id = int(request.form.get('job_id'))

#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)

#         saved_files = []
#         total_questions = 0

#         all_keys = list(request.form.keys()) + list(request.files.keys())
#         q_indices = set()
#         for key in all_keys:
#             if key.startswith('audio_') or key.startswith('answer_'):
#                 try:
#                     q_indices.add(int(key.split('_')[1]))
#                 except:
#                     pass

#         for question_num in sorted(q_indices):
#             answer_text = request.form.get(f'answer_{question_num}', '')
#             audio_path_db = None

#             # 1) Multipart file upload (from AI interview page)
#             if f'audio_{question_num}' in request.files:
#                 af = request.files[f'audio_{question_num}']
#                 if af and af.filename:
#                     ct = af.content_type or 'video/webm'
#                     ext = 'mp4' if 'mp4' in ct else 'webm'
#                     ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.{ext}"
#                     filepath = os.path.join(upload_folder, filename)
#                     af.save(filepath)
#                     audio_path_db = filename
#                     saved_files.append(filepath)
#                     print(f"  ✅ Saved Q{question_num}: {filename} ({ct})")

#             # 2) Base64 in audio_N form field
#             if not audio_path_db:
#                 b64 = request.form.get(f'audio_{question_num}', '')
#                 if b64.startswith('data:'):
#                     try:
#                         _, enc = b64.split(',', 1)
#                         data = base64.b64decode(enc)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(data)
#                         audio_path_db = filename
#                         saved_files.append(filepath)
#                     except Exception as e:
#                         print(f"  ⚠️ base64 audio_{question_num}: {e}")

#             # 3) Base64 in q_N form field
#             if not audio_path_db:
#                 qv = request.form.get(f'q_{question_num}', '')
#                 if qv.startswith('data:'):
#                     try:
#                         _, enc = qv.split(',', 1)
#                         data = base64.b64decode(enc)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(data)
#                         audio_path_db = filename
#                         saved_files.append(filepath)
#                     except Exception as e:
#                         print(f"  ⚠️ base64 q_{question_num}: {e}")
#                 elif qv:
#                     answer_text = qv

#             conn.execute('''
#                 INSERT INTO softskills_responses
#                 (candidate_id, job_id, question_number, audio_path, answer_text)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (candidate_id, job_id, question_num, audio_path_db, answer_text))
#             total_questions += 1

#         # Standard q_N keys
#         for key in [k for k in request.form.keys() if re.match(r'^q_\d+$', k)]:
#             try:
#                 qn = int(key.split('_')[1])
#             except:
#                 continue
#             if qn in q_indices:
#                 continue
#             val = request.form.get(key, '')
#             apath = None
#             atext = ''
#             if val.startswith('data:'):
#                 try:
#                     _, enc = val.split(',', 1)
#                     data = base64.b64decode(enc)
#                     ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     fn = f"candidate_{candidate_id}_job_{job_id}_q{qn}_{ts}.webm"
#                     fp = os.path.join(upload_folder, fn)
#                     with open(fp, 'wb') as fh:
#                         fh.write(data)
#                     apath = fn
#                     saved_files.append(fp)
#                 except Exception as e:
#                     print(f"  ⚠️ q_{qn}: {e}")
#                     atext = val
#             else:
#                 atext = val
#             conn.execute('''
#                 INSERT INTO softskills_responses
#                 (candidate_id, job_id, question_number, audio_path, answer_text)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (candidate_id, job_id, qn, apath, atext))
#             total_questions += 1

#         conn.execute(
#             "UPDATE applications SET status='Test Completed' WHERE candidate_id=? AND job_id=?",
#             (candidate_id, job_id)
#         )
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results (candidate_id, job_id, score, submitted_answers_json)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
#         conn.commit()
#         print(f"✅ Done: {len(saved_files)} files, {total_questions} questions")
#         return jsonify({'success': True, 'message': 'Interview submitted successfully', 'files_saved': len(saved_files)})
#     except Exception as e:
#         print(f"❌ Submit error: {e}")
#         import traceback; traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         if conn:
#             conn.close()


# # ── Serve video/audio files ───────────────────────────────────────────────────
# @softskills_bp.route('/audio/<path:filename>')
# def serve_softskills_audio(filename):
#     """
#     Serve candidate video recordings to admin.
#     Implements HTTP Range requests so browsers can seek and render video frames.
#     """
#     if session.get('user_type') != 'admin':
#         return jsonify({'error': 'Unauthorized'}), 403

#     import re as _re
#     from flask import Response

#     audio_dir = os.path.join(os.getcwd(), 'uploads', 'softskills_audio')
#     filepath  = os.path.join(audio_dir, filename)

#     if not os.path.exists(filepath):
#         return jsonify({'error': 'File not found'}), 404

#     mimetype  = 'video/mp4' if filename.endswith('.mp4') else 'video/webm'
#     file_size = os.path.getsize(filepath)

#     range_header = request.headers.get('Range', None)

#     if range_header:
#         m = _re.match(r'bytes=(\d+)-(\d*)', range_header)
#         if m:
#             start  = int(m.group(1))
#             end    = int(m.group(2)) if m.group(2) else file_size - 1
#             end    = min(end, file_size - 1)
#             length = end - start + 1

#             with open(filepath, 'rb') as f:
#                 f.seek(start)
#                 chunk = f.read(length)

#             rv = Response(chunk, 206, mimetype=mimetype, direct_passthrough=True)
#             rv.headers['Content-Range']  = f'bytes {start}-{end}/{file_size}'
#             rv.headers['Accept-Ranges']  = 'bytes'
#             rv.headers['Content-Length'] = str(length)
#             rv.headers['Cache-Control']  = 'no-cache'
#             return rv

#     # Full file
#     with open(filepath, 'rb') as f:
#         data = f.read()

#     rv = Response(data, 200, mimetype=mimetype)
#     rv.headers['Accept-Ranges']  = 'bytes'
#     rv.headers['Content-Length'] = str(file_size)
#     rv.headers['Cache-Control']  = 'no-cache'
#     return rv


# # ── On-demand Groq Whisper transcription ─────────────────────────────────────
# @softskills_bp.route('/admin/transcribe/<int:response_id>', methods=['POST'])
# def admin_transcribe(response_id):
#     """Transcribe one response's recording using Groq Whisper. Admin only."""
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
#     try:
#         row = conn.execute(
#             'SELECT id, audio_path, transcript FROM softskills_responses WHERE id = ?',
#             (response_id,)
#         ).fetchone()

#         if not row:
#             return jsonify({'success': False, 'message': 'Response not found'}), 404

#         # Return cached transcript instantly
#         if row['transcript']:
#             return jsonify({'success': True, 'transcript': row['transcript'], 'cached': True})

#         if not row['audio_path']:
#             return jsonify({'success': False, 'message': 'No audio file attached to this response'}), 400

#         filepath = os.path.join('uploads', 'softskills_audio', row['audio_path'])
#         transcript, error = transcribe_audio_file(filepath)

#         if error:
#             return jsonify({'success': False, 'message': f'Transcription failed: {error}'}), 500

#         # Persist so next call is instant
#         conn.execute(
#             'UPDATE softskills_responses SET transcript = ? WHERE id = ?',
#             (transcript, response_id)
#         )
#         conn.commit()
#         return jsonify({'success': True, 'transcript': transcript, 'cached': False})

#     except Exception as e:
#         print(f"Transcription error: {e}")
#         import traceback; traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# # ── Admin results page ────────────────────────────────────────────────────────
# # @softskills_bp.route('/admin/results/<int:job_id>')
# # def admin_softskills_results(job_id):
# #     if session.get('user_type') != 'admin':
# #         flash("Unauthorized access.", 'warning')
# #         return redirect(url_for('admin_login'))
# #     conn = get_db()
# #     if not conn:
# #         flash("Database connection error", 'error')
# #         return redirect(url_for('admin_dashboard'))
# #     try:
# #         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
# #         responses = conn.execute('''
# #             SELECT sr.*, c.name as candidate_name, c.email as candidate_email
# #             FROM softskills_responses sr
# #             JOIN candidates c ON sr.candidate_id = c.id
# #             WHERE sr.job_id = ?
# #             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
# #         ''', (job_id,)).fetchall()

# #         candidates_dict = {}
# #         for r in responses:
# #             cid = r['candidate_id']
# #             if cid not in candidates_dict:
# #                 candidates_dict[cid] = {
# #                     'candidate_id': cid,
# #                     'candidate_name': r['candidate_name'],
# #                     'candidate_email': r['candidate_email'],
# #                     'responses': [],
# #                     'submission_time': r['submission_time']
# #                 }
# #             audio_url = None
# #             if r['audio_path']:
# #                 audio_url = url_for('softskills.serve_softskills_audio', filename=r['audio_path'])

# #             candidates_dict[cid]['responses'].append({
# #                 'id': r['id'],
# #                 'question_number': r['question_number'],
# #                 'question_text': r['question_text'],
# #                 'audio_path': r['audio_path'],
# #                 'audio_url': audio_url,
# #                 'answer_text': r['answer_text'],
# #                 'transcript': r['transcript'] if r['transcript'] else None,
# #             })

# #         return render_template('admin_softskills_results.html',
# #                                job=job,
# #                                candidates=list(candidates_dict.values()),
# #                                job_id=job_id)
# #     except Exception as e:
# #         print(f"Results error: {e}")
# #         flash(f"Error loading results: {e}", 'error')
# #         return redirect(url_for('admin_dashboard'))
# #     finally:
# #         conn.close()



# @softskills_bp.route('/admin/results/<int:job_id>')
# def admin_softskills_results(job_id):
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     conn = get_db()
#     try:
#         # 1. Fetch the job details for the template header
#         job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()

#         # 2. Fetch all softskills_responses rows directly (source of truth for submissions)
#         responses = conn.execute('''
#             SELECT
#                 c.id AS candidate_id, c.name, c.email,
#                 r.id AS response_id,
#                 r.question_number, r.question_text, r.audio_path,
#                 r.answer_text, r.transcript,
#                 r.submission_time
#             FROM softskills_responses r
#             JOIN candidates c ON r.candidate_id = c.id
#             WHERE r.job_id = ?
#             ORDER BY c.id, r.question_number
#         ''', (job_id,)).fetchall()

#         candidates_dict = {}
#         for row in responses:
#             cid = row['candidate_id']
#             if cid not in candidates_dict:
#                 candidates_dict[cid] = {
#                     'candidate_id': cid,
#                     'candidate_name': row['name'],
#                     'candidate_email': row['email'],
#                     'submission_time': row['submission_time'] or 'Recently',
#                     'responses': []
#                 }
#             audio_url = None
#             if row['audio_path']:
#                 audio_url = url_for('softskills.serve_softskills_audio', filename=row['audio_path'])
#             candidates_dict[cid]['responses'].append({
#                 'id': row['response_id'],
#                 'question_number': row['question_number'],
#                 'question_text': row['question_text'],
#                 'audio_path': row['audio_path'],
#                 'audio_url': audio_url,
#                 'answer_text': row['answer_text'],
#                 'transcript': row['transcript'],
#             })
                
#         return render_template('admin_softskills_results.html',
#                                job=job,
#                                candidates=list(candidates_dict.values()),
#                                job_id=job_id)
                               
#     except Exception as e:
#         print(f"Results error: {e}")
#         flash(f"Error loading results: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         conn.close()

# # ── Proctor event logging ─────────────────────────────────────────────────────
# @softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
# def log_proctor_event(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
#     candidate_id = session['user_id']
#     data = request.get_json()
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS proctor_logs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER, job_id INTEGER,
#                 event_type TEXT, details TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (candidate_id, job_id, data.get('event_type'), data.get('details', ''))
#         )
#         conn.commit()
#         return jsonify({'success': True})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


















































































# """
# softskills_routes.py
# Handles:
#   - AI question generation  (Groq)
#   - Candidate interview view
#   - Recording submission + evaluation pipeline
#       * AssemblyAI  → speech-to-text + fluency metrics
#       * LanguageTool → grammar / spelling errors
#       * Groq AI      → confidence / relevance / tone scoring
#   - Admin results view
# """

# import os, json, re, time, math, requests, tempfile
# from flask import (Blueprint, render_template, request, redirect,
#                    url_for, session, flash, jsonify)
# from datetime import datetime
# from groq import Groq

# softskills_bp = Blueprint('softskills', __name__)

# # ------------------------------------------------------------------ #
# #  CLIENTS                                                             #
# # ------------------------------------------------------------------ #
# GROQ_CLIENT = None
# try:
#     _key = os.getenv("GROQ_API_KEY")
#     if _key:
#         GROQ_CLIENT = Groq(api_key=_key)
# except Exception as e:
#     print(f"Softskills: Groq client failed: {e}")

# ASSEMBLYAI_KEY   = os.getenv("ASSEMBLYAI_API_KEY", "")
# LANGUAGETOOL_URL = "https://api.languagetoolplus.com/v2/check"   # free tier works
# LT_API_KEY       = os.getenv("LANGUAGETOOL_API_KEY", "")         # optional, works without

# # ------------------------------------------------------------------ #
# #  DB helper (imported from main app at registration time)           #
# # ------------------------------------------------------------------ #
# _get_db = None   # set via register_db(fn) below

# def register_db(fn):
#     global _get_db
#     _get_db = fn

# def db():
#     return _get_db()

# # ------------------------------------------------------------------ #
# #  QUESTION GENERATION                                                #
# # ------------------------------------------------------------------ #
# SOFT_SKILLS_SYSTEM = """You are an expert HR interviewer creating scenario-based spoken interview questions.
# Questions must require a verbal, conversational answer — NOT multiple choice.
# Focus on: communication, confidence, teamwork, conflict resolution, leadership, self-awareness.
# Return ONLY a valid JSON array. No markdown fences, no prose."""

# def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
#     if not GROQ_CLIENT:
#         return None, "Groq client not available."

#     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# Each question must:
# - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# - Require 60-90 seconds to answer verbally
# - Test a different soft skill

# Default marks per question: {marks_per_question}

# Return a JSON array:
# [
#   {{
#     "q": "<full question text>",
#     "type": "audio_text",
#     "skill": "<skill being tested e.g. communication>",
#     "marks": {marks_per_question},
#     "options": [],
#     "answer": "<ideal answer keywords/themes for evaluation>"
#   }}
# ]"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0.6,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         questions = json.loads(text)
#         if not isinstance(questions, list):
#             return None, "Unexpected format from Groq."
#         return questions, None
#     except Exception as e:
#         return None, f"Question generation failed: {e}"

# # ------------------------------------------------------------------ #
# #  ASSEMBLYAI — speech to text + fluency                              #
# # ------------------------------------------------------------------ #
# def transcribe_with_assemblyai(audio_path: str) -> dict:
#     """Upload audio file to AssemblyAI, poll for result, return metrics."""
#     base = {"transcript": "", "filler_count": 0, "pause_count": 0,
#             "words_per_minute": 0, "confidence": 0.0, "error": None}

#     if not ASSEMBLYAI_KEY:
#         base["error"] = "ASSEMBLYAI_API_KEY not set"
#         return base

#     headers = {"authorization": ASSEMBLYAI_KEY, "content-type": "application/json"}

#     try:
#         # 1. Upload file
#         with open(audio_path, "rb") as f:
#             up = requests.post("https://api.assemblyai.com/v2/upload",
#                                headers={"authorization": ASSEMBLYAI_KEY},
#                                data=f, timeout=60)
#         upload_url = up.json()["upload_url"]

#         # 2. Submit transcription with IAB + auto_chapters disabled, but keep disfluencies
#         payload = {
#             "audio_url": upload_url,
#             "disfluencies": True,       # keeps uh, um in transcript
#             "auto_highlights": True,    # key phrase extraction
#             "punctuate": True,
#             "format_text": True,
#         }
#         job = requests.post("https://api.assemblyai.com/v2/transcript",
#                             headers=headers, json=payload, timeout=30).json()
#         job_id = job["id"]

#         # 3. Poll (max 120s)
#         for _ in range(60):
#             time.sleep(2)
#             result = requests.get(f"https://api.assemblyai.com/v2/transcript/{job_id}",
#                                   headers=headers, timeout=15).json()
#             if result["status"] == "completed":
#                 break
#             if result["status"] == "error":
#                 base["error"] = result.get("error", "AssemblyAI error")
#                 return base

#         transcript_text = result.get("text") or ""
#         words           = result.get("words") or []
#         duration_sec    = (result.get("audio_duration") or 1)

#         # Words per minute
#         wpm = round(len(words) / (duration_sec / 60)) if duration_sec > 0 else 0

#         # Filler word count (uh, um, like, you know, basically)
#         filler_re = re.compile(r'\b(uh+|um+|uhm|like|you know|basically|so|right|okay)\b', re.I)
#         filler_count = len(filler_re.findall(transcript_text))

#         # Long pauses (gaps > 1.5s between consecutive words)
#         pause_count = 0
#         for i in range(1, len(words)):
#             gap = (words[i].get("start", 0) - words[i-1].get("end", 0)) / 1000.0
#             if gap > 1.5:
#                 pause_count += 1

#         # Average word confidence
#         confidences = [w.get("confidence", 0) for w in words if "confidence" in w]
#         avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

#         return {
#             "transcript":    transcript_text,
#             "filler_count":  filler_count,
#             "pause_count":   pause_count,
#             "words_per_minute": wpm,
#             "confidence":    avg_conf,
#             "error":         None,
#         }

#     except Exception as e:
#         base["error"] = str(e)
#         return base

# # ------------------------------------------------------------------ #
# #  LANGUAGETOOL — grammar check                                        #
# # ------------------------------------------------------------------ #
# def check_grammar(text: str) -> dict:
#     """Return count of grammar/spelling/style errors + list of issues."""
#     base = {"error_count": 0, "errors": [], "error": None}
#     if not text or len(text.strip()) < 10:
#         return base
#     try:
#         params = {
#             "text": text, "language": "en-US",
#             "enabledOnly": "false",
#         }
#         if LT_API_KEY:
#             params["apiKey"] = LT_API_KEY

#         resp = requests.post(LANGUAGETOOL_URL, data=params, timeout=20)
#         matches = resp.json().get("matches", [])
#         errors = [
#             {
#                 "message": m.get("message", ""),
#                 "context": m.get("context", {}).get("text", ""),
#                 "rule":    m.get("rule", {}).get("issueType", ""),
#             }
#             for m in matches[:10]   # cap at 10 for display
#         ]
#         return {"error_count": len(matches), "errors": errors, "error": None}
#     except Exception as e:
#         base["error"] = str(e)
#         return base

# # ------------------------------------------------------------------ #
# #  GROQ — confidence / relevance / tone scoring                        #
# # ------------------------------------------------------------------ #
# def score_answer_with_groq(question: str, ideal_themes: str, transcript: str,
#                             fluency_metrics: dict) -> dict:
#     """Ask Groq to score confidence, relevance, tone and give explanation."""
#     base = {"confidence": 50, "relevance": 50, "tone": 50,
#             "positivity": 50, "explanation": "AI scoring unavailable."}

#     if not GROQ_CLIENT or not transcript:
#         return base

#     prompt = f"""You are an expert HR assessor scoring a spoken interview answer.

# Question: {question}
# Ideal answer themes: {ideal_themes}
# Candidate transcript: {transcript}
# Fluency metrics: WPM={fluency_metrics.get('words_per_minute',0)}, fillers={fluency_metrics.get('filler_count',0)}, long pauses={fluency_metrics.get('pause_count',0)}

# Score each dimension from 0-100:
# - confidence: Does the candidate sound sure and assertive?
# - relevance: Does the answer address the question and ideal themes?
# - tone: Is the tone professional and appropriate?
# - positivity: Is the candidate's attitude positive and constructive?

# Return ONLY valid JSON:
# {{
#   "confidence": <int>,
#   "relevance": <int>,
#   "tone": <int>,
#   "positivity": <int>,
#   "explanation": "<2-3 sentences explaining the evaluation>"
# }}"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": "You are an HR evaluation expert. Reply with valid JSON only."},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         result = json.loads(text)
#         return {
#             "confidence":  max(0, min(100, int(result.get("confidence",  50)))),
#             "relevance":   max(0, min(100, int(result.get("relevance",   50)))),
#             "tone":        max(0, min(100, int(result.get("tone",        50)))),
#             "positivity":  max(0, min(100, int(result.get("positivity",  50)))),
#             "explanation": result.get("explanation", ""),
#         }
#     except Exception as e:
#         base["explanation"] = f"AI scoring error: {e}"
#         return base

# # ------------------------------------------------------------------ #
# #  SCORING AGGREGATION                                                 #
# # ------------------------------------------------------------------ #
# def compute_fluency_score(metrics: dict) -> int:
#     """Convert raw fluency metrics to a 0-100 score."""
#     wpm        = metrics.get("words_per_minute", 0)
#     fillers    = metrics.get("filler_count", 0)
#     pauses     = metrics.get("pause_count", 0)
#     conf       = metrics.get("confidence", 0.5) * 100   # 0-100

#     # WPM score: ideal 120-160 wpm for spoken English
#     if   wpm == 0:      wpm_score = 20
#     elif wpm < 80:      wpm_score = 50
#     elif wpm < 120:     wpm_score = 75
#     elif wpm <= 170:    wpm_score = 100
#     else:               wpm_score = 70   # too fast

#     # Penalty: each filler -3pts, each long pause -5pts
#     penalty = min(50, fillers * 3 + pauses * 5)
#     raw = (wpm_score * 0.4) + (conf * 0.4) - penalty * 0.2
#     return max(0, min(100, round(raw)))

# def compute_grammar_score(grammar: dict) -> int:
#     errors = grammar.get("error_count", 0)
#     if   errors == 0: return 100
#     elif errors <= 2: return 85
#     elif errors <= 5: return 65
#     elif errors <= 10: return 45
#     else:              return 25

# def aggregate_scores(question_results: list, questions: list) -> dict:
#     """Average all per-question scores into weighted totals using marks per question."""
#     n = len(question_results)
#     if n == 0:
#         return {"fluency": 0, "grammar": 0, "confidence": 0, "relevance": 0, "overall": 0,
#                 "total_marks": 0, "marks_obtained": 0}

#     # Total possible marks
#     total_marks = sum(int(q.get('marks', 5)) for q in questions) if questions else n * 5

#     def avg(key):
#         return round(sum(q.get(key, 0) for q in question_results) / n)

#     fluency    = avg("fluency_score")
#     grammar    = avg("grammar_score")
#     confidence = avg("confidence_score")
#     relevance  = avg("relevance_score")

#     # Marks obtained = weighted by per-question marks
#     marks_obtained = 0
#     for i, qr in enumerate(question_results):
#         q_marks  = int(questions[i].get('marks', 5)) if i < len(questions) else 5
#         # Average of 4 dimensions as 0-1 ratio, multiplied by question marks
#         ratio = (qr.get('fluency_score', 0) + qr.get('grammar_score', 0) +
#                  qr.get('confidence_score', 0) + qr.get('relevance_score', 0)) / 400.0
#         marks_obtained += round(ratio * q_marks, 2)

#     overall = round((marks_obtained / total_marks) * 100) if total_marks > 0 else 0
#     overall = max(0, min(100, overall))

#     return {
#         "fluency":        fluency,
#         "grammar":        grammar,
#         "confidence":     confidence,
#         "relevance":      relevance,
#         "overall":        overall,
#         "total_marks":    total_marks,
#         "marks_obtained": round(marks_obtained, 1),
#     }

# # ------------------------------------------------------------------ #
# #  ROUTES                                                              #
# # ------------------------------------------------------------------ #

# @softskills_bp.route('/candidate/softskills/test/<int:job_id>')
# def candidate_softskills_view(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = db()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     app_row = conn.execute(
#         'SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?',
#         (job_id, candidate_id)
#     ).fetchone()
#     already = conn.execute(
#         'SELECT id FROM softskills_results WHERE job_id = ? AND candidate_id = ?',
#         (job_id, candidate_id)
#     ).fetchone()
#     conn.close()

#     if not test or not app_row or app_row['status'] != 'Selected for Test':
#         flash("Not authorised for this interview.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     if already:
#         flash("You have already completed this soft skills interview.", 'info')
#         return redirect(url_for('candidate_jobs'))

#     questions = json.loads(test['questions_json']) if test['questions_json'] else []
#     if not questions:
#         flash("No questions configured for this interview.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     return render_template('candidate_softskills_test.html',
#                            test=test, questions=questions, job_id=job_id)


# @softskills_bp.route('/candidate/softskills/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = db()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if not test:
#         conn.close()
#         flash("Test not found.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     questions  = json.loads(test['questions_json'])
#     upload_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
#     os.makedirs(upload_dir, exist_ok=True)

#     question_results = []

#     for idx, q in enumerate(questions):
#         file_key = f"answer_{idx + 1}"
#         audio_file = request.files.get(file_key)

#         q_result = {
#             "question":      q.get("q", ""),
#             "skill":         q.get("skill", ""),
#             "marks":         q.get("marks", 10),
#             "transcript":    "",
#             "fluency_score": 50,
#             "grammar_score": 50,
#             "confidence_score": 50,
#             "relevance_score":  50,
#             "filler_words":  0,
#             "pauses":        0,
#             "grammar_errors": 0,
#             "explanation":   "No recording submitted.",
#             "recording_path": None,   # ← stored so admin can play it back
#         }

#         if audio_file and audio_file.filename:
#             save_path = os.path.join(upload_dir, f"q{idx+1}.webm")
#             audio_file.save(save_path)

#             # Store relative path for later playback
#             relative_path = os.path.join('softskills', str(job_id), str(candidate_id), f"q{idx+1}.webm")
#             q_result["recording_path"] = relative_path

#             # 1. Speech-to-text + fluency (AssemblyAI)
#             fluency_data = transcribe_with_assemblyai(save_path)
#             transcript   = fluency_data.get("transcript", "")

#             # 2. Grammar check (LanguageTool)
#             grammar_data = check_grammar(transcript)

#             # 3. AI scoring (Groq)
#             ai_scores = score_answer_with_groq(
#                 question     = q.get("q", ""),
#                 ideal_themes = q.get("answer", ""),
#                 transcript   = transcript,
#                 fluency_metrics = fluency_data,
#             )

#             fluency_score  = compute_fluency_score(fluency_data)
#             grammar_score  = compute_grammar_score(grammar_data)

#             q_result.update({
#                 "transcript":       transcript,
#                 "fluency_score":    fluency_score,
#                 "grammar_score":    grammar_score,
#                 "confidence_score": ai_scores["confidence"],
#                 "relevance_score":  ai_scores["relevance"],
#                 "filler_words":     fluency_data.get("filler_count", 0),
#                 "pauses":           fluency_data.get("pause_count", 0),
#                 "grammar_errors":   grammar_data.get("error_count", 0),
#                 "explanation":      ai_scores.get("explanation", ""),
#             })

#         question_results.append(q_result)

#     # Aggregate with per-question marks
#     totals = aggregate_scores(question_results, questions)

#     # Build overall explanation via Groq
#     overall_explanation = "Evaluation based on fluency, grammar, confidence and answer relevance."
#     if GROQ_CLIENT:
#         try:
#             summary_prompt = f"""Summarise this candidate's overall soft skills interview performance in 3 sentences.
# Scores: Fluency={totals['fluency']}, Grammar={totals['grammar']}, Confidence={totals['confidence']}, Relevance={totals['relevance']}, Overall={totals['overall']}
# Per-question notes: {'; '.join([r.get('explanation','') for r in question_results][:3])}
# Be specific and professional. Mention strengths and areas for improvement."""
#             r = GROQ_CLIENT.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=[{"role": "user", "content": summary_prompt}],
#                 temperature=0.3,
#             )
#             overall_explanation = r.choices[0].message.content.strip()
#         except Exception:
#             pass

#     # Save to DB
#     try:
#         conn.execute('''
#             INSERT INTO softskills_results
#               (candidate_id, job_id, overall_score, fluency_score, grammar_score,
#                confidence_score, relevance_score, overall_explanation, question_details)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             candidate_id, job_id,
#             totals['overall'], totals['fluency'], totals['grammar'],
#             totals['confidence'], totals['relevance'],
#             overall_explanation,
#             json.dumps(question_results),
#         ))
#         conn.execute(
#             "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#             (candidate_id, job_id)
#         )
#         conn.commit()
#         flash(f"Interview submitted! Score: {totals['overall']}/100 "
#               f"({totals['marks_obtained']}/{totals['total_marks']} marks)", 'success')
#     except Exception as e:
#         flash(f"Error saving results: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))


# @softskills_bp.route('/candidate/softskills/proctor_log/<int:job_id>', methods=['POST'])
# def softskills_proctor_log(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'ok': False}), 403
#     event = request.json.get('event', 'unknown')
#     conn = db()
#     try:
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (session['user_id'], job_id, 'softskills_proctor', event)
#         )
#         conn.commit()
#     except Exception:
#         pass
#     finally:
#         conn.close()
#     return jsonify({'ok': True})


# @softskills_bp.route('/admin/softskills_shortlist/<int:job_id>', methods=['POST'])
# def admin_softskills_shortlist(job_id):
#     """Send congratulations messages to all candidates above the threshold score."""
#     if session.get('user_type') != 'admin':
#         return jsonify({'ok': False, 'message': 'Unauthorised'}), 403

#     threshold = int(request.json.get('threshold', 60))
#     conn = db()
#     try:
#         # Get all candidates above threshold for this job
#         rows = conn.execute('''
#             SELECT r.candidate_id, r.overall_score, c.name
#             FROM softskills_results r
#             JOIN candidates c ON r.candidate_id = c.id
#             WHERE r.job_id = ? AND r.overall_score >= ?
#         ''', (job_id, threshold)).fetchall()

#         if not rows:
#             return jsonify({'ok': False, 'message': f'No candidates scored {threshold} or above.'})

#         count = 0
#         for row in rows:
#             # Check if message already sent to avoid duplicates
#             existing = conn.execute('''
#                 SELECT id FROM messages
#                 WHERE candidate_id = ? AND job_id = ?
#                 AND subject LIKE '%Selected for Next Round%'
#             ''', (row['candidate_id'], job_id)).fetchone()

#             if not existing:
#                 subject = "🎉 Congratulations! You've Been Selected for the Next Round"
#                 body = f"""Dear {row['name']},

# We are thrilled to inform you that you have successfully cleared the Soft Skills Interview round with an impressive score of {row['overall_score']}/100!

# Your communication, confidence, and overall presentation stood out among all the candidates. We are pleased to invite you to the next stage of our selection process.

# Our team will be in touch shortly with further details about what's next.

# Once again, congratulations on this achievement — you should be proud!

# Warm regards,
# HR Team"""
#                 conn.execute(
#                     'INSERT INTO messages (candidate_id, job_id, subject, body) VALUES (?, ?, ?, ?)',
#                     (row['candidate_id'], job_id, subject, body)
#                 )
#                 # Update application status
#                 conn.execute(
#                     "UPDATE applications SET status = 'Shortlisted for Next Round' WHERE candidate_id = ? AND job_id = ?",
#                     (row['candidate_id'], job_id)
#                 )
#                 count += 1

#         conn.commit()
#         return jsonify({'ok': True, 'count': count, 'total': len(rows),
#                         'message': f'{count} new candidates notified (threshold: {threshold}/100).'})
#     except Exception as e:
#         return jsonify({'ok': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @softskills_bp.route('/admin/softskills_results/<int:job_id>')
# def admin_softskills_results(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorised.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = db()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#     results = conn.execute('''
#         SELECT
#             c.id AS candidate_id,
#             c.name, c.email,
#             r.overall_score, r.fluency_score, r.grammar_score,
#             r.confidence_score, r.relevance_score,
#             r.overall_explanation, r.question_details,
#             r.submission_time
#         FROM softskills_results r
#         JOIN candidates c ON r.candidate_id = c.id
#         WHERE r.job_id = ?
#         ORDER BY r.overall_score DESC
#     ''', (job_id,)).fetchall()
#     conn.close()

#     return render_template('admin_softskills_results.html', job=job, results=results,
#                            job_id=job_id)


# @softskills_bp.route('/admin/softskills_video/<int:job_id>/<int:candidate_id>/<int:q_num>')
# def serve_softskills_video(job_id, candidate_id, q_num):
#     """Serve a candidate's recorded answer video to the admin."""
#     if session.get('user_type') != 'admin':
#         return "Unauthorised", 403
#     from flask import send_from_directory
#     video_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
#     filename   = f"q{q_num}.webm"
#     full_path  = os.path.join(video_dir, filename)
#     if not os.path.exists(full_path):
#         return "Recording not found", 404
#     return send_from_directory(video_dir, filename, mimetype='video/webm')

# # Add this function to generate test link
# def generate_test_link(job_id):
#     """Generate the full URL for the test"""
#     from flask import url_for
#     # This will be set when blueprint is registered
#     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)

# # Modify the generate_softskills_questions function to also return a test link
# # def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
# #     """
# #     Generate soft skills questions and return (questions, error, test_link)
# #     Now returns test_link as third value
# #     """
# #     if not GROQ_CLIENT:
# #         return None, "Groq client not available.", None

# #     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# # Each question must:
# # - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# # - Require 60-90 seconds to answer verbally
# # - Test a different soft skill

# # Default marks per question: {marks_per_question}

# # Return a JSON array:
# # [
# #   {{
# #     "q": "<full question text>",
# #     "type": "audio_text",
# #     "skill": "<skill being tested e.g. communication>",
# #     "marks": {marks_per_question},
# #     "options": [],
# #     "answer": "<ideal answer keywords/themes for evaluation>"
# #   }}
# # ]"""

# #     try:
# #         resp = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
# #                 {"role": "user",   "content": prompt}
# #             ],
# #             temperature=0.6,
# #         )
# #         text = resp.choices[0].message.content.strip()
# #         if text.startswith("```"):
# #             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
# #             text = re.sub(r"\n?```$", "", text).strip()
# #         questions = json.loads(text)
# #         if not isinstance(questions, list):
# #             return None, "Unexpected format from Groq.", None
        
# #         # Generate test link
# #         from flask import url_for
# #         test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
        
# #         return questions, None, test_link
# #     except Exception as e:
# #         return None, f"Question generation failed: {e}", None


# def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5, job_id: int = None) -> tuple:
#     """
#     Generate soft skills questions and return (questions, error, test_link)
#     Now accepts job_id as parameter
#     """
#     if not GROQ_CLIENT:
#         return None, "Groq client not available.", None

#     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# Each question must:
# - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# - Require 60-90 seconds to answer verbally
# - Test a different soft skill

# Default marks per question: {marks_per_question}

# Return a JSON array:
# [
#   {{
#     "q": "<full question text>",
#     "type": "audio_text",
#     "skill": "<skill being tested e.g. communication>",
#     "marks": {marks_per_question},
#     "options": [],
#     "answer": "<ideal answer keywords/themes for evaluation>"
#   }}
# ]"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0.6,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         questions = json.loads(text)
#         if not isinstance(questions, list):
#             return None, "Unexpected format from Groq.", None
        
#         # Generate test link only if job_id is provided
#         test_link = None
#         if job_id:
#             from flask import url_for
#             try:
#                 test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
#             except Exception as e:
#                 print(f"Warning: Could not generate test link: {e}")
#                 test_link = None
        
#         return questions, None, test_link
#     except Exception as e:
#         return None, f"Question generation failed: {e}", None


# def get_softskills_test_link(job_id):
#     """Generate the test link for softskills interview"""
#     from flask import url_for
#     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)



# # ------------------------------------------------------------------ #
# #  DB MIGRATION — call once at startup                                #
# # ------------------------------------------------------------------ #
# def create_softskills_table():
#     """Create the softskills_results table if it doesn't exist."""
#     conn = db()
#     conn.execute('''
#         CREATE TABLE IF NOT EXISTS softskills_results (
#             id                INTEGER PRIMARY KEY AUTOINCREMENT,
#             candidate_id      INTEGER NOT NULL,
#             job_id            INTEGER NOT NULL,
#             overall_score     INTEGER DEFAULT 0,
#             fluency_score     INTEGER DEFAULT 0,
#             grammar_score     INTEGER DEFAULT 0,
#             confidence_score  INTEGER DEFAULT 0,
#             relevance_score   INTEGER DEFAULT 0,
#             overall_explanation TEXT,
#             question_details  TEXT,
#             submission_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
#     conn.commit()
#     conn.close()



































































# from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
# import json
# import os
# from datetime import datetime
# import sqlite3
# import re

# softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

# # Database connection function (will be set from app)
# _db_connection = None

# def register_db(conn_func):
#     global _db_connection
#     _db_connection = conn_func

# def get_db():
#     if _db_connection:
#         return _db_connection()
#     return None

# def create_softskills_table():
#     """Create soft skills responses table if it doesn't exist"""
#     conn = get_db()
#     if not conn:
#         return
    
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS softskills_responses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER NOT NULL,
#                 job_id INTEGER NOT NULL,
#                 question_number INTEGER NOT NULL,
#                 question_text TEXT,
#                 audio_path TEXT,
#                 answer_text TEXT,
#                 submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.commit()
#         print("✅ Soft skills responses table created/verified")
#     except Exception as e:
#         print(f"Error creating softskills table: {e}")
#     finally:
#         conn.close()

# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     """Generate soft skills interview questions using Groq"""
#     from app import GROQ_CLIENT
    
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
    
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "audio_text",
#     "options": [],
#     "answer": "Sample ideal answer guide for evaluation"
#   }}
# ]

# Make the questions professional, relevant, and open-ended to allow detailed responses.
# """
        
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
        
#         response_text = completion.choices[0].message.content.strip()
        
#         # Clean up markdown if present
#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
        
#         questions = json.loads(response_text)
        
#         # Generate test link
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
#         return questions, None, test_link
        
#     except Exception as e:
#         print(f"Error generating soft skills questions: {e}")
#         import traceback
#         traceback.print_exc()
#         return None, str(e), None

# @softskills_bp.route('/candidate/view/<int:job_id>')
# def candidate_softskills_view(job_id):
#     """Display soft skills interview page"""
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to take the interview.", 'warning')
#         return redirect(url_for('candidate_login'))
    
#     candidate_id = session['user_id']
#     conn = get_db()
    
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     # Check if already submitted
#     existing = conn.execute(
#         'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
    
#     if existing:
#         conn.close()
#         flash("You have already completed this interview.", 'info')
#         return redirect(url_for('candidate_jobs'))
    
#     # Get test details
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     conn.close()
    
#     if not test:
#         flash("Interview not found.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     # Parse questions
#     questions = []
#     try:
#         if test['questions_json']:
#             questions_json_str = test['questions_json'].strip()
#             if questions_json_str.startswith('```'):
#                 questions_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', questions_json_str)
#                 questions_json_str = re.sub(r'\n?```$', '', questions_json_str)
#             questions = json.loads(questions_json_str)
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         flash("Error loading interview questions.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     return render_template('candidate_softskills_test.html',
#                          test=test,
#                          questions=questions,
#                          job_id=job_id)

# @softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     """Submit soft skills interview answers"""
#     print(f"=== SUBMIT SOFT SKILLS CALLED for job_id: {job_id} ===")
    
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
#     candidate_id = session['user_id']
#     conn = get_db()
    
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
#     try:
#         # Check if already submitted
#         existing = conn.execute(
#             'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#             (candidate_id, job_id)
#         ).fetchone()
        
#         if existing:
#             conn.close()
#             return jsonify({'success': False, 'message': 'You have already submitted this interview'}), 400
        
#         # Get job ID from form
#         job_id_from_form = request.form.get('job_id')
#         if job_id_from_form:
#             job_id = int(job_id_from_form)
        
#         # Create uploads folder if not exists
#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)
        
#         # Process all audio files
#         saved_files = []
#         for key in request.files:
#             if key.startswith('audio_'):
#                 audio_file = request.files[key]
#                 if audio_file and audio_file.filename:
#                     # Generate filename
#                     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     filename = f"candidate_{candidate_id}_job_{job_id}_{key}_{timestamp}.webm"
#                     filepath = os.path.join(upload_folder, filename)
                    
#                     # Save file
#                     audio_file.save(filepath)
#                     saved_files.append(filepath)
                    
#                     # Extract question number from key (audio_1, audio_2, etc.)
#                     question_num = int(key.split('_')[1])
                    
#                     # Get answer text
#                     answer_key = f"answer_{question_num}"
#                     answer_text = request.form.get(answer_key, '')
                    
#                     # Save to database
#                     conn.execute('''
#                         INSERT INTO softskills_responses 
#                         (candidate_id, job_id, question_number, audio_path, answer_text)
#                         VALUES (?, ?, ?, ?, ?)
#                     ''', (candidate_id, job_id, question_num, filename, answer_text))
        
#         # Update application status
#         conn.execute('''
#             UPDATE applications 
#             SET status = 'Test Completed' 
#             WHERE candidate_id = ? AND job_id = ?
#         ''', (candidate_id, job_id))
        
#         # Also update test_results table for consistency
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results 
#             (candidate_id, job_id, score, submitted_answers_json)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
        
#         conn.commit()
        
#         print(f"✅ Soft skills interview submitted successfully for candidate {candidate_id}")
#         print(f"   Saved {len(saved_files)} audio files")
        
#         return jsonify({
#             'success': True, 
#             'message': 'Interview submitted successfully',
#             'files_saved': len(saved_files)
#         })
        
#     except Exception as e:
#         print(f"❌ Error submitting soft skills: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         if conn:
#             conn.close()



# @softskills_bp.route('/admin/results/<int:job_id>')
# def admin_softskills_results(job_id):
#     """View soft skills interview results for admin"""
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))
    
#     conn = get_db()
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('admin_dashboard'))
    
#     try:
#         # Get job details
#         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
        
#         # Get all soft skills responses for this job
#         responses = conn.execute('''
#             SELECT 
#                 sr.*,
#                 c.name as candidate_name,
#                 c.email as candidate_email
#             FROM softskills_responses sr
#             JOIN candidates c ON sr.candidate_id = c.id
#             WHERE sr.job_id = ?
#             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
#         ''', (job_id,)).fetchall()
        
#         # Group responses by candidate
#         candidates_dict = {}
#         for response in responses:
#             candidate_id = response['candidate_id']
#             if candidate_id not in candidates_dict:
#                 candidates_dict[candidate_id] = {
#                     'candidate_id': candidate_id,
#                     'candidate_name': response['candidate_name'],
#                     'candidate_email': response['candidate_email'],
#                     'responses': [],
#                     'submission_time': response['submission_time']
#                 }
#             candidates_dict[candidate_id]['responses'].append({
#                 'question_number': response['question_number'],
#                 'question_text': response['question_text'],
#                 'audio_path': response['audio_path'],
#                 'answer_text': response['answer_text']
#             })
        
#         candidates_list = list(candidates_dict.values())
        
#         return render_template('admin_softskills_results.html', 
#                              job=job, 
#                              candidates=candidates_list,
#                              job_id=job_id)
#     except Exception as e:
#         print(f"Error viewing soft skills results: {e}")
#         flash(f"Error loading results: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         conn.close()



# @softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
# def log_proctor_event(job_id):
#     """Log proctor events for soft skills interview"""
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
#     candidate_id = session['user_id']
#     data = request.get_json()
#     event_type = data.get('event_type')
#     details = data.get('details', '')
    
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
    
#     try:
#         # Create proctor_logs table if not exists
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS proctor_logs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER,
#                 job_id INTEGER,
#                 event_type TEXT,
#                 details TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         conn.execute('''
#             INSERT INTO proctor_logs (candidate_id, job_id, event_type, details)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, event_type, details))
#         conn.commit()
#         return jsonify({'success': True})
#     except Exception as e:
#         print(f"Error logging proctor event: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()

# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     """Generate soft skills interview questions using Groq"""
#     from app import GROQ_CLIENT
    
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
    
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "audio_text",
#     "options": [],
#     "answer": "Sample ideal answer guide for evaluation"
#   }}
# ]

# Make the questions professional, relevant, and open-ended to allow detailed responses.
# """
        
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
        
#         response_text = completion.choices[0].message.content.strip()
        
#         # Clean up markdown if present
#         if response_text.startswith('```'):
#             import re
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
        
#         questions = json.loads(response_text)
        
#         # Generate test link
#         from flask import url_for
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
#         return questions, None, test_link
        
#     except Exception as e:
#         print(f"Error generating soft skills questions: {e}")
#         import traceback
#         traceback.print_exc()
#         return None, str(e), None












































































































# from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify, send_from_directory
# import json
# import os
# import base64
# from datetime import datetime
# import sqlite3
# import re

# softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

# _db_connection = None

# def register_db(conn_func):
#     global _db_connection
#     _db_connection = conn_func

# def get_db():
#     if _db_connection:
#         return _db_connection()
#     return None

# def create_softskills_table():
#     """Create soft skills responses table if it doesn't exist"""
#     conn = get_db()
#     if not conn:
#         return
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS softskills_responses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER NOT NULL,
#                 job_id INTEGER NOT NULL,
#                 question_number INTEGER NOT NULL,
#                 question_text TEXT,
#                 audio_path TEXT,
#                 answer_text TEXT,
#                 transcript TEXT,
#                 submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         # Migrate older schema that may not have transcript column
#         try:
#             conn.execute('ALTER TABLE softskills_responses ADD COLUMN transcript TEXT')
#         except Exception:
#             pass  # Column already exists — that's fine
#         conn.commit()
#         print("✅ Soft skills responses table created/verified")
#     except Exception as e:
#         print(f"Error creating softskills table: {e}")
#     finally:
#         conn.close()


# # ── Groq Whisper transcription ────────────────────────────────────────────────
# def transcribe_audio_file(filepath):
#     """
#     Transcribe an audio/video file using Groq Whisper.
#     Returns (transcript_text, error_message).
#     Groq Whisper supports: mp3, mp4, mpeg, mpga, m4a, wav, webm
#     """
#     from app import GROQ_CLIENT
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialised — check GROQ_API_KEY"

#     if not filepath or not os.path.exists(filepath):
#         return None, f"File not found: {filepath}"

#     try:
#         with open(filepath, 'rb') as f:
#             # Pass explicit content-type so Groq knows how to decode the container
#             transcription = GROQ_CLIENT.audio.transcriptions.create(
#                 file=(os.path.basename(filepath), f, 'audio/webm'),
#                 model='whisper-large-v3',
#                 language='en',
#                 response_format='text'   # returns a plain string, not JSON
#             )
#         transcript = str(transcription).strip()
#         return (transcript if transcript else "(No speech detected)"), None
#     except Exception as e:
#         print(f"Whisper transcription error for {filepath}: {e}")
#         return None, str(e)


# # ── Question generation ───────────────────────────────────────────────────────
# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     from app import GROQ_CLIENT
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.
# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.
# Return ONLY a JSON array:
# [{{"q":"Question text?","type":"audio_text","options":[],"answer":"Ideal answer guide"}}]
# """
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": "You are a professional HR assessment generator. Always respond with valid JSON only."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
#         response_text = completion.choices[0].message.content.strip()
#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
#         questions = json.loads(response_text)
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
#         return questions, None, test_link
#     except Exception as e:
#         print(f"Error generating questions: {e}")
#         import traceback; traceback.print_exc()
#         return None, str(e), None


# # ── Candidate routes ──────────────────────────────────────────────────────────
# @softskills_bp.route('/candidate/view/<int:job_id>')
# def candidate_softskills_view(job_id):
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to take the interview.", 'warning')
#         return redirect(url_for('candidate_login'))
#     candidate_id = session['user_id']
#     conn = get_db()
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('candidate_jobs'))
#     existing = conn.execute(
#         'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
#     if existing:
#         conn.close()
#         flash("You have already completed this interview.", 'info')
#         return redirect(url_for('candidate_jobs'))
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     conn.close()
#     if not test:
#         flash("Interview not found.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     questions = []
#     try:
#         if test['questions_json']:
#             qs = test['questions_json'].strip()
#             if qs.startswith('```'):
#                 qs = re.sub(r'^```[a-zA-Z]*\n?', '', qs)
#                 qs = re.sub(r'\n?```$', '', qs)
#             questions = json.loads(qs)
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         flash("Error loading interview questions.", 'error')
#         return redirect(url_for('candidate_jobs'))
#     return render_template('candidate_softskills_test.html', test=test, questions=questions, job_id=job_id)


# @softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     print(f"=== SUBMIT SOFT SKILLS for job_id={job_id} ===")
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
#     candidate_id = session['user_id']
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database connection error'}), 500
#     try:
#         existing = conn.execute(
#             'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#             (candidate_id, job_id)
#         ).fetchone()
#         if existing:
#             conn.close()
#             return jsonify({'success': False, 'message': 'Already submitted'}), 400

#         if request.form.get('job_id'):
#             job_id = int(request.form.get('job_id'))

#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)

#         saved_files = []
#         total_questions = 0

#         all_keys = list(request.form.keys()) + list(request.files.keys())
#         q_indices = set()
#         for key in all_keys:
#             if key.startswith('audio_') or key.startswith('answer_'):
#                 try:
#                     q_indices.add(int(key.split('_')[1]))
#                 except:
#                     pass

#         for question_num in sorted(q_indices):
#             answer_text = request.form.get(f'answer_{question_num}', '')
#             audio_path_db = None

#             # 1) Multipart file upload (from AI interview page)
#             if f'audio_{question_num}' in request.files:
#                 af = request.files[f'audio_{question_num}']
#                 if af and af.filename:
#                     ct = af.content_type or 'video/webm'
#                     ext = 'mp4' if 'mp4' in ct else 'webm'
#                     ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.{ext}"
#                     filepath = os.path.join(upload_folder, filename)
#                     af.save(filepath)
#                     audio_path_db = filename
#                     saved_files.append(filepath)
#                     print(f"  ✅ Saved Q{question_num}: {filename} ({ct})")

#             # 2) Base64 in audio_N form field
#             if not audio_path_db:
#                 b64 = request.form.get(f'audio_{question_num}', '')
#                 if b64.startswith('data:'):
#                     try:
#                         _, enc = b64.split(',', 1)
#                         data = base64.b64decode(enc)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(data)
#                         audio_path_db = filename
#                         saved_files.append(filepath)
#                     except Exception as e:
#                         print(f"  ⚠️ base64 audio_{question_num}: {e}")

#             # 3) Base64 in q_N form field
#             if not audio_path_db:
#                 qv = request.form.get(f'q_{question_num}', '')
#                 if qv.startswith('data:'):
#                     try:
#                         _, enc = qv.split(',', 1)
#                         data = base64.b64decode(enc)
#                         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                         filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
#                         filepath = os.path.join(upload_folder, filename)
#                         with open(filepath, 'wb') as fh:
#                             fh.write(data)
#                         audio_path_db = filename
#                         saved_files.append(filepath)
#                     except Exception as e:
#                         print(f"  ⚠️ base64 q_{question_num}: {e}")
#                 elif qv:
#                     answer_text = qv

#             conn.execute('''
#                 INSERT INTO softskills_responses
#                 (candidate_id, job_id, question_number, audio_path, answer_text)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (candidate_id, job_id, question_num, audio_path_db, answer_text))
#             total_questions += 1

#         # Standard q_N keys
#         for key in [k for k in request.form.keys() if re.match(r'^q_\d+$', k)]:
#             try:
#                 qn = int(key.split('_')[1])
#             except:
#                 continue
#             if qn in q_indices:
#                 continue
#             val = request.form.get(key, '')
#             apath = None
#             atext = ''
#             if val.startswith('data:'):
#                 try:
#                     _, enc = val.split(',', 1)
#                     data = base64.b64decode(enc)
#                     ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     fn = f"candidate_{candidate_id}_job_{job_id}_q{qn}_{ts}.webm"
#                     fp = os.path.join(upload_folder, fn)
#                     with open(fp, 'wb') as fh:
#                         fh.write(data)
#                     apath = fn
#                     saved_files.append(fp)
#                 except Exception as e:
#                     print(f"  ⚠️ q_{qn}: {e}")
#                     atext = val
#             else:
#                 atext = val
#             conn.execute('''
#                 INSERT INTO softskills_responses
#                 (candidate_id, job_id, question_number, audio_path, answer_text)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (candidate_id, job_id, qn, apath, atext))
#             total_questions += 1

#         conn.execute(
#             "UPDATE applications SET status='Test Completed' WHERE candidate_id=? AND job_id=?",
#             (candidate_id, job_id)
#         )
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results (candidate_id, job_id, score, submitted_answers_json)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
#         conn.commit()
#         print(f"✅ Done: {len(saved_files)} files, {total_questions} questions")
#         return jsonify({'success': True, 'message': 'Interview submitted successfully', 'files_saved': len(saved_files)})
#     except Exception as e:
#         print(f"❌ Submit error: {e}")
#         import traceback; traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         if conn:
#             conn.close()


# # ── Serve video/audio files ───────────────────────────────────────────────────
# @softskills_bp.route('/audio/<path:filename>')
# def serve_softskills_audio(filename):
#     """
#     Serve candidate video recordings to admin.
#     Implements HTTP Range requests so browsers can seek and render video frames.
#     """
#     if session.get('user_type') != 'admin':
#         return jsonify({'error': 'Unauthorized'}), 403

#     import re as _re
#     from flask import Response

#     audio_dir = os.path.join(os.getcwd(), 'uploads', 'softskills_audio')
#     filepath  = os.path.join(audio_dir, filename)

#     if not os.path.exists(filepath):
#         return jsonify({'error': 'File not found'}), 404

#     mimetype  = 'video/mp4' if filename.endswith('.mp4') else 'video/webm'
#     file_size = os.path.getsize(filepath)

#     range_header = request.headers.get('Range', None)

#     if range_header:
#         m = _re.match(r'bytes=(\d+)-(\d*)', range_header)
#         if m:
#             start  = int(m.group(1))
#             end    = int(m.group(2)) if m.group(2) else file_size - 1
#             end    = min(end, file_size - 1)
#             length = end - start + 1

#             with open(filepath, 'rb') as f:
#                 f.seek(start)
#                 chunk = f.read(length)

#             rv = Response(chunk, 206, mimetype=mimetype, direct_passthrough=True)
#             rv.headers['Content-Range']  = f'bytes {start}-{end}/{file_size}'
#             rv.headers['Accept-Ranges']  = 'bytes'
#             rv.headers['Content-Length'] = str(length)
#             rv.headers['Cache-Control']  = 'no-cache'
#             return rv

#     # Full file
#     with open(filepath, 'rb') as f:
#         data = f.read()

#     rv = Response(data, 200, mimetype=mimetype)
#     rv.headers['Accept-Ranges']  = 'bytes'
#     rv.headers['Content-Length'] = str(file_size)
#     rv.headers['Cache-Control']  = 'no-cache'
#     return rv


# # ── On-demand Groq Whisper transcription ─────────────────────────────────────
# @softskills_bp.route('/admin/transcribe/<int:response_id>', methods=['POST'])
# def admin_transcribe(response_id):
#     """Transcribe one response's recording using Groq Whisper. Admin only."""
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
#     try:
#         row = conn.execute(
#             'SELECT id, audio_path, transcript FROM softskills_responses WHERE id = ?',
#             (response_id,)
#         ).fetchone()

#         if not row:
#             return jsonify({'success': False, 'message': 'Response not found'}), 404

#         # Return cached transcript instantly
#         if row['transcript']:
#             return jsonify({'success': True, 'transcript': row['transcript'], 'cached': True})

#         if not row['audio_path']:
#             return jsonify({'success': False, 'message': 'No audio file attached to this response'}), 400

#         filepath = os.path.join('uploads', 'softskills_audio', row['audio_path'])
#         transcript, error = transcribe_audio_file(filepath)

#         if error:
#             return jsonify({'success': False, 'message': f'Transcription failed: {error}'}), 500

#         # Persist so next call is instant
#         conn.execute(
#             'UPDATE softskills_responses SET transcript = ? WHERE id = ?',
#             (transcript, response_id)
#         )
#         conn.commit()
#         return jsonify({'success': True, 'transcript': transcript, 'cached': False})

#     except Exception as e:
#         print(f"Transcription error: {e}")
#         import traceback; traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# # ── Admin results page ────────────────────────────────────────────────────────
# # @softskills_bp.route('/admin/results/<int:job_id>')
# # def admin_softskills_results(job_id):
# #     if session.get('user_type') != 'admin':
# #         flash("Unauthorized access.", 'warning')
# #         return redirect(url_for('admin_login'))
# #     conn = get_db()
# #     if not conn:
# #         flash("Database connection error", 'error')
# #         return redirect(url_for('admin_dashboard'))
# #     try:
# #         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
# #         responses = conn.execute('''
# #             SELECT sr.*, c.name as candidate_name, c.email as candidate_email
# #             FROM softskills_responses sr
# #             JOIN candidates c ON sr.candidate_id = c.id
# #             WHERE sr.job_id = ?
# #             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
# #         ''', (job_id,)).fetchall()

# #         candidates_dict = {}
# #         for r in responses:
# #             cid = r['candidate_id']
# #             if cid not in candidates_dict:
# #                 candidates_dict[cid] = {
# #                     'candidate_id': cid,
# #                     'candidate_name': r['candidate_name'],
# #                     'candidate_email': r['candidate_email'],
# #                     'responses': [],
# #                     'submission_time': r['submission_time']
# #                 }
# #             audio_url = None
# #             if r['audio_path']:
# #                 audio_url = url_for('softskills.serve_softskills_audio', filename=r['audio_path'])

# #             candidates_dict[cid]['responses'].append({
# #                 'id': r['id'],
# #                 'question_number': r['question_number'],
# #                 'question_text': r['question_text'],
# #                 'audio_path': r['audio_path'],
# #                 'audio_url': audio_url,
# #                 'answer_text': r['answer_text'],
# #                 'transcript': r['transcript'] if r['transcript'] else None,
# #             })

# #         return render_template('admin_softskills_results.html',
# #                                job=job,
# #                                candidates=list(candidates_dict.values()),
# #                                job_id=job_id)
# #     except Exception as e:
# #         print(f"Results error: {e}")
# #         flash(f"Error loading results: {e}", 'error')
# #         return redirect(url_for('admin_dashboard'))
# #     finally:
# #         conn.close()



# @softskills_bp.route('/admin/results/<int:job_id>')
# def admin_softskills_results(job_id):
#     if session.get('user_type') != 'admin':
#         return redirect(url_for('admin_login'))

#     conn = get_db()
#     try:
#         job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()

#         # Fetch all responses grouped by candidate
#         responses = conn.execute('''
#             SELECT
#                 c.id AS candidate_id, c.name, c.email,
#                 r.id AS response_id,
#                 r.question_number, r.question_text, r.audio_path,
#                 r.answer_text, r.transcript,
#                 r.submission_time
#             FROM softskills_responses r
#             JOIN candidates c ON r.candidate_id = c.id
#             WHERE r.job_id = ?
#             ORDER BY c.id, r.question_number
#         ''', (job_id,)).fetchall()

#         # Fetch existing Groq scores keyed by candidate_id
#         scored_rows = conn.execute(
#             'SELECT * FROM softskills_results WHERE job_id = ?', (job_id,)
#         ).fetchall()
#         scores_by_candidate = {row['candidate_id']: dict(row) for row in scored_rows}

#         candidates_dict = {}
#         for row in responses:
#             cid = row['candidate_id']
#             if cid not in candidates_dict:
#                 score_data = scores_by_candidate.get(cid, {})
#                 q_details = []
#                 if score_data.get('question_details'):
#                     try:
#                         q_details = json.loads(score_data['question_details'])
#                     except Exception:
#                         q_details = []
#                 candidates_dict[cid] = {
#                     'candidate_id': cid,
#                     'candidate_name': row['name'],
#                     'candidate_email': row['email'],
#                     'submission_time': row['submission_time'] or 'Recently',
#                     'responses': [],
#                     # Groq score fields (None if not yet scored)
#                     'overall_score':     score_data.get('overall_score'),
#                     'fluency_score':     score_data.get('fluency_score'),
#                     'grammar_score':     score_data.get('grammar_score'),
#                     'confidence_score':  score_data.get('confidence_score'),
#                     'relevance_score':   score_data.get('relevance_score'),
#                     'overall_explanation': score_data.get('overall_explanation'),
#                     'question_details':  q_details,
#                     'total_marks':       sum(q.get('marks', 10) for q in q_details) if q_details else None,
#                     'marks_obtained':    score_data.get('marks_obtained'),
#                 }
#             audio_url = None
#             if row['audio_path']:
#                 audio_url = url_for('softskills.serve_softskills_audio', filename=row['audio_path'])
#             candidates_dict[cid]['responses'].append({
#                 'id': row['response_id'],
#                 'question_number': row['question_number'],
#                 'question_text': row['question_text'],
#                 'audio_path': row['audio_path'],
#                 'audio_url': audio_url,
#                 'answer_text': row['answer_text'],
#                 'transcript': row['transcript'],
#             })

#         return render_template('admin_softskills_results.html',
#                                job=job,
#                                candidates=list(candidates_dict.values()),
#                                job_id=job_id)
#     except Exception as e:
#         print(f"Results error: {e}")
#         import traceback; traceback.print_exc()
#         flash(f"Error loading results: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         conn.close()


# # ── Groq scoring for a candidate ─────────────────────────────────────────────
# @softskills_bp.route('/admin/score_candidate/<int:job_id>/<int:candidate_id>', methods=['POST'])
# def admin_score_candidate(job_id, candidate_id):
#     """
#     Transcribes all of a candidate's responses with Groq Whisper,
#     then scores each one (fluency, grammar, confidence, relevance) via Groq LLM,
#     aggregates totals, and saves to softskills_results.
#     """
#     if session.get('user_type') != 'admin':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403

#     from app import GROQ_CLIENT
#     if not GROQ_CLIENT:
#         return jsonify({'success': False, 'message': 'Groq client not available — check GROQ_API_KEY'}), 500

#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500

#     try:
#         # Fetch all responses for this candidate + job
#         rows = conn.execute(
#             '''SELECT * FROM softskills_responses
#                WHERE candidate_id = ? AND job_id = ?
#                ORDER BY question_number''',
#             (candidate_id, job_id)
#         ).fetchall()

#         if not rows:
#             return jsonify({'success': False, 'message': 'No responses found for this candidate'}), 404

#         # Fetch the test questions_json for marks info
#         test = conn.execute('SELECT questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#         questions_meta = []
#         if test and test['questions_json']:
#             try:
#                 questions_meta = json.loads(test['questions_json'])
#             except Exception:
#                 questions_meta = []

#         question_results = []

#         for idx, row in enumerate(rows):
#             q_meta = questions_meta[idx] if idx < len(questions_meta) else {}
#             marks = int(q_meta.get('marks', 10))
#             question_text = row['question_text'] or q_meta.get('q', f'Question {idx+1}')
#             ideal_answer  = q_meta.get('answer', '')
#             skill         = q_meta.get('skill', '')

#             transcript = row['transcript'] or ''

#             # 1. Transcribe if no transcript yet
#             if not transcript and row['audio_path']:
#                 filepath = os.path.join('uploads', 'softskills_audio', row['audio_path'])
#                 t, err = transcribe_audio_file(filepath)
#                 if t:
#                     transcript = t
#                     conn.execute(
#                         'UPDATE softskills_responses SET transcript = ? WHERE id = ?',
#                         (transcript, row['id'])
#                     )

#             # 2. Score via Groq LLM
#             score_prompt = f"""You are an expert HR assessor. Score this spoken interview answer across 4 dimensions (0-100 each).

# Question: {question_text}
# Ideal answer themes: {ideal_answer if ideal_answer else 'Not specified'}
# Candidate transcript: {transcript if transcript else '(No transcript available)'}

# Score each dimension:
# - fluency: How clear, articulate and smooth is the delivery?
# - grammar: How grammatically correct is the language?
# - confidence: How confident and assertive does the candidate sound?
# - relevance: How well does the answer address the question?

# Return ONLY valid JSON (no markdown, no extra text):
# {{"fluency": <int 0-100>, "grammar": <int 0-100>, "confidence": <int 0-100>, "relevance": <int 0-100>, "explanation": "<2 sentences of specific feedback>"}}"""

#             fluency = grammar = confidence = relevance = 50
#             explanation = 'AI scoring pending.'

#             try:
#                 resp = GROQ_CLIENT.chat.completions.create(
#                     model='llama-3.3-70b-versatile',
#                     messages=[
#                         {'role': 'system', 'content': 'You are an HR evaluation expert. Respond with valid JSON only.'},
#                         {'role': 'user',   'content': score_prompt}
#                     ],
#                     temperature=0,
#                 )
#                 raw = resp.choices[0].message.content.strip()
#                 if raw.startswith('```'):
#                     raw = re.sub(r'^```[a-zA-Z]*\n?', '', raw)
#                     raw = re.sub(r'\n?```$', '', raw).strip()
#                 s = json.loads(raw)
#                 fluency     = max(0, min(100, int(s.get('fluency',    50))))
#                 grammar     = max(0, min(100, int(s.get('grammar',    50))))
#                 confidence  = max(0, min(100, int(s.get('confidence', 50))))
#                 relevance   = max(0, min(100, int(s.get('relevance',  50))))
#                 explanation = s.get('explanation', '')
#             except Exception as e:
#                 print(f'Groq scoring error Q{idx+1}: {e}')

#             # Per-question score out of marks
#             avg_pct   = (fluency + grammar + confidence + relevance) / 4.0
#             q_score   = round(avg_pct * marks / 100, 2)

#             question_results.append({
#                 'question':          question_text,
#                 'skill':             skill,
#                 'marks':             marks,
#                 'transcript':        transcript,
#                 'fluency_score':     fluency,
#                 'grammar_score':     grammar,
#                 'confidence_score':  confidence,
#                 'relevance_score':   relevance,
#                 'explanation':       explanation,
#                 'score':             q_score,
#                 'recording_path':    row['audio_path'],
#             })

#         # 3. Aggregate totals
#         n = len(question_results)
#         def avg_dim(key):
#             return round(sum(q[key] for q in question_results) / n) if n else 0

#         total_marks    = sum(q['marks'] for q in question_results)
#         marks_obtained = round(sum(q['score'] for q in question_results), 1)
#         overall_score  = round((marks_obtained / total_marks) * 100) if total_marks else 0
#         overall_score  = max(0, min(100, overall_score))

#         fluency_avg    = avg_dim('fluency_score')
#         grammar_avg    = avg_dim('grammar_score')
#         confidence_avg = avg_dim('confidence_score')
#         relevance_avg  = avg_dim('relevance_score')

#         # 4. Overall AI summary
#         overall_explanation = 'Evaluation based on fluency, grammar, confidence and relevance.'
#         try:
#             summary_prompt = f"""Summarise this candidate's overall soft skills interview performance in 3 concise sentences.
# Overall scores: Fluency={fluency_avg}, Grammar={grammar_avg}, Confidence={confidence_avg}, Relevance={relevance_avg}, Overall={overall_score}/100
# Per-question notes: {'; '.join(q['explanation'] for q in question_results[:3])}
# Be specific, professional, and mention both strengths and areas for improvement."""
#             r2 = GROQ_CLIENT.chat.completions.create(
#                 model='llama-3.3-70b-versatile',
#                 messages=[{'role': 'user', 'content': summary_prompt}],
#                 temperature=0.3,
#             )
#             overall_explanation = r2.choices[0].message.content.strip()
#         except Exception as e:
#             print(f'Overall summary error: {e}')

#         # Add marks_obtained to the stored data
#         for q in question_results:
#             pass  # already present as q['score']

#         # 5. Upsert into softskills_results
#         existing = conn.execute(
#             'SELECT id FROM softskills_results WHERE candidate_id = ? AND job_id = ?',
#             (candidate_id, job_id)
#         ).fetchone()

#         if existing:
#             conn.execute('''
#                 UPDATE softskills_results
#                 SET overall_score=?, fluency_score=?, grammar_score=?,
#                     confidence_score=?, relevance_score=?,
#                     overall_explanation=?, question_details=?,
#                     submission_time=CURRENT_TIMESTAMP
#                 WHERE candidate_id=? AND job_id=?
#             ''', (overall_score, fluency_avg, grammar_avg, confidence_avg, relevance_avg,
#                   overall_explanation, json.dumps(question_results),
#                   candidate_id, job_id))
#         else:
#             conn.execute('''
#                 INSERT INTO softskills_results
#                 (candidate_id, job_id, overall_score, fluency_score, grammar_score,
#                  confidence_score, relevance_score, overall_explanation, question_details)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#             ''', (candidate_id, job_id, overall_score, fluency_avg, grammar_avg,
#                   confidence_avg, relevance_avg, overall_explanation,
#                   json.dumps(question_results)))

#         conn.commit()

#         return jsonify({
#             'success': True,
#             'overall_score':    overall_score,
#             'fluency':          fluency_avg,
#             'grammar':          grammar_avg,
#             'confidence':       confidence_avg,
#             'relevance':        relevance_avg,
#             'total_marks':      total_marks,
#             'marks_obtained':   marks_obtained,
#             'overall_explanation': overall_explanation,
#             'question_details': question_results,
#         })

#     except Exception as e:
#         print(f'Score candidate error: {e}')
#         import traceback; traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()

# # ── Proctor event logging ─────────────────────────────────────────────────────
# @softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
# def log_proctor_event(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
#     candidate_id = session['user_id']
#     data = request.get_json()
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS proctor_logs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER, job_id INTEGER,
#                 event_type TEXT, details TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (candidate_id, job_id, data.get('event_type'), data.get('details', ''))
#         )
#         conn.commit()
#         return jsonify({'success': True})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()






































































































































# """
# softskills_routes.py
# Handles:
#   - AI question generation  (Groq)
#   - Candidate interview view
#   - Recording submission + evaluation pipeline
#       * AssemblyAI  → speech-to-text + fluency metrics
#       * LanguageTool → grammar / spelling errors
#       * Groq AI      → confidence / relevance / tone scoring
#   - Admin results view
# """

# import os, json, re, time, math, requests, tempfile
# from flask import (Blueprint, render_template, request, redirect,
#                    url_for, session, flash, jsonify)
# from datetime import datetime
# from groq import Groq

# softskills_bp = Blueprint('softskills', __name__)

# # ------------------------------------------------------------------ #
# #  CLIENTS                                                             #
# # ------------------------------------------------------------------ #
# GROQ_CLIENT = None
# try:
#     _key = os.getenv("GROQ_API_KEY")
#     if _key:
#         GROQ_CLIENT = Groq(api_key=_key)
# except Exception as e:
#     print(f"Softskills: Groq client failed: {e}")

# ASSEMBLYAI_KEY   = os.getenv("ASSEMBLYAI_API_KEY", "")
# LANGUAGETOOL_URL = "https://api.languagetoolplus.com/v2/check"   # free tier works
# LT_API_KEY       = os.getenv("LANGUAGETOOL_API_KEY", "")         # optional, works without

# # ------------------------------------------------------------------ #
# #  DB helper (imported from main app at registration time)           #
# # ------------------------------------------------------------------ #
# _get_db = None   # set via register_db(fn) below

# def register_db(fn):
#     global _get_db
#     _get_db = fn

# def db():
#     return _get_db()

# # ------------------------------------------------------------------ #
# #  QUESTION GENERATION                                                #
# # ------------------------------------------------------------------ #
# SOFT_SKILLS_SYSTEM = """You are an expert HR interviewer creating scenario-based spoken interview questions.
# Questions must require a verbal, conversational answer — NOT multiple choice.
# Focus on: communication, confidence, teamwork, conflict resolution, leadership, self-awareness.
# Return ONLY a valid JSON array. No markdown fences, no prose."""

# def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
#     if not GROQ_CLIENT:
#         return None, "Groq client not available."

#     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# Each question must:
# - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# - Require 60-90 seconds to answer verbally
# - Test a different soft skill

# Default marks per question: {marks_per_question}

# Return a JSON array:
# [
#   {{
#     "q": "<full question text>",
#     "type": "audio_text",
#     "skill": "<skill being tested e.g. communication>",
#     "marks": {marks_per_question},
#     "options": [],
#     "answer": "<ideal answer keywords/themes for evaluation>"
#   }}
# ]"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0.6,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         questions = json.loads(text)
#         if not isinstance(questions, list):
#             return None, "Unexpected format from Groq."
#         return questions, None
#     except Exception as e:
#         return None, f"Question generation failed: {e}"

# # ------------------------------------------------------------------ #
# #  ASSEMBLYAI — speech to text + fluency                              #
# # ------------------------------------------------------------------ #
# def transcribe_with_assemblyai(audio_path: str) -> dict:
#     """Upload audio file to AssemblyAI, poll for result, return metrics."""
#     base = {"transcript": "", "filler_count": 0, "pause_count": 0,
#             "words_per_minute": 0, "confidence": 0.0, "error": None}

#     if not ASSEMBLYAI_KEY:
#         base["error"] = "ASSEMBLYAI_API_KEY not set"
#         return base

#     headers = {"authorization": ASSEMBLYAI_KEY, "content-type": "application/json"}

#     try:
#         # 1. Upload file
#         with open(audio_path, "rb") as f:
#             up = requests.post("https://api.assemblyai.com/v2/upload",
#                                headers={"authorization": ASSEMBLYAI_KEY},
#                                data=f, timeout=60)
#         upload_url = up.json()["upload_url"]

#         # 2. Submit transcription with IAB + auto_chapters disabled, but keep disfluencies
#         payload = {
#             "audio_url": upload_url,
#             "disfluencies": True,       # keeps uh, um in transcript
#             "auto_highlights": True,    # key phrase extraction
#             "punctuate": True,
#             "format_text": True,
#         }
#         job = requests.post("https://api.assemblyai.com/v2/transcript",
#                             headers=headers, json=payload, timeout=30).json()
#         job_id = job["id"]

#         # 3. Poll (max 120s)
#         for _ in range(60):
#             time.sleep(2)
#             result = requests.get(f"https://api.assemblyai.com/v2/transcript/{job_id}",
#                                   headers=headers, timeout=15).json()
#             if result["status"] == "completed":
#                 break
#             if result["status"] == "error":
#                 base["error"] = result.get("error", "AssemblyAI error")
#                 return base

#         transcript_text = result.get("text") or ""
#         words           = result.get("words") or []
#         duration_sec    = (result.get("audio_duration") or 1)

#         # Words per minute
#         wpm = round(len(words) / (duration_sec / 60)) if duration_sec > 0 else 0

#         # Filler word count (uh, um, like, you know, basically)
#         filler_re = re.compile(r'\b(uh+|um+|uhm|like|you know|basically|so|right|okay)\b', re.I)
#         filler_count = len(filler_re.findall(transcript_text))

#         # Long pauses (gaps > 1.5s between consecutive words)
#         pause_count = 0
#         for i in range(1, len(words)):
#             gap = (words[i].get("start", 0) - words[i-1].get("end", 0)) / 1000.0
#             if gap > 1.5:
#                 pause_count += 1

#         # Average word confidence
#         confidences = [w.get("confidence", 0) for w in words if "confidence" in w]
#         avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

#         return {
#             "transcript":    transcript_text,
#             "filler_count":  filler_count,
#             "pause_count":   pause_count,
#             "words_per_minute": wpm,
#             "confidence":    avg_conf,
#             "error":         None,
#         }

#     except Exception as e:
#         base["error"] = str(e)
#         return base

# # ------------------------------------------------------------------ #
# #  LANGUAGETOOL — grammar check                                        #
# # ------------------------------------------------------------------ #
# def check_grammar(text: str) -> dict:
#     """Return count of grammar/spelling/style errors + list of issues."""
#     base = {"error_count": 0, "errors": [], "error": None}
#     if not text or len(text.strip()) < 10:
#         return base
#     try:
#         params = {
#             "text": text, "language": "en-US",
#             "enabledOnly": "false",
#         }
#         if LT_API_KEY:
#             params["apiKey"] = LT_API_KEY

#         resp = requests.post(LANGUAGETOOL_URL, data=params, timeout=20)
#         matches = resp.json().get("matches", [])
#         errors = [
#             {
#                 "message": m.get("message", ""),
#                 "context": m.get("context", {}).get("text", ""),
#                 "rule":    m.get("rule", {}).get("issueType", ""),
#             }
#             for m in matches[:10]   # cap at 10 for display
#         ]
#         return {"error_count": len(matches), "errors": errors, "error": None}
#     except Exception as e:
#         base["error"] = str(e)
#         return base

# # ------------------------------------------------------------------ #
# #  GROQ — confidence / relevance / tone scoring                        #
# # ------------------------------------------------------------------ #
# def score_answer_with_groq(question: str, ideal_themes: str, transcript: str,
#                             fluency_metrics: dict) -> dict:
#     """Ask Groq to score confidence, relevance, tone and give explanation."""
#     base = {"confidence": 50, "relevance": 50, "tone": 50,
#             "positivity": 50, "explanation": "AI scoring unavailable."}

#     if not GROQ_CLIENT or not transcript:
#         return base

#     prompt = f"""You are an expert HR assessor scoring a spoken interview answer.

# Question: {question}
# Ideal answer themes: {ideal_themes}
# Candidate transcript: {transcript}
# Fluency metrics: WPM={fluency_metrics.get('words_per_minute',0)}, fillers={fluency_metrics.get('filler_count',0)}, long pauses={fluency_metrics.get('pause_count',0)}

# Score each dimension from 0-100:
# - confidence: Does the candidate sound sure and assertive?
# - relevance: Does the answer address the question and ideal themes?
# - tone: Is the tone professional and appropriate?
# - positivity: Is the candidate's attitude positive and constructive?

# Return ONLY valid JSON:
# {{
#   "confidence": <int>,
#   "relevance": <int>,
#   "tone": <int>,
#   "positivity": <int>,
#   "explanation": "<2-3 sentences explaining the evaluation>"
# }}"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": "You are an HR evaluation expert. Reply with valid JSON only."},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         result = json.loads(text)
#         return {
#             "confidence":  max(0, min(100, int(result.get("confidence",  50)))),
#             "relevance":   max(0, min(100, int(result.get("relevance",   50)))),
#             "tone":        max(0, min(100, int(result.get("tone",        50)))),
#             "positivity":  max(0, min(100, int(result.get("positivity",  50)))),
#             "explanation": result.get("explanation", ""),
#         }
#     except Exception as e:
#         base["explanation"] = f"AI scoring error: {e}"
#         return base

# # ------------------------------------------------------------------ #
# #  SCORING AGGREGATION                                                 #
# # ------------------------------------------------------------------ #
# def compute_fluency_score(metrics: dict) -> int:
#     """Convert raw fluency metrics to a 0-100 score."""
#     wpm        = metrics.get("words_per_minute", 0)
#     fillers    = metrics.get("filler_count", 0)
#     pauses     = metrics.get("pause_count", 0)
#     conf       = metrics.get("confidence", 0.5) * 100   # 0-100

#     # WPM score: ideal 120-160 wpm for spoken English
#     if   wpm == 0:      wpm_score = 20
#     elif wpm < 80:      wpm_score = 50
#     elif wpm < 120:     wpm_score = 75
#     elif wpm <= 170:    wpm_score = 100
#     else:               wpm_score = 70   # too fast

#     # Penalty: each filler -3pts, each long pause -5pts
#     penalty = min(50, fillers * 3 + pauses * 5)
#     raw = (wpm_score * 0.4) + (conf * 0.4) - penalty * 0.2
#     return max(0, min(100, round(raw)))

# def compute_grammar_score(grammar: dict) -> int:
#     errors = grammar.get("error_count", 0)
#     if   errors == 0: return 100
#     elif errors <= 2: return 85
#     elif errors <= 5: return 65
#     elif errors <= 10: return 45
#     else:              return 25

# def aggregate_scores(question_results: list, questions: list) -> dict:
#     """Average all per-question scores into weighted totals using marks per question."""
#     n = len(question_results)
#     if n == 0:
#         return {"fluency": 0, "grammar": 0, "confidence": 0, "relevance": 0, "overall": 0,
#                 "total_marks": 0, "marks_obtained": 0}

#     # Total possible marks
#     total_marks = sum(int(q.get('marks', 5)) for q in questions) if questions else n * 5

#     def avg(key):
#         return round(sum(q.get(key, 0) for q in question_results) / n)

#     fluency    = avg("fluency_score")
#     grammar    = avg("grammar_score")
#     confidence = avg("confidence_score")
#     relevance  = avg("relevance_score")

#     # Marks obtained = weighted by per-question marks
#     marks_obtained = 0
#     for i, qr in enumerate(question_results):
#         q_marks  = int(questions[i].get('marks', 5)) if i < len(questions) else 5
#         # Average of 4 dimensions as 0-1 ratio, multiplied by question marks
#         ratio = (qr.get('fluency_score', 0) + qr.get('grammar_score', 0) +
#                  qr.get('confidence_score', 0) + qr.get('relevance_score', 0)) / 400.0
#         marks_obtained += round(ratio * q_marks, 2)

#     overall = round((marks_obtained / total_marks) * 100) if total_marks > 0 else 0
#     overall = max(0, min(100, overall))

#     return {
#         "fluency":        fluency,
#         "grammar":        grammar,
#         "confidence":     confidence,
#         "relevance":      relevance,
#         "overall":        overall,
#         "total_marks":    total_marks,
#         "marks_obtained": round(marks_obtained, 1),
#     }

# # ------------------------------------------------------------------ #
# #  ROUTES                                                              #
# # ------------------------------------------------------------------ #

# @softskills_bp.route('/candidate/softskills/test/<int:job_id>')
# def candidate_softskills_view(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = db()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     app_row = conn.execute(
#         'SELECT status FROM applications WHERE job_id = ? AND candidate_id = ?',
#         (job_id, candidate_id)
#     ).fetchone()
#     already = conn.execute(
#         'SELECT id FROM softskills_results WHERE job_id = ? AND candidate_id = ?',
#         (job_id, candidate_id)
#     ).fetchone()
#     conn.close()

#     if not test or not app_row or app_row['status'] != 'Selected for Test':
#         flash("Not authorised for this interview.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     if already:
#         flash("You have already completed this soft skills interview.", 'info')
#         return redirect(url_for('candidate_jobs'))

#     questions = json.loads(test['questions_json']) if test['questions_json'] else []
#     if not questions:
#         flash("No questions configured for this interview.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     return render_template('candidate_softskills_test.html',
#                            test=test, questions=questions, job_id=job_id)


# @softskills_bp.route('/candidate/softskills/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     if session.get('user_type') != 'candidate':
#         return redirect(url_for('candidate_login'))

#     candidate_id = session['user_id']
#     conn = db()
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()

#     if not test:
#         conn.close()
#         flash("Test not found.", 'error')
#         return redirect(url_for('candidate_jobs'))

#     questions  = json.loads(test['questions_json'])
#     upload_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
#     os.makedirs(upload_dir, exist_ok=True)

#     question_results = []

#     for idx, q in enumerate(questions):
#         file_key = f"answer_{idx + 1}"
#         audio_file = request.files.get(file_key)

#         q_result = {
#             "question":      q.get("q", ""),
#             "skill":         q.get("skill", ""),
#             "marks":         q.get("marks", 10),
#             "transcript":    "",
#             "fluency_score": 50,
#             "grammar_score": 50,
#             "confidence_score": 50,
#             "relevance_score":  50,
#             "filler_words":  0,
#             "pauses":        0,
#             "grammar_errors": 0,
#             "explanation":   "No recording submitted.",
#             "recording_path": None,   # ← stored so admin can play it back
#         }

#         if audio_file and audio_file.filename:
#             save_path = os.path.join(upload_dir, f"q{idx+1}.webm")
#             audio_file.save(save_path)

#             # Store relative path for later playback
#             relative_path = os.path.join('softskills', str(job_id), str(candidate_id), f"q{idx+1}.webm")
#             q_result["recording_path"] = relative_path

#             # 1. Speech-to-text + fluency (AssemblyAI)
#             fluency_data = transcribe_with_assemblyai(save_path)
#             transcript   = fluency_data.get("transcript", "")

#             # 2. Grammar check (LanguageTool)
#             grammar_data = check_grammar(transcript)

#             # 3. AI scoring (Groq)
#             ai_scores = score_answer_with_groq(
#                 question     = q.get("q", ""),
#                 ideal_themes = q.get("answer", ""),
#                 transcript   = transcript,
#                 fluency_metrics = fluency_data,
#             )

#             fluency_score  = compute_fluency_score(fluency_data)
#             grammar_score  = compute_grammar_score(grammar_data)

#             q_result.update({
#                 "transcript":       transcript,
#                 "fluency_score":    fluency_score,
#                 "grammar_score":    grammar_score,
#                 "confidence_score": ai_scores["confidence"],
#                 "relevance_score":  ai_scores["relevance"],
#                 "filler_words":     fluency_data.get("filler_count", 0),
#                 "pauses":           fluency_data.get("pause_count", 0),
#                 "grammar_errors":   grammar_data.get("error_count", 0),
#                 "explanation":      ai_scores.get("explanation", ""),
#             })

#         question_results.append(q_result)

#     # Aggregate with per-question marks
#     totals = aggregate_scores(question_results, questions)

#     # Build overall explanation via Groq
#     overall_explanation = "Evaluation based on fluency, grammar, confidence and answer relevance."
#     if GROQ_CLIENT:
#         try:
#             summary_prompt = f"""Summarise this candidate's overall soft skills interview performance in 3 sentences.
# Scores: Fluency={totals['fluency']}, Grammar={totals['grammar']}, Confidence={totals['confidence']}, Relevance={totals['relevance']}, Overall={totals['overall']}
# Per-question notes: {'; '.join([r.get('explanation','') for r in question_results][:3])}
# Be specific and professional. Mention strengths and areas for improvement."""
#             r = GROQ_CLIENT.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=[{"role": "user", "content": summary_prompt}],
#                 temperature=0.3,
#             )
#             overall_explanation = r.choices[0].message.content.strip()
#         except Exception:
#             pass

#     # Save to DB
#     try:
#         conn.execute('''
#             INSERT INTO softskills_results
#               (candidate_id, job_id, overall_score, fluency_score, grammar_score,
#                confidence_score, relevance_score, overall_explanation, question_details)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             candidate_id, job_id,
#             totals['overall'], totals['fluency'], totals['grammar'],
#             totals['confidence'], totals['relevance'],
#             overall_explanation,
#             json.dumps(question_results),
#         ))
#         conn.execute(
#             "UPDATE applications SET status = 'Test Completed' WHERE candidate_id = ? AND job_id = ?",
#             (candidate_id, job_id)
#         )
#         conn.commit()
#         flash(f"Interview submitted! Score: {totals['overall']}/100 "
#               f"({totals['marks_obtained']}/{totals['total_marks']} marks)", 'success')
#     except Exception as e:
#         flash(f"Error saving results: {e}", 'error')
#     finally:
#         conn.close()

#     return redirect(url_for('candidate_jobs'))


# @softskills_bp.route('/candidate/softskills/proctor_log/<int:job_id>', methods=['POST'])
# def softskills_proctor_log(job_id):
#     if session.get('user_type') != 'candidate':
#         return jsonify({'ok': False}), 403
#     event = request.json.get('event', 'unknown')
#     conn = db()
#     try:
#         conn.execute(
#             'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
#             (session['user_id'], job_id, 'softskills_proctor', event)
#         )
#         conn.commit()
#     except Exception:
#         pass
#     finally:
#         conn.close()
#     return jsonify({'ok': True})


# @softskills_bp.route('/admin/softskills_shortlist/<int:job_id>', methods=['POST'])
# def admin_softskills_shortlist(job_id):
#     """Send congratulations messages to all candidates above the threshold score."""
#     if session.get('user_type') != 'admin':
#         return jsonify({'ok': False, 'message': 'Unauthorised'}), 403

#     threshold = int(request.json.get('threshold', 60))
#     conn = db()
#     try:
#         # Get all candidates above threshold for this job
#         rows = conn.execute('''
#             SELECT r.candidate_id, r.overall_score, c.name
#             FROM softskills_results r
#             JOIN candidates c ON r.candidate_id = c.id
#             WHERE r.job_id = ? AND r.overall_score >= ?
#         ''', (job_id, threshold)).fetchall()

#         if not rows:
#             return jsonify({'ok': False, 'message': f'No candidates scored {threshold} or above.'})

#         count = 0
#         for row in rows:
#             # Check if message already sent to avoid duplicates
#             existing = conn.execute('''
#                 SELECT id FROM messages
#                 WHERE candidate_id = ? AND job_id = ?
#                 AND subject LIKE '%Selected for Next Round%'
#             ''', (row['candidate_id'], job_id)).fetchone()

#             if not existing:
#                 subject = "🎉 Congratulations! You've Been Selected for the Next Round"
#                 body = f"""Dear {row['name']},

# We are thrilled to inform you that you have successfully cleared the Soft Skills Interview round with an impressive score of {row['overall_score']}/100!

# Your communication, confidence, and overall presentation stood out among all the candidates. We are pleased to invite you to the next stage of our selection process.

# Our team will be in touch shortly with further details about what's next.

# Once again, congratulations on this achievement — you should be proud!

# Warm regards,
# HR Team"""
#                 conn.execute(
#                     'INSERT INTO messages (candidate_id, job_id, subject, body) VALUES (?, ?, ?, ?)',
#                     (row['candidate_id'], job_id, subject, body)
#                 )
#                 # Update application status
#                 conn.execute(
#                     "UPDATE applications SET status = 'Shortlisted for Next Round' WHERE candidate_id = ? AND job_id = ?",
#                     (row['candidate_id'], job_id)
#                 )
#                 count += 1

#         conn.commit()
#         return jsonify({'ok': True, 'count': count, 'total': len(rows),
#                         'message': f'{count} new candidates notified (threshold: {threshold}/100).'})
#     except Exception as e:
#         return jsonify({'ok': False, 'message': str(e)}), 500
#     finally:
#         conn.close()


# @softskills_bp.route('/admin/softskills_results/<int:job_id>')
# def admin_softskills_results(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorised.", 'warning')
#         return redirect(url_for('admin_login'))

#     conn = db()
#     job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#     results = conn.execute('''
#         SELECT
#             c.id AS candidate_id,
#             c.name, c.email,
#             r.overall_score, r.fluency_score, r.grammar_score,
#             r.confidence_score, r.relevance_score,
#             r.overall_explanation, r.question_details,
#             r.submission_time
#         FROM softskills_results r
#         JOIN candidates c ON r.candidate_id = c.id
#         WHERE r.job_id = ?
#         ORDER BY r.overall_score DESC
#     ''', (job_id,)).fetchall()
#     conn.close()

#     return render_template('admin_softskills_results.html', job=job, results=results,
#                            job_id=job_id)


# @softskills_bp.route('/admin/softskills_video/<int:job_id>/<int:candidate_id>/<int:q_num>')
# def serve_softskills_video(job_id, candidate_id, q_num):
#     """Serve a candidate's recorded answer video to the admin."""
#     if session.get('user_type') != 'admin':
#         return "Unauthorised", 403
#     from flask import send_from_directory
#     video_dir = os.path.join('uploads', 'softskills', str(job_id), str(candidate_id))
#     filename   = f"q{q_num}.webm"
#     full_path  = os.path.join(video_dir, filename)
#     if not os.path.exists(full_path):
#         return "Recording not found", 404
#     return send_from_directory(video_dir, filename, mimetype='video/webm')

# # Add this function to generate test link
# def generate_test_link(job_id):
#     """Generate the full URL for the test"""
#     from flask import url_for
#     # This will be set when blueprint is registered
#     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)

# # Modify the generate_softskills_questions function to also return a test link
# # def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5) -> tuple:
# #     """
# #     Generate soft skills questions and return (questions, error, test_link)
# #     Now returns test_link as third value
# #     """
# #     if not GROQ_CLIENT:
# #         return None, "Groq client not available.", None

# #     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# # Each question must:
# # - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# # - Require 60-90 seconds to answer verbally
# # - Test a different soft skill

# # Default marks per question: {marks_per_question}

# # Return a JSON array:
# # [
# #   {{
# #     "q": "<full question text>",
# #     "type": "audio_text",
# #     "skill": "<skill being tested e.g. communication>",
# #     "marks": {marks_per_question},
# #     "options": [],
# #     "answer": "<ideal answer keywords/themes for evaluation>"
# #   }}
# # ]"""

# #     try:
# #         resp = GROQ_CLIENT.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[
# #                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
# #                 {"role": "user",   "content": prompt}
# #             ],
# #             temperature=0.6,
# #         )
# #         text = resp.choices[0].message.content.strip()
# #         if text.startswith("```"):
# #             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
# #             text = re.sub(r"\n?```$", "", text).strip()
# #         questions = json.loads(text)
# #         if not isinstance(questions, list):
# #             return None, "Unexpected format from Groq.", None
        
# #         # Generate test link
# #         from flask import url_for
# #         test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
        
# #         return questions, None, test_link
# #     except Exception as e:
# #         return None, f"Question generation failed: {e}", None


# def generate_softskills_questions(role_context: str, num_questions: int, marks_per_question: int = 5, job_id: int = None) -> tuple:
#     """
#     Generate soft skills questions and return (questions, error, test_link)
#     Now accepts job_id as parameter
#     """
#     if not GROQ_CLIENT:
#         return None, "Groq client not available.", None

#     prompt = f"""Create {num_questions} spoken interview questions for a candidate applying for: {role_context}

# Each question must:
# - Be open-ended and scenario-based (e.g. "Tell me about a time when...", "What would you do if...", "Describe how you...")
# - Require 60-90 seconds to answer verbally
# - Test a different soft skill

# Default marks per question: {marks_per_question}

# Return a JSON array:
# [
#   {{
#     "q": "<full question text>",
#     "type": "audio_text",
#     "skill": "<skill being tested e.g. communication>",
#     "marks": {marks_per_question},
#     "options": [],
#     "answer": "<ideal answer keywords/themes for evaluation>"
#   }}
# ]"""

#     try:
#         resp = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {"role": "system", "content": SOFT_SKILLS_SYSTEM},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=0.6,
#         )
#         text = resp.choices[0].message.content.strip()
#         if text.startswith("```"):
#             text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
#             text = re.sub(r"\n?```$", "", text).strip()
#         questions = json.loads(text)
#         if not isinstance(questions, list):
#             return None, "Unexpected format from Groq.", None
        
#         # Generate test link only if job_id is provided
#         test_link = None
#         if job_id:
#             from flask import url_for
#             try:
#                 test_link = url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)
#             except Exception as e:
#                 print(f"Warning: Could not generate test link: {e}")
#                 test_link = None
        
#         return questions, None, test_link
#     except Exception as e:
#         return None, f"Question generation failed: {e}", None


# def get_softskills_test_link(job_id):
#     """Generate the test link for softskills interview"""
#     from flask import url_for
#     return url_for('softskills.candidate_softskills_view', job_id=job_id, _external=True)



# # ------------------------------------------------------------------ #
# #  DB MIGRATION — call once at startup                                #
# # ------------------------------------------------------------------ #
# def create_softskills_table():
#     """Create the softskills_results table if it doesn't exist."""
#     conn = db()
#     conn.execute('''
#         CREATE TABLE IF NOT EXISTS softskills_results (
#             id                INTEGER PRIMARY KEY AUTOINCREMENT,
#             candidate_id      INTEGER NOT NULL,
#             job_id            INTEGER NOT NULL,
#             overall_score     INTEGER DEFAULT 0,
#             fluency_score     INTEGER DEFAULT 0,
#             grammar_score     INTEGER DEFAULT 0,
#             confidence_score  INTEGER DEFAULT 0,
#             relevance_score   INTEGER DEFAULT 0,
#             overall_explanation TEXT,
#             question_details  TEXT,
#             submission_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
#     conn.commit()
#     conn.close()



































































# from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
# import json
# import os
# from datetime import datetime
# import sqlite3
# import re

# softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

# # Database connection function (will be set from app)
# _db_connection = None

# def register_db(conn_func):
#     global _db_connection
#     _db_connection = conn_func

# def get_db():
#     if _db_connection:
#         return _db_connection()
#     return None

# def create_softskills_table():
#     """Create soft skills responses table if it doesn't exist"""
#     conn = get_db()
#     if not conn:
#         return
    
#     try:
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS softskills_responses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER NOT NULL,
#                 job_id INTEGER NOT NULL,
#                 question_number INTEGER NOT NULL,
#                 question_text TEXT,
#                 audio_path TEXT,
#                 answer_text TEXT,
#                 submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.commit()
#         print("✅ Soft skills responses table created/verified")
#     except Exception as e:
#         print(f"Error creating softskills table: {e}")
#     finally:
#         conn.close()

# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     """Generate soft skills interview questions using Groq"""
#     from app import GROQ_CLIENT
    
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
    
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "audio_text",
#     "options": [],
#     "answer": "Sample ideal answer guide for evaluation"
#   }}
# ]

# Make the questions professional, relevant, and open-ended to allow detailed responses.
# """
        
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
        
#         response_text = completion.choices[0].message.content.strip()
        
#         # Clean up markdown if present
#         if response_text.startswith('```'):
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
        
#         questions = json.loads(response_text)
        
#         # Generate test link
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
#         return questions, None, test_link
        
#     except Exception as e:
#         print(f"Error generating soft skills questions: {e}")
#         import traceback
#         traceback.print_exc()
#         return None, str(e), None

# @softskills_bp.route('/candidate/view/<int:job_id>')
# def candidate_softskills_view(job_id):
#     """Display soft skills interview page"""
#     if session.get('user_type') != 'candidate':
#         flash("Please log in to take the interview.", 'warning')
#         return redirect(url_for('candidate_login'))
    
#     candidate_id = session['user_id']
#     conn = get_db()
    
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     # Check if already submitted
#     existing = conn.execute(
#         'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#         (candidate_id, job_id)
#     ).fetchone()
    
#     if existing:
#         conn.close()
#         flash("You have already completed this interview.", 'info')
#         return redirect(url_for('candidate_jobs'))
    
#     # Get test details
#     test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
#     conn.close()
    
#     if not test:
#         flash("Interview not found.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     # Parse questions
#     questions = []
#     try:
#         if test['questions_json']:
#             questions_json_str = test['questions_json'].strip()
#             if questions_json_str.startswith('```'):
#                 questions_json_str = re.sub(r'^```[a-zA-Z]*\n?', '', questions_json_str)
#                 questions_json_str = re.sub(r'\n?```$', '', questions_json_str)
#             questions = json.loads(questions_json_str)
#     except Exception as e:
#         print(f"Error parsing questions: {e}")
#         flash("Error loading interview questions.", 'error')
#         return redirect(url_for('candidate_jobs'))
    
#     return render_template('candidate_softskills_test.html',
#                          test=test,
#                          questions=questions,
#                          job_id=job_id)

# @softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
# def candidate_submit_softskills(job_id):
#     """Submit soft skills interview answers"""
#     print(f"=== SUBMIT SOFT SKILLS CALLED for job_id: {job_id} ===")
    
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
#     candidate_id = session['user_id']
#     conn = get_db()
    
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
#     try:
#         # Check if already submitted
#         existing = conn.execute(
#             'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
#             (candidate_id, job_id)
#         ).fetchone()
        
#         if existing:
#             conn.close()
#             return jsonify({'success': False, 'message': 'You have already submitted this interview'}), 400
        
#         # Get job ID from form
#         job_id_from_form = request.form.get('job_id')
#         if job_id_from_form:
#             job_id = int(job_id_from_form)
        
#         # Create uploads folder if not exists
#         upload_folder = os.path.join('uploads', 'softskills_audio')
#         os.makedirs(upload_folder, exist_ok=True)
        
#         # Process all audio files
#         saved_files = []
#         for key in request.files:
#             if key.startswith('audio_'):
#                 audio_file = request.files[key]
#                 if audio_file and audio_file.filename:
#                     # Generate filename
#                     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     filename = f"candidate_{candidate_id}_job_{job_id}_{key}_{timestamp}.webm"
#                     filepath = os.path.join(upload_folder, filename)
                    
#                     # Save file
#                     audio_file.save(filepath)
#                     saved_files.append(filepath)
                    
#                     # Extract question number from key (audio_1, audio_2, etc.)
#                     question_num = int(key.split('_')[1])
                    
#                     # Get answer text
#                     answer_key = f"answer_{question_num}"
#                     answer_text = request.form.get(answer_key, '')
                    
#                     # Save to database
#                     conn.execute('''
#                         INSERT INTO softskills_responses 
#                         (candidate_id, job_id, question_number, audio_path, answer_text)
#                         VALUES (?, ?, ?, ?, ?)
#                     ''', (candidate_id, job_id, question_num, filename, answer_text))
        
#         # Update application status
#         conn.execute('''
#             UPDATE applications 
#             SET status = 'Test Completed' 
#             WHERE candidate_id = ? AND job_id = ?
#         ''', (candidate_id, job_id))
        
#         # Also update test_results table for consistency
#         conn.execute('''
#             INSERT OR REPLACE INTO test_results 
#             (candidate_id, job_id, score, submitted_answers_json)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
        
#         conn.commit()
        
#         print(f"✅ Soft skills interview submitted successfully for candidate {candidate_id}")
#         print(f"   Saved {len(saved_files)} audio files")
        
#         return jsonify({
#             'success': True, 
#             'message': 'Interview submitted successfully',
#             'files_saved': len(saved_files)
#         })
        
#     except Exception as e:
#         print(f"❌ Error submitting soft skills: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         if conn:
#             conn.close()



# @softskills_bp.route('/admin/results/<int:job_id>')
# def admin_softskills_results(job_id):
#     """View soft skills interview results for admin"""
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))
    
#     conn = get_db()
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('admin_dashboard'))
    
#     try:
#         # Get job details
#         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
        
#         # Get all soft skills responses for this job
#         responses = conn.execute('''
#             SELECT 
#                 sr.*,
#                 c.name as candidate_name,
#                 c.email as candidate_email
#             FROM softskills_responses sr
#             JOIN candidates c ON sr.candidate_id = c.id
#             WHERE sr.job_id = ?
#             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
#         ''', (job_id,)).fetchall()
        
#         # Group responses by candidate
#         candidates_dict = {}
#         for response in responses:
#             candidate_id = response['candidate_id']
#             if candidate_id not in candidates_dict:
#                 candidates_dict[candidate_id] = {
#                     'candidate_id': candidate_id,
#                     'candidate_name': response['candidate_name'],
#                     'candidate_email': response['candidate_email'],
#                     'responses': [],
#                     'submission_time': response['submission_time']
#                 }
#             candidates_dict[candidate_id]['responses'].append({
#                 'question_number': response['question_number'],
#                 'question_text': response['question_text'],
#                 'audio_path': response['audio_path'],
#                 'answer_text': response['answer_text']
#             })
        
#         candidates_list = list(candidates_dict.values())
        
#         return render_template('admin_softskills_results.html', 
#                              job=job, 
#                              candidates=candidates_list,
#                              job_id=job_id)
#     except Exception as e:
#         print(f"Error viewing soft skills results: {e}")
#         flash(f"Error loading results: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         conn.close()



# @softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
# def log_proctor_event(job_id):
#     """Log proctor events for soft skills interview"""
#     if session.get('user_type') != 'candidate':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
#     candidate_id = session['user_id']
#     data = request.get_json()
#     event_type = data.get('event_type')
#     details = data.get('details', '')
    
#     conn = get_db()
#     if not conn:
#         return jsonify({'success': False, 'message': 'Database error'}), 500
    
#     try:
#         # Create proctor_logs table if not exists
#         conn.execute('''
#             CREATE TABLE IF NOT EXISTS proctor_logs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 candidate_id INTEGER,
#                 job_id INTEGER,
#                 event_type TEXT,
#                 details TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         conn.execute('''
#             INSERT INTO proctor_logs (candidate_id, job_id, event_type, details)
#             VALUES (?, ?, ?, ?)
#         ''', (candidate_id, job_id, event_type, details))
#         conn.commit()
#         return jsonify({'success': True})
#     except Exception as e:
#         print(f"Error logging proctor event: {e}")
#         return jsonify({'success': False, 'message': str(e)}), 500
#     finally:
#         conn.close()

# def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
#     """Generate soft skills interview questions using Groq"""
#     from app import GROQ_CLIENT
    
#     if not GROQ_CLIENT:
#         return None, "Groq client not initialized", None
    
#     try:
#         prompt = f"""
# You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.

# Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.

# Return ONLY a JSON array in this format:
# [
#   {{
#     "q": "Question text?",
#     "type": "audio_text",
#     "options": [],
#     "answer": "Sample ideal answer guide for evaluation"
#   }}
# ]

# Make the questions professional, relevant, and open-ended to allow detailed responses.
# """
        
#         completion = GROQ_CLIENT.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[
#                 {
#                     "role": "system", 
#                     "content": "You are a professional HR assessment generator. Always respond with valid JSON only."
#                 },
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#         )
        
#         response_text = completion.choices[0].message.content.strip()
        
#         # Clean up markdown if present
#         if response_text.startswith('```'):
#             import re
#             response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
#             response_text = re.sub(r'\n?```$', '', response_text)
        
#         questions = json.loads(response_text)
        
#         # Generate test link
#         from flask import url_for
#         test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        
#         return questions, None, test_link
        
#     except Exception as e:
#         print(f"Error generating soft skills questions: {e}")
#         import traceback
#         traceback.print_exc()
#         return None, str(e), None












































































































from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify, send_from_directory
import json
import os
import base64
from datetime import datetime
import sqlite3
import re

softskills_bp = Blueprint('softskills', __name__, url_prefix='/softskills')

_db_connection = None

def register_db(conn_func):
    global _db_connection
    _db_connection = conn_func

def get_db():
    if _db_connection:
        return _db_connection()
    return None

def create_softskills_table():
    """Create soft skills responses table if it doesn't exist"""
    conn = get_db()
    if not conn:
        return
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS softskills_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question_text TEXT,
                audio_path TEXT,
                answer_text TEXT,
                transcript TEXT,
                submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Migrate older schema that may not have transcript column
        try:
            conn.execute('ALTER TABLE softskills_responses ADD COLUMN transcript TEXT')
        except Exception:
            pass  # Column already exists — that's fine
        conn.commit()
        print("✅ Soft skills responses table created/verified")
    except Exception as e:
        print(f"Error creating softskills table: {e}")
    finally:
        conn.close()


# ── Groq Whisper transcription ────────────────────────────────────────────────
def transcribe_audio_file(filepath):
    """
    Transcribe an audio/video file using Groq Whisper.
    Returns (transcript_text, error_message).
    Groq Whisper supports: mp3, mp4, mpeg, mpga, m4a, wav, webm
    """
    from app import GROQ_CLIENT
    if not GROQ_CLIENT:
        return None, "Groq client not initialised — check GROQ_API_KEY"

    if not filepath or not os.path.exists(filepath):
        return None, f"File not found: {filepath}"

    try:
        with open(filepath, 'rb') as f:
            # Pass explicit content-type so Groq knows how to decode the container
            transcription = GROQ_CLIENT.audio.transcriptions.create(
                file=(os.path.basename(filepath), f, 'audio/webm'),
                model='whisper-large-v3',
                language='en',
                response_format='text'   # returns a plain string, not JSON
            )
        transcript = str(transcription).strip()
        return (transcript if transcript else "(No speech detected)"), None
    except Exception as e:
        print(f"Whisper transcription error for {filepath}: {e}")
        return None, str(e)


# ── Question generation ───────────────────────────────────────────────────────
def generate_softskills_questions(role_context, num_questions, marks_per_question, job_id):
    from app import GROQ_CLIENT
    if not GROQ_CLIENT:
        return None, "Groq client not initialized", None
    try:
        prompt = f"""
You are an expert HR interviewer. Generate {num_questions} soft skills interview questions for a candidate applying for a {role_context} role.
Each question should assess soft skills like communication, teamwork, problem-solving, leadership, adaptability, etc.
Return ONLY a JSON array:
[{{"q":"Question text?","type":"audio_text","options":[],"answer":"Ideal answer guide"}}]
"""
        completion = GROQ_CLIENT.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional HR assessment generator. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        response_text = completion.choices[0].message.content.strip()
        if response_text.startswith('```'):
            response_text = re.sub(r'^```[a-zA-Z]*\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        questions = json.loads(response_text)
        test_link = url_for('candidate_auth_start', job_id=job_id, _external=True)
        return questions, None, test_link
    except Exception as e:
        print(f"Error generating questions: {e}")
        import traceback; traceback.print_exc()
        return None, str(e), None


# ── Candidate routes ──────────────────────────────────────────────────────────
@softskills_bp.route('/candidate/view/<int:job_id>')
def candidate_softskills_view(job_id):
    if session.get('user_type') != 'candidate':
        flash("Please log in to take the interview.", 'warning')
        return redirect(url_for('candidate_login'))
    candidate_id = session['user_id']
    conn = get_db()
    if not conn:
        flash("Database connection error", 'error')
        return redirect(url_for('candidate_jobs'))
    existing = conn.execute(
        'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
        (candidate_id, job_id)
    ).fetchone()
    if existing:
        conn.close()
        flash("You have already completed this interview.", 'info')
        return redirect(url_for('candidate_jobs'))
    test = conn.execute('SELECT * FROM tests WHERE job_id = ?', (job_id,)).fetchone()
    conn.close()
    if not test:
        flash("Interview not found.", 'error')
        return redirect(url_for('candidate_jobs'))
    questions = []
    try:
        if test['questions_json']:
            qs = test['questions_json'].strip()
            if qs.startswith('```'):
                qs = re.sub(r'^```[a-zA-Z]*\n?', '', qs)
                qs = re.sub(r'\n?```$', '', qs)
            questions = json.loads(qs)
    except Exception as e:
        print(f"Error parsing questions: {e}")
        flash("Error loading interview questions.", 'error')
        return redirect(url_for('candidate_jobs'))
    return render_template('candidate_softskills_test.html', test=test, questions=questions, job_id=job_id)


@softskills_bp.route('/candidate/submit/<int:job_id>', methods=['POST'])
def candidate_submit_softskills(job_id):
    print(f"=== SUBMIT SOFT SKILLS for job_id={job_id} ===")
    if session.get('user_type') != 'candidate':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    candidate_id = session['user_id']
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    try:
        existing = conn.execute(
            'SELECT * FROM softskills_responses WHERE candidate_id = ? AND job_id = ?',
            (candidate_id, job_id)
        ).fetchone()
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Already submitted'}), 400

        if request.form.get('job_id'):
            job_id = int(request.form.get('job_id'))

        upload_folder = os.path.join('uploads', 'softskills_audio')
        os.makedirs(upload_folder, exist_ok=True)

        saved_files = []
        total_questions = 0

        all_keys = list(request.form.keys()) + list(request.files.keys())
        q_indices = set()
        for key in all_keys:
            if key.startswith('audio_') or key.startswith('answer_'):
                try:
                    q_indices.add(int(key.split('_')[1]))
                except:
                    pass

        for question_num in sorted(q_indices):
            answer_text = request.form.get(f'answer_{question_num}', '')
            audio_path_db = None

            # 1) Multipart file upload (from AI interview page)
            if f'audio_{question_num}' in request.files:
                af = request.files[f'audio_{question_num}']
                if af and af.filename:
                    ct = af.content_type or 'video/webm'
                    ext = 'mp4' if 'mp4' in ct else 'webm'
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.{ext}"
                    filepath = os.path.join(upload_folder, filename)
                    af.save(filepath)
                    audio_path_db = filename
                    saved_files.append(filepath)
                    print(f"  ✅ Saved Q{question_num}: {filename} ({ct})")

            # 2) Base64 in audio_N form field
            if not audio_path_db:
                b64 = request.form.get(f'audio_{question_num}', '')
                if b64.startswith('data:'):
                    try:
                        _, enc = b64.split(',', 1)
                        data = base64.b64decode(enc)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
                        filepath = os.path.join(upload_folder, filename)
                        with open(filepath, 'wb') as fh:
                            fh.write(data)
                        audio_path_db = filename
                        saved_files.append(filepath)
                    except Exception as e:
                        print(f"  ⚠️ base64 audio_{question_num}: {e}")

            # 3) Base64 in q_N form field
            if not audio_path_db:
                qv = request.form.get(f'q_{question_num}', '')
                if qv.startswith('data:'):
                    try:
                        _, enc = qv.split(',', 1)
                        data = base64.b64decode(enc)
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"candidate_{candidate_id}_job_{job_id}_q{question_num}_{ts}.webm"
                        filepath = os.path.join(upload_folder, filename)
                        with open(filepath, 'wb') as fh:
                            fh.write(data)
                        audio_path_db = filename
                        saved_files.append(filepath)
                    except Exception as e:
                        print(f"  ⚠️ base64 q_{question_num}: {e}")
                elif qv:
                    answer_text = qv

            conn.execute('''
                INSERT INTO softskills_responses
                (candidate_id, job_id, question_number, audio_path, answer_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (candidate_id, job_id, question_num, audio_path_db, answer_text))
            total_questions += 1

        # Standard q_N keys
        for key in [k for k in request.form.keys() if re.match(r'^q_\d+$', k)]:
            try:
                qn = int(key.split('_')[1])
            except:
                continue
            if qn in q_indices:
                continue
            val = request.form.get(key, '')
            apath = None
            atext = ''
            if val.startswith('data:'):
                try:
                    _, enc = val.split(',', 1)
                    data = base64.b64decode(enc)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    fn = f"candidate_{candidate_id}_job_{job_id}_q{qn}_{ts}.webm"
                    fp = os.path.join(upload_folder, fn)
                    with open(fp, 'wb') as fh:
                        fh.write(data)
                    apath = fn
                    saved_files.append(fp)
                except Exception as e:
                    print(f"  ⚠️ q_{qn}: {e}")
                    atext = val
            else:
                atext = val
            conn.execute('''
                INSERT INTO softskills_responses
                (candidate_id, job_id, question_number, audio_path, answer_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (candidate_id, job_id, qn, apath, atext))
            total_questions += 1

        conn.execute(
            "UPDATE applications SET status='Test Completed' WHERE candidate_id=? AND job_id=?",
            (candidate_id, job_id)
        )
        conn.execute('''
            INSERT OR REPLACE INTO test_results (candidate_id, job_id, score, submitted_answers_json)
            VALUES (?, ?, ?, ?)
        ''', (candidate_id, job_id, 0, json.dumps({'status': 'Soft skills interview completed'})))
        conn.commit()
        print(f"✅ Done: {len(saved_files)} files, {total_questions} questions")
        return jsonify({'success': True, 'message': 'Interview submitted successfully', 'files_saved': len(saved_files)})
    except Exception as e:
        print(f"❌ Submit error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()


# ── Serve video/audio files ───────────────────────────────────────────────────
@softskills_bp.route('/audio/<path:filename>')
def serve_softskills_audio(filename):
    """
    Serve candidate video recordings to admin.
    Implements HTTP Range requests so browsers can seek and render video frames.
    """
    if session.get('user_type') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    import re as _re
    from flask import Response

    audio_dir = os.path.join(os.getcwd(), 'uploads', 'softskills_audio')
    filepath  = os.path.join(audio_dir, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    mimetype  = 'video/mp4' if filename.endswith('.mp4') else 'video/webm'
    file_size = os.path.getsize(filepath)

    range_header = request.headers.get('Range', None)

    if range_header:
        m = _re.match(r'bytes=(\d+)-(\d*)', range_header)
        if m:
            start  = int(m.group(1))
            end    = int(m.group(2)) if m.group(2) else file_size - 1
            end    = min(end, file_size - 1)
            length = end - start + 1

            with open(filepath, 'rb') as f:
                f.seek(start)
                chunk = f.read(length)

            rv = Response(chunk, 206, mimetype=mimetype, direct_passthrough=True)
            rv.headers['Content-Range']  = f'bytes {start}-{end}/{file_size}'
            rv.headers['Accept-Ranges']  = 'bytes'
            rv.headers['Content-Length'] = str(length)
            rv.headers['Cache-Control']  = 'no-cache'
            return rv

    # Full file
    with open(filepath, 'rb') as f:
        data = f.read()

    rv = Response(data, 200, mimetype=mimetype)
    rv.headers['Accept-Ranges']  = 'bytes'
    rv.headers['Content-Length'] = str(file_size)
    rv.headers['Cache-Control']  = 'no-cache'
    return rv


# ── On-demand Groq Whisper transcription ─────────────────────────────────────
@softskills_bp.route('/admin/transcribe/<int:response_id>', methods=['POST'])
def admin_transcribe(response_id):
    """Transcribe one response's recording using Groq Whisper. Admin only."""
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500
    try:
        row = conn.execute(
            'SELECT id, audio_path, transcript FROM softskills_responses WHERE id = ?',
            (response_id,)
        ).fetchone()

        if not row:
            return jsonify({'success': False, 'message': 'Response not found'}), 404

        # Return cached transcript instantly
        if row['transcript']:
            return jsonify({'success': True, 'transcript': row['transcript'], 'cached': True})

        if not row['audio_path']:
            return jsonify({'success': False, 'message': 'No audio file attached to this response'}), 400

        filepath = os.path.join('uploads', 'softskills_audio', row['audio_path'])
        transcript, error = transcribe_audio_file(filepath)

        if error:
            return jsonify({'success': False, 'message': f'Transcription failed: {error}'}), 500

        # Persist so next call is instant
        conn.execute(
            'UPDATE softskills_responses SET transcript = ? WHERE id = ?',
            (transcript, response_id)
        )
        conn.commit()
        return jsonify({'success': True, 'transcript': transcript, 'cached': False})

    except Exception as e:
        print(f"Transcription error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


# ── Admin results page ────────────────────────────────────────────────────────
# @softskills_bp.route('/admin/results/<int:job_id>')
# def admin_softskills_results(job_id):
#     if session.get('user_type') != 'admin':
#         flash("Unauthorized access.", 'warning')
#         return redirect(url_for('admin_login'))
#     conn = get_db()
#     if not conn:
#         flash("Database connection error", 'error')
#         return redirect(url_for('admin_dashboard'))
#     try:
#         job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
#         responses = conn.execute('''
#             SELECT sr.*, c.name as candidate_name, c.email as candidate_email
#             FROM softskills_responses sr
#             JOIN candidates c ON sr.candidate_id = c.id
#             WHERE sr.job_id = ?
#             ORDER BY sr.submission_time DESC, sr.candidate_id, sr.question_number
#         ''', (job_id,)).fetchall()

#         candidates_dict = {}
#         for r in responses:
#             cid = r['candidate_id']
#             if cid not in candidates_dict:
#                 candidates_dict[cid] = {
#                     'candidate_id': cid,
#                     'candidate_name': r['candidate_name'],
#                     'candidate_email': r['candidate_email'],
#                     'responses': [],
#                     'submission_time': r['submission_time']
#                 }
#             audio_url = None
#             if r['audio_path']:
#                 audio_url = url_for('softskills.serve_softskills_audio', filename=r['audio_path'])

#             candidates_dict[cid]['responses'].append({
#                 'id': r['id'],
#                 'question_number': r['question_number'],
#                 'question_text': r['question_text'],
#                 'audio_path': r['audio_path'],
#                 'audio_url': audio_url,
#                 'answer_text': r['answer_text'],
#                 'transcript': r['transcript'] if r['transcript'] else None,
#             })

#         return render_template('admin_softskills_results.html',
#                                job=job,
#                                candidates=list(candidates_dict.values()),
#                                job_id=job_id)
#     except Exception as e:
#         print(f"Results error: {e}")
#         flash(f"Error loading results: {e}", 'error')
#         return redirect(url_for('admin_dashboard'))
#     finally:
#         conn.close()



@softskills_bp.route('/admin/results/<int:job_id>')
def admin_softskills_results(job_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db()
    try:
        job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()

        # Fetch all responses grouped by candidate
        responses = conn.execute('''
            SELECT
                c.id AS candidate_id, c.name, c.email,
                r.id AS response_id,
                r.question_number, r.question_text, r.audio_path,
                r.answer_text, r.transcript,
                r.submission_time
            FROM softskills_responses r
            JOIN candidates c ON r.candidate_id = c.id
            WHERE r.job_id = ?
            ORDER BY c.id, r.question_number
        ''', (job_id,)).fetchall()

        # Fetch existing Groq scores keyed by candidate_id
        scored_rows = conn.execute(
            'SELECT * FROM softskills_results WHERE job_id = ?', (job_id,)
        ).fetchall()
        scores_by_candidate = {row['candidate_id']: dict(row) for row in scored_rows}

        # Group responses by candidate first
        candidates_dict = {}
        for row in responses:
            cid = row['candidate_id']
            if cid not in candidates_dict:
                candidates_dict[cid] = {
                    'candidate_id': cid,
                    'candidate_name': row['name'],
                    'candidate_email': row['email'],
                    'submission_time': row['submission_time'] or 'Recently',
                    'responses': [],
                }
            audio_url = None
            if row['audio_path']:
                audio_url = url_for('softskills.serve_softskills_audio', filename=row['audio_path'])
            candidates_dict[cid]['responses'].append({
                'id': row['response_id'],
                'question_number': row['question_number'],
                'question_text': row['question_text'],
                'audio_path': row['audio_path'],
                'audio_url': audio_url,
                'answer_text': row['answer_text'],
                'transcript': row['transcript'],
            })

        # Auto-score any candidate not yet scored
        test = conn.execute('SELECT questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
        questions_meta = []
        if test and test['questions_json']:
            try:
                questions_meta = json.loads(test['questions_json'])
            except Exception:
                questions_meta = []

        for cid, cdata in candidates_dict.items():
            if cid not in scores_by_candidate:
                # Score this candidate now
                _score_candidate_inline(conn, job_id, cid, cdata['responses'], questions_meta)

        # Re-fetch scores after auto-scoring
        scored_rows = conn.execute(
            'SELECT * FROM softskills_results WHERE job_id = ?', (job_id,)
        ).fetchall()
        scores_by_candidate = {row['candidate_id']: dict(row) for row in scored_rows}

        # Merge score data into candidates_dict
        for cid, cdata in candidates_dict.items():
            score_data = scores_by_candidate.get(cid, {})
            q_details = []
            if score_data.get('question_details'):
                try:
                    q_details = json.loads(score_data['question_details'])
                except Exception:
                    q_details = []
            cdata.update({
                'overall_score':       score_data.get('overall_score'),
                'fluency_score':       score_data.get('fluency_score'),
                'grammar_score':       score_data.get('grammar_score'),
                'confidence_score':    score_data.get('confidence_score'),
                'relevance_score':     score_data.get('relevance_score'),
                'overall_explanation': score_data.get('overall_explanation'),
                'question_details':    q_details,
                'total_marks':         sum(q.get('marks', 10) for q in q_details) if q_details else None,
                'marks_obtained':      score_data.get('marks_obtained'),
            })

        return render_template('admin_softskills_results.html',
                               job=job,
                               candidates=list(candidates_dict.values()),
                               job_id=job_id)
    except Exception as e:
        print(f"Results error: {e}")
        import traceback; traceback.print_exc()
        flash(f"Error loading results: {e}", 'error')
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()


def _score_candidate_inline(conn, job_id, candidate_id, response_rows, questions_meta):
    """
    Internal helper: transcribe + Groq-score all responses for one candidate
    and upsert into softskills_results. Called automatically on page load.
    """
    try:
        from app import GROQ_CLIENT
    except Exception:
        GROQ_CLIENT = None

    if not GROQ_CLIENT:
        print(f"Groq not available — skipping auto-score for candidate {candidate_id}")
        return

    question_results = []

    for idx, resp in enumerate(sorted(response_rows, key=lambda r: r.get('question_number') or idx)):
        q_meta       = questions_meta[idx] if idx < len(questions_meta) else {}
        marks        = int(q_meta.get('marks', 10))
        question_text = resp.get('question_text') or q_meta.get('q', f'Question {idx+1}')
        ideal_answer  = q_meta.get('answer', '')
        skill         = q_meta.get('skill', '')

        transcript = resp.get('transcript') or ''

        # Transcribe if needed
        if not transcript and resp.get('audio_path'):
            filepath = os.path.join('uploads', 'softskills_audio', resp['audio_path'])
            t, err = transcribe_audio_file(filepath)
            if t:
                transcript = t
                conn.execute(
                    'UPDATE softskills_responses SET transcript = ? WHERE id = ?',
                    (transcript, resp['id'])
                )

        # ── Strict Groq scoring prompt ──────────────────────────────────────────
        score_prompt = f"""You are a strict, senior HR evaluator scoring a candidate's spoken interview answer.

QUESTION ASKED: {question_text}
IDEAL ANSWER THEMES: {ideal_answer if ideal_answer else 'Not specified'}
CANDIDATE'S TRANSCRIPT: {transcript if transcript else '(No response — candidate did not speak)'}

STRICT SCORING RULES — follow these exactly:
1. RELEVANCE (most important): Does the answer DIRECTLY address the question asked?
   - If transcript is empty, "(No speech detected)", or clearly off-topic: relevance = 0–15
   - If answer is vague, generic, or avoids the actual question: relevance = 16–40
   - If answer partially addresses the question with some specifics: relevance = 41–70
   - If answer directly and fully addresses the question with clear examples: relevance = 71–100

2. FLUENCY: Assess clarity, pace, and articulation from the transcript.
   - No response or incoherent: 0–20
   - Broken/fragmented sentences: 21–50
   - Mostly clear with minor issues: 51–80
   - Clear and well-structured: 81–100

3. GRAMMAR: Assess grammatical correctness of the spoken answer.
   - No response: 0
   - Many errors making it hard to follow: 10–40
   - Some errors but understandable: 41–70
   - Minor or no errors: 71–100

4. CONFIDENCE: Does the tone sound assertive, certain, and professional?
   - No response: 0
   - Hesitant, uncertain throughout: 10–40
   - Moderate confidence: 41–70
   - Consistently confident and assertive: 71–100

IMPORTANT: Do NOT give high scores to vague or off-topic answers. A candidate who gives a generic or rambling answer with no specific relevance to the question should score below 40 in relevance.

Return ONLY valid JSON:
{{"fluency": <int>, "grammar": <int>, "confidence": <int>, "relevance": <int>, "explanation": "<2 specific sentences explaining what the candidate said and why they received these scores>"}}"""

        fluency = grammar = confidence = relevance = 0
        explanation = 'Could not score — no transcript available.'

        try:
            resp_api = GROQ_CLIENT.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[
                    {'role': 'system', 'content': (
                        'You are a strict HR evaluator. Score candidates honestly. '
                        'Never inflate scores for vague, empty, or off-topic answers. '
                        'Respond with valid JSON only — no markdown, no extra text.'
                    )},
                    {'role': 'user', 'content': score_prompt}
                ],
                temperature=0,
            )
            raw = resp_api.choices[0].message.content.strip()
            if raw.startswith('```'):
                raw = re.sub(r'^```[a-zA-Z]*\n?', '', raw)
                raw = re.sub(r'\n?```$', '', raw).strip()
            s = json.loads(raw)
            fluency    = max(0, min(100, int(s.get('fluency',    0))))
            grammar    = max(0, min(100, int(s.get('grammar',    0))))
            confidence = max(0, min(100, int(s.get('confidence', 0))))
            relevance  = max(0, min(100, int(s.get('relevance',  0))))
            explanation = s.get('explanation', '')
        except Exception as e:
            print(f'Groq scoring error Q{idx+1} candidate {candidate_id}: {e}')

        avg_pct = (fluency + grammar + confidence + relevance) / 4.0
        q_score = round(avg_pct * marks / 100, 2)

        question_results.append({
            'question':         question_text,
            'skill':            skill,
            'marks':            marks,
            'transcript':       transcript,
            'fluency_score':    fluency,
            'grammar_score':    grammar,
            'confidence_score': confidence,
            'relevance_score':  relevance,
            'explanation':      explanation,
            'score':            q_score,
            'recording_path':   resp.get('audio_path'),
        })

    if not question_results:
        return

    n = len(question_results)
    def _avg(key): return round(sum(q[key] for q in question_results) / n)

    total_marks    = sum(q['marks'] for q in question_results)
    marks_obtained = round(sum(q['score'] for q in question_results), 1)
    overall_score  = max(0, min(100, round((marks_obtained / total_marks) * 100) if total_marks else 0))
    fluency_avg    = _avg('fluency_score')
    grammar_avg    = _avg('grammar_score')
    confidence_avg = _avg('confidence_score')
    relevance_avg  = _avg('relevance_score')

    overall_explanation = 'Evaluation based on fluency, grammar, confidence and relevance.'
    try:
        summary_prompt = f"""You are a senior HR evaluator. Write a 3-sentence professional summary of this candidate's soft skills interview.

Overall scores — Fluency: {fluency_avg}/100, Grammar: {grammar_avg}/100, Confidence: {confidence_avg}/100, Relevance: {relevance_avg}/100, Overall: {overall_score}/100
Per-question feedback: {'; '.join(q['explanation'] for q in question_results if q['explanation'])}

Be honest and specific. Mention what the candidate actually said (or failed to say). Highlight genuine strengths and clear areas for improvement."""
        r2 = GROQ_CLIENT.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': summary_prompt}],
            temperature=0.2,
        )
        overall_explanation = r2.choices[0].message.content.strip()
    except Exception as e:
        print(f'Overall summary error: {e}')

    existing = conn.execute(
        'SELECT id FROM softskills_results WHERE candidate_id = ? AND job_id = ?',
        (candidate_id, job_id)
    ).fetchone()

    if existing:
        conn.execute('''
            UPDATE softskills_results
            SET overall_score=?, fluency_score=?, grammar_score=?,
                confidence_score=?, relevance_score=?,
                overall_explanation=?, question_details=?,
                submission_time=CURRENT_TIMESTAMP
            WHERE candidate_id=? AND job_id=?
        ''', (overall_score, fluency_avg, grammar_avg, confidence_avg, relevance_avg,
              overall_explanation, json.dumps(question_results),
              candidate_id, job_id))
    else:
        conn.execute('''
            INSERT INTO softskills_results
            (candidate_id, job_id, overall_score, fluency_score, grammar_score,
             confidence_score, relevance_score, overall_explanation, question_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (candidate_id, job_id, overall_score, fluency_avg, grammar_avg,
              confidence_avg, relevance_avg, overall_explanation,
              json.dumps(question_results)))
    conn.commit()
    print(f"✅ Auto-scored candidate {candidate_id} for job {job_id}: {overall_score}/100")


# ── Groq scoring for a candidate ─────────────────────────────────────────────
@softskills_bp.route('/admin/score_candidate/<int:job_id>/<int:candidate_id>', methods=['POST'])
def admin_score_candidate(job_id, candidate_id):
    """
    Transcribes all of a candidate's responses with Groq Whisper,
    then scores each one (fluency, grammar, confidence, relevance) via Groq LLM,
    aggregates totals, and saves to softskills_results.
    """
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    from app import GROQ_CLIENT
    if not GROQ_CLIENT:
        return jsonify({'success': False, 'message': 'Groq client not available — check GROQ_API_KEY'}), 500

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500

    try:
        # Fetch all responses for this candidate + job
        rows = conn.execute(
            '''SELECT * FROM softskills_responses
               WHERE candidate_id = ? AND job_id = ?
               ORDER BY question_number''',
            (candidate_id, job_id)
        ).fetchall()

        if not rows:
            return jsonify({'success': False, 'message': 'No responses found for this candidate'}), 404

        # Fetch the test questions_json for marks info
        test = conn.execute('SELECT questions_json FROM tests WHERE job_id = ?', (job_id,)).fetchone()
        questions_meta = []
        if test and test['questions_json']:
            try:
                questions_meta = json.loads(test['questions_json'])
            except Exception:
                questions_meta = []

        question_results = []

        for idx, row in enumerate(rows):
            q_meta = questions_meta[idx] if idx < len(questions_meta) else {}
            marks = int(q_meta.get('marks', 10))
            question_text = row['question_text'] or q_meta.get('q', f'Question {idx+1}')
            ideal_answer  = q_meta.get('answer', '')
            skill         = q_meta.get('skill', '')

            transcript = row['transcript'] or ''

            # 1. Transcribe if no transcript yet
            if not transcript and row['audio_path']:
                filepath = os.path.join('uploads', 'softskills_audio', row['audio_path'])
                t, err = transcribe_audio_file(filepath)
                if t:
                    transcript = t
                    conn.execute(
                        'UPDATE softskills_responses SET transcript = ? WHERE id = ?',
                        (transcript, row['id'])
                    )

            # 2. Score via Groq LLM
            score_prompt = f"""You are an expert HR assessor. Score this spoken interview answer across 4 dimensions (0-100 each).

Question: {question_text}
Ideal answer themes: {ideal_answer if ideal_answer else 'Not specified'}
Candidate transcript: {transcript if transcript else '(No transcript available)'}

Score each dimension:
- fluency: How clear, articulate and smooth is the delivery?
- grammar: How grammatically correct is the language?
- confidence: How confident and assertive does the candidate sound?
- relevance: How well does the answer address the question?

Return ONLY valid JSON (no markdown, no extra text):
{{"fluency": <int 0-100>, "grammar": <int 0-100>, "confidence": <int 0-100>, "relevance": <int 0-100>, "explanation": "<2 sentences of specific feedback>"}}"""

            fluency = grammar = confidence = relevance = 50
            explanation = 'AI scoring pending.'

            try:
                resp = GROQ_CLIENT.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=[
                        {'role': 'system', 'content': 'You are an HR evaluation expert. Respond with valid JSON only.'},
                        {'role': 'user',   'content': score_prompt}
                    ],
                    temperature=0,
                )
                raw = resp.choices[0].message.content.strip()
                if raw.startswith('```'):
                    raw = re.sub(r'^```[a-zA-Z]*\n?', '', raw)
                    raw = re.sub(r'\n?```$', '', raw).strip()
                s = json.loads(raw)
                fluency     = max(0, min(100, int(s.get('fluency',    50))))
                grammar     = max(0, min(100, int(s.get('grammar',    50))))
                confidence  = max(0, min(100, int(s.get('confidence', 50))))
                relevance   = max(0, min(100, int(s.get('relevance',  50))))
                explanation = s.get('explanation', '')
            except Exception as e:
                print(f'Groq scoring error Q{idx+1}: {e}')

            # Per-question score out of marks
            avg_pct   = (fluency + grammar + confidence + relevance) / 4.0
            q_score   = round(avg_pct * marks / 100, 2)

            question_results.append({
                'question':          question_text,
                'skill':             skill,
                'marks':             marks,
                'transcript':        transcript,
                'fluency_score':     fluency,
                'grammar_score':     grammar,
                'confidence_score':  confidence,
                'relevance_score':   relevance,
                'explanation':       explanation,
                'score':             q_score,
                'recording_path':    row['audio_path'],
            })

        # 3. Aggregate totals
        n = len(question_results)
        def avg_dim(key):
            return round(sum(q[key] for q in question_results) / n) if n else 0

        total_marks    = sum(q['marks'] for q in question_results)
        marks_obtained = round(sum(q['score'] for q in question_results), 1)
        overall_score  = round((marks_obtained / total_marks) * 100) if total_marks else 0
        overall_score  = max(0, min(100, overall_score))

        fluency_avg    = avg_dim('fluency_score')
        grammar_avg    = avg_dim('grammar_score')
        confidence_avg = avg_dim('confidence_score')
        relevance_avg  = avg_dim('relevance_score')

        # 4. Overall AI summary
        overall_explanation = 'Evaluation based on fluency, grammar, confidence and relevance.'
        try:
            summary_prompt = f"""Summarise this candidate's overall soft skills interview performance in 3 concise sentences.
Overall scores: Fluency={fluency_avg}, Grammar={grammar_avg}, Confidence={confidence_avg}, Relevance={relevance_avg}, Overall={overall_score}/100
Per-question notes: {'; '.join(q['explanation'] for q in question_results[:3])}
Be specific, professional, and mention both strengths and areas for improvement."""
            r2 = GROQ_CLIENT.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{'role': 'user', 'content': summary_prompt}],
                temperature=0.3,
            )
            overall_explanation = r2.choices[0].message.content.strip()
        except Exception as e:
            print(f'Overall summary error: {e}')

        # Add marks_obtained to the stored data
        for q in question_results:
            pass  # already present as q['score']

        # 5. Upsert into softskills_results
        existing = conn.execute(
            'SELECT id FROM softskills_results WHERE candidate_id = ? AND job_id = ?',
            (candidate_id, job_id)
        ).fetchone()

        if existing:
            conn.execute('''
                UPDATE softskills_results
                SET overall_score=?, fluency_score=?, grammar_score=?,
                    confidence_score=?, relevance_score=?,
                    overall_explanation=?, question_details=?,
                    submission_time=CURRENT_TIMESTAMP
                WHERE candidate_id=? AND job_id=?
            ''', (overall_score, fluency_avg, grammar_avg, confidence_avg, relevance_avg,
                  overall_explanation, json.dumps(question_results),
                  candidate_id, job_id))
        else:
            conn.execute('''
                INSERT INTO softskills_results
                (candidate_id, job_id, overall_score, fluency_score, grammar_score,
                 confidence_score, relevance_score, overall_explanation, question_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (candidate_id, job_id, overall_score, fluency_avg, grammar_avg,
                  confidence_avg, relevance_avg, overall_explanation,
                  json.dumps(question_results)))

        conn.commit()

        return jsonify({
            'success': True,
            'overall_score':    overall_score,
            'fluency':          fluency_avg,
            'grammar':          grammar_avg,
            'confidence':       confidence_avg,
            'relevance':        relevance_avg,
            'total_marks':      total_marks,
            'marks_obtained':   marks_obtained,
            'overall_explanation': overall_explanation,
            'question_details': question_results,
        })

    except Exception as e:
        print(f'Score candidate error: {e}')
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ── Proctor event logging ─────────────────────────────────────────────────────
@softskills_bp.route('/log_proctor/<int:job_id>', methods=['POST'])
def log_proctor_event(job_id):
    if session.get('user_type') != 'candidate':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    candidate_id = session['user_id']
    data = request.get_json()
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS proctor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER, job_id INTEGER,
                event_type TEXT, details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute(
            'INSERT INTO proctor_logs (candidate_id, job_id, event_type, details) VALUES (?, ?, ?, ?)',
            (candidate_id, job_id, data.get('event_type'), data.get('details', ''))
        )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()