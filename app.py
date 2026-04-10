from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import numpy as np
import os
import json

app = Flask(__name__)
# Security Hardening: Use Environment Variable for Secret Key or fallback to a default
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key-3344')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///planner.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    metrics_json = db.Column(db.Text, nullable=True)
    schedule_json = db.Column(db.Text, nullable=True)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Unauthorized. Please log in."}), 401

# Load model and feature names
try:
    model = joblib.load('model/rf_model.joblib')
    feature_names = joblib.load('model/feature_names.joblib')
except FileNotFoundError:
    model = None
    feature_names = []
    print("Warning: Model not found. Please train the model first.")

@app.route('/')
def home():
    return render_template('index.html')

def evaluate_metrics(data, custom_schedule=None):
    if model is None:
        raise Exception("Model not loaded")
        
    # Build DataFrame with the exact sequence of columns expected
    input_data = {}
    for feature in feature_names:
        if feature not in data:
            raise Exception(f"Missing feature: {feature}")
        input_data[feature] = [data[feature]]
        
    df = pd.DataFrame(input_data)
    
    # Predict burnout
    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1] # Probability of burnout (class 1)
    
    # 1. More Predictions: Academic Success Potential (Heuristic)
    attendance_pts = min(100, df['attendance_percentage'][0]) * 0.4
    study_pts = min(100, (df['study_hours_per_week'][0] / 30.0) * 100) * 0.3
    sleep_pts = min(100, (df['sleep_hours_per_night'][0] / 8.0) * 100) * 0.3
    academic_potential = int(attendance_pts + study_pts + sleep_pts)
    
    # Burnout penalty on potential
    if prediction == 1:
        academic_potential = int(academic_potential * 0.8)
        
    # 2. Actionable Insights to "help the student do more"
    action_plan = []
    if df['sleep_hours_per_night'][0] < 7:
        action_plan.append({
            "title": "Sleep Deficiency Detected", 
            "desc": "Sleeping less than 7 hours severely impacts cognitive load and memory retention. Commit to a 7-8 hour sleep schedule.", 
            "icon": "fa-bed"
        })
    if df['stress_level'][0] >= 7:
        action_plan.append({
            "title": "High Stress Intervention", 
            "desc": "Your stress is unhealthily high. Incorporate a daily 15-minute mindfulness break or light physical exercise.", 
            "icon": "fa-heart-pulse"
        })
    if df['study_hours_per_week'][0] > 35:
        action_plan.append({
            "title": "Overstudying Risk", 
            "desc": "You're clocking high study hours. Ensure you use the Pomodoro technique (25m study, 5m break) to avoid brain fatigue.", 
            "icon": "fa-book-open-reader"
        })
    elif df['study_hours_per_week'][0] < 12:
        action_plan.append({
            "title": "Study Routine Boost", 
            "desc": "Consider gradually adding 30-45 minutes of daily structured studying to improve your midterm confidence.", 
            "icon": "fa-calendar-check"
        })
    if df['attendance_percentage'][0] < 80:
         action_plan.append({
            "title": "Attendance Improvement", 
            "desc": "Skipping lectures forces you to self-learn under pressure. Aim for at least 85% attendance.", 
            "icon": "fa-person-chalkboard"
        })
        
    if not action_plan:
         action_plan.append({
            "title": "Excellent Routine", 
            "desc": "You're maintaining a fantastic balance between study, rest, and lifestyle! Keep it up.", 
            "icon": "fa-thumbs-up", 
            "positive": True
        })
        
    # 3. Personalized Timetable/Weekly Plan based on the prediction itself
    if custom_schedule:
        weekly_plan = custom_schedule
    else:
        if prediction == 1:
            weekly_plan = [
                {"day": "Monday", "focus": "Mental Rest & Recovery", "morning": "No alarms. Focus on hydration and a nutritious breakfast. Avoid checking emails/messages.", "afternoon": "Engage in a low-cognitive hobby (e.g., drawing, walking). Total disconnect from academics.", "evening": "Prepare a healthy dinner. Read fiction or meditate. Hard sleep cutoff at 10:00 PM."},
                {"day": "Tuesday", "focus": "Light Diagnostic Review", "morning": "Review the week's syllabus without executing any tasks. Identify 1-2 easy assignments.", "afternoon": "Max 90 minutes of low-stakes studying using the Pomodoro technique (25m study / 5m break).", "evening": "Stop studying by 6 PM. Listen to a podcast or spend time socializing."},
                {"day": "Wednesday", "focus": "Catch-up & Core Foundation", "morning": "Attend mandatory classes. If overwhelmed, skip non-essential extracurriculars.", "afternoon": "Focus specifically on the most overdue assignment for exactly 2 hours avoiding multitasking.", "evening": "Active physical recovery (yoga, jogging). Ensure 8+ hours of sleep."},
                {"day": "Thursday", "focus": "Targeted Deep Study", "morning": "Eat a protein-rich breakfast. 1 hour of active recall on core subjects.", "afternoon": "Group study or office hours to resolve bottlenecks fast rather than struggling alone.", "evening": "No-screen time 1 hour before bed. Prepare materials for Friday."},
                {"day": "Friday", "focus": "Hard Wrap & Social Reset", "morning": "Final 2-hour push to submit any pending end-of-week deliverables.", "afternoon": "Hard stop at 4 PM. Organize your desk and close all academic tabs on your laptop.", "evening": "Hang out with friends or treat yourself to a favorite meal. Strictly no academic talk."},
                {"day": "Weekend", "focus": "Complete Disconnect", "morning": "Sleep in. Plan a fun outdoor activity or a hobby project.", "afternoon": "Spend quality time with family/friends or run errands at a relaxed pace.", "evening": "Sunday evening only: Spend 30 mins planning the upcoming week to reduce Monday anxiety."}
            ]
        else:
             weekly_plan = [
                {"day": "Monday", "focus": "Momentum & Heavy Lifting", "morning": "Start with a 15-minute weekly planning session. Attack the hardest/most hated subject first.", "afternoon": "Attend classes and engage actively. 2 hours of deep work focusing on new concepts.", "evening": "Light review of today's notes (30m). Hit the gym or exercise."},
                {"day": "Tuesday", "focus": "Maintenance & Output", "morning": "Focus on creative output (writing essays, coding). Use a 50m study / 10m break cycle.", "afternoon": "Knock out small administrative tasks (emails, quizzes) in a 1-hour batch.", "evening": "Extracurricular club meetings or group projects. Maintain a normal 11 PM sleep time."},
                {"day": "Wednesday", "focus": "Active Recall & Social", "morning": "Test yourself on Monday/Tuesday material using flashcards or practice tests without notes.", "afternoon": "Attend lectures. Spend 1-2 hours summarizing key theorems or models.", "evening": "Mid-week social break. Dinner with friends or engaging in a team sport."},
                {"day": "Thursday", "focus": "Deep Focus Blocks", "morning": "Tackle the second hardest subject of the week. Block out all social media.", "afternoon": "Library session (2 hours) solely dedicated to reading and researching upcoming papers.", "evening": "Review feedback from graded assignments to find systematic mistakes."},
                {"day": "Friday", "focus": "Declutter & Wrap Up", "morning": "Finish all pending weekly assignments. Don't leave homework for the weekend if possible.", "afternoon": "Organize notes, back up files, and plan your weekend study blocks.", "evening": "Celebrate the week's wins. Movie night or social event."},
                {"day": "Weekend", "focus": "Balanced Progress", "morning": "Saturday: Complete rest or hobbies. Sunday: 2-hour morning block for next week's prep.", "afternoon": "Explore interests outside of your curriculum. Read, volunteer, or work on a side hustle.", "evening": "Relax and wind down. Get an early night's sleep on Sunday to reset."}
            ]

    return {
        "metrics": data,
        "burnout_predicted": int(prediction),
        "burnout_probability": float(probability),
        "academic_potential": academic_potential,
        "action_plan": action_plan,
        "weekly_schedule": weekly_plan
    }

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        result = evaluate_metrics(data)
        
        # If user is logged in, optionally auto-save their state when they request a brand new setup
        if current_user.is_authenticated:
            current_user.metrics_json = json.dumps(result["metrics"])
            current_user.schedule_json = json.dumps(result["weekly_schedule"])
            db.session.commit()
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ================= AUTHENTICATION ENDPOINTS =================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
        
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password_hash=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password_hash, data.get('password')):
        login_user(user)
        return jsonify({"message": "Logged in successfully", "username": user.username})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/status', methods=['GET'])
