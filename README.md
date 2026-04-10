# 🧠 AI-Powered Student Burnout Planner

An intelligent web application designed to predict, analyze, and mitigate student burnout using Machine Learning and Generative AI. 

This project integrates a **Random Forest Classifier** trained on student behavioral data with the **Google Gemini Pro** model to provide personalized, real-time recovery schedules.

## 🚀 Key Features

- **Burnout Risk Inference**: Uses a Scikit-Learn Random Forest model to calculate the probability of burnout based on study habits, sleep, stress, and academic performance.
- **Intelligent Chat Assistant**: Powered by **Gemini 2.5 Flash**, the chatbot analyzes the user's schedule and metrics. It can dynamically update the plan through natural language commands (e.g., *"I need more sleep"*).
- **Two-Way Synchronization**: Changes requested in the chat interface physically update the dashboard sliders and re-trigger the ML prediction model.
- **Personalized Dashboards**: Visual burnout gauges, academic potential scores, and actionable insight cards.
- **Smart Scheduling**: Generates a full weekly timetable tailored to the user's specific risk level.
- **Data Persistence**: Secure user authentication and a SQLite database to save and load personal burnout progress.
- **PDF Export**: Allows students to download their personalized recovery schedule for offline use.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Login
- **AI/ML**: Scikit-Learn, Pandas, NumPy, Joblib, Google Generative AI (Gemini)
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism UI), Javascript (ES6+)
- **Database**: SQLite3

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/niranjanmundakkal/ai-study-planner.git
   cd ai-study-planner
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**:
   Create a `.env` file in the root directory and add:
   ```env
   GEMINI_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000` in your browser.

## 📊 How it Works (The ML Pipeline)
The application uses a synthetic dataset of 5,000 students to train a `RandomForestClassifier`. It evaluates six key features:
1. Study Hours per Week
2. Sleep Hours per Night
3. Extracurricular Hours
4. Attendance Percentage
5. Midterm Scores
6. Self-reported Stress Levels

When the user adjusts the dashboard, the backend triggers real-time inference to predict the likelihood of burnout.

---
Built with ❤️ for student well-being.