def status():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "username": current_user.username})
    return jsonify({"logged_in": False})

@app.route('/api/save', methods=['POST'])
@login_required
def save_plan():
    data = request.json
    current_user.metrics_json = json.dumps(data.get("metrics", {}))
    current_user.schedule_json = json.dumps(data.get("schedule", []))
    db.session.commit()
    return jsonify({"message": "Plan saved to profile!"})

@app.route('/api/load', methods=['GET'])
@login_required
def load_plan():
    metrics = json.loads(current_user.metrics_json) if current_user.metrics_json else None
    schedule = json.loads(current_user.schedule_json) if current_user.schedule_json else None
    
    if not metrics:
        return jsonify({"error": "No saved plan found"}), 404
        
    # We must re-evaluate to get the burnout data visually attached to the payload
    payload = evaluate_metrics(metrics, custom_schedule=schedule)
    return jsonify(payload)

# ================= AI ASSISTANT ENDPOINT =================

from dotenv import load_dotenv

load_dotenv()
try:
    # Use environment variable for API Key (REQUIRED for production)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    gemini_model = None
    print(f"Error configuring Gemini: {e}")

@app.route('/api/chat', methods=['POST'])
def chat():
    """Gemini-powered Chat Assistant with Two-Stage Pipeline."""
    try:
        data = request.json
        user_msg = data.get("message", "").strip()
        current_schedule = data.get("schedule", [])
        current_metrics = data.get("metrics", {})
        
        if not user_msg:
             return jsonify({
                 "response": "How can I help you customize your schedule?", 
                 "schedule": current_schedule,
                 "metrics": current_metrics
             })

        if gemini_model is None:
             return jsonify({"error": "Gemini model is not configured properly on the server."}), 500

        # STAGE 1: Extract Intent & Update Metrics
        prompt_metrics = f"""
The user is a student. Here are their current lifestyle metrics:
{json.dumps(current_metrics, indent=2)}

The user said: "{user_msg}"

Did their message imply a change to their metrics (study_hours_per_week, sleep_hours_per_night, extracurricular_hours_per_week, attendance_percentage, midterm_score, stress_level)? 
Make a reasonable integer best-guess if they are vague. If no change is implied, keep the metrics the same.
You MUST output ONLY a valid JSON object matching this schema:
{{
  "updated_metrics": {{
    "study_hours_per_week": int,
    "sleep_hours_per_night": int,
    "extracurricular_hours_per_week": int,
    "attendance_percentage": int,
    "midterm_score": int,
    "stress_level": int
  }}
}}
"""
        res_metrics = gemini_model.generate_content(prompt_metrics, generation_config={"response_mime_type": "application/json"})
        parsed_metrics = json.loads(res_metrics.text).get("updated_metrics", current_metrics)
        
        # STAGE 2: Generate the core ML Archetype Payload using the new metrics
        new_payload = evaluate_metrics(parsed_metrics, custom_schedule=None) # We let Python generate the fresh default schedule!
        
        # STAGE 3: Apply User's Custom Schedule Tweaks & Get Response
        prompt_schedule = f"""
The user is a student interacting with an AI Planner.
They said: "{user_msg}"

We just generated the optimum base Weekly Schedule for them based on their metrics:
{json.dumps(new_payload['weekly_schedule'], indent=2)}

Your job:
1. Write a friendly, concise response telling them what you changed.
2. If their message implies moving things around their schedule (e.g., "move math to Friday"), modify the schedule JSON to accommodate it. Otherwise, keep the base schedule exactly as is.
You MUST output ONLY a valid JSON object matching this schema:
{{
  "response": "Your friendly reply...",
  "schedule": [
    {{"day": "Monday", "focus": "...", "morning": "...", "afternoon": "...", "evening": "..."}},
    ... for all 7 days ...
  ]
}}
"""
        res_schedule = gemini_model.generate_content(prompt_schedule, generation_config={"response_mime_type": "application/json"})
        parsed_schedule_data = json.loads(res_schedule.text)
        
        # Merge final data
        new_payload["response"] = parsed_schedule_data.get("response", "I've updated your plan!")
        new_payload["schedule"] = parsed_schedule_data.get("schedule", new_payload["weekly_schedule"])
        new_payload["weekly_schedule"] = new_payload["schedule"] # Ensure frontend variable matches
        
        # Auto-save changes if logged in
        if current_user.is_authenticated:
            current_user.metrics_json = json.dumps(new_payload["metrics"])
            current_user.schedule_json = json.dumps(new_payload["schedule"])
            db.session.commit()
            
        return jsonify(new_payload)

    except Exception as e:
        import sys, traceback
        error_details = traceback.format_exc()
        print(f"Gemini API Error: {e}\n{error_details}", file=sys.stderr)
        return jsonify({
            "response": f"Sorry, I had trouble processing your request over the AI network. Error: {str(e)}",
            "schedule": request.json.get("schedule", [])
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
