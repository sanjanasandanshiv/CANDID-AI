CandidAI — AI-Powered Pre-Interview Screening Platform

CandidAI is an AI-powered pre-interview screening platform designed to help HR teams evaluate candidates through multimodal assessments involving video, audio, and text. The platform combines cognitive reasoning tests, speech-to-text processing, emotion analysis, plagiarism detection, and explainable AI to support a more structured and efficient candidate screening process.

🚀 Key Features

Candidate Authentication: Secure authentication and access management using Clerk.

Multimodal Assessment: Supports video, audio, and text-based candidate responses.

Speech-to-Text: Converts spoken responses into text for further analysis.

Emotion Analysis: Analyzes selected emotional signals from candidate responses using AI-based techniques.

Cognitive Assessment: Evaluates responses to reasoning and cognitive assessment questions.

Plagiarism Detection: Checks candidate responses for potential copied or suspiciously similar content.

Explainable AI (XAI): Provides insights into assessment results to help HR teams understand the factors contributing to an evaluation.

HR Dashboard: Organizes candidate information and assessment results for easier review.

Automated Screening: Helps streamline initial candidate evaluation and reduce repetitive manual screening tasks.

🛠️ Tech Stack

Technology

Purpose

React.js

Frontend user interface

Vite

Frontend development and build tooling

Tailwind CSS

Responsive UI styling

Clerk

Authentication and user management

Python

AI processing and backend logic

Flask / FastAPI

Backend API development

MongoDB Atlas

Candidate and assessment data storage

Speech-to-Text tools

Transcription of audio responses

NLP and Machine Learning

Text processing and response analysis

Explainable AI (XAI)

Interpretable assessment insights

Note: Update the technology list to reflect the libraries and backend framework actually implemented in your final codebase.

🏗️ System Architecture

The platform follows a modular architecture:

Frontend: Candidates log in, complete assessments, and submit responses through the React interface.

Authentication: Clerk manages user authentication and access.

Backend APIs: The Python backend processes requests and coordinates assessment modules.

AI Processing: Dedicated modules handle transcription, emotion analysis, cognitive evaluation, and plagiarism checks.

Database: MongoDB Atlas stores relevant candidate profiles and assessment information.

Explainability Layer: Assessment outputs are accompanied by explanations of the factors used to generate them.

HR Dashboard: Authorized HR users review candidate submissions and assessment summaries.

📂 Project Structure

CandidAI/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
└── README.md

This is a suggested structure. Adjust the directory names and files to match your actual repository.

⚙️ Installation and Setup

Prerequisites

Python 3.10 or another version supported by your dependencies

Node.js and npm

MongoDB Atlas account

Clerk application credentials

Git

1. Clone the repository

git clone <YOUR_REPOSITORY_URL>
cd CandidAI

2. Configure the backend

cd backend
python -m venv venv

Activate the virtual environment.

Windows:

venv\Scripts\activate

Install the dependencies:

pip install -r requirements.txt

Configure the required environment variables in your backend environment file, including your MongoDB connection string and any necessary AI service credentials.

Start the backend using the command appropriate for your application.

For a FastAPI application:

uvicorn app.main:app --reload

For a Flask application, use the entry point configured in your project.

3. Configure the frontend

Open a new terminal:

cd frontend
npm install

Add your Clerk publishable key to the frontend environment configuration using the variable name expected by your Clerk integration.

Start the development server:

npm run dev

Open the local URL displayed by Vite in your terminal.

🔄 Application Workflow

The candidate signs in through the authentication interface.

The candidate accesses the assigned pre-interview assessment.

The platform collects the supported video, audio, or text responses.

The backend processes responses using the configured AI assessment modules.

Cognitive evaluation and plagiarism checks generate their respective outputs.

The system prepares assessment summaries and available explanations.

Authorized HR users review the results through the dashboard.

🔐 Environment Variables

Create environment files locally and never commit real credentials.

Example configuration:

# Backend
MONGODB_URI=your_mongodb_connection_string
DATABASE_NAME=candid

# Frontend
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key

Use the environment variable names required by your implementation. Keep secret keys, database credentials, and private API tokens out of frontend code and public repositories.

🎯 Project Objectives

Streamline initial candidate screening.

Integrate AI-based analysis into a unified assessment workflow.

Support multimodal candidate responses.

Improve the interpretability of automated assessment outputs.

Help HR teams organize and review candidate assessment data.

Explore responsible applications of AI in recruitment.

🛡️ Responsible AI and Privacy

CandidAI is intended to support—not replace—human decision-making in recruitment.

Assessment outputs should be treated as decision-support signals rather than definitive judgments about a candidate.

Emotion-analysis results should not be treated as reliable measures of personality, honesty, competence, or job suitability.

Candidate recordings and personal information should be handled with appropriate consent, access controls, retention policies, and security measures.

Plagiarism flags and AI-generated scores should be reviewed in context before any action is taken.

The system should be evaluated for bias, accuracy, accessibility, and fairness before use in real hiring decisions.

🔮 Future Enhancements

Real-time assessment progress and status tracking.

More robust speech recognition for different accents.

Improved semantic similarity and plagiarism analysis.

Detailed assessment reports for HR teams.

Role-specific question banks and configurable assessment criteria.

Audit logs, enhanced privacy controls, and fairness evaluation.

Comprehensive automated testing and deployment.

👩‍💻 Author

Developed as an AI-powered recruitment technology project exploring multimodal assessment, NLP, machine learning, and explainable AI.

## 📚 Research Publication

CandidAI is an AI-powered candidate screening platform that explores multimodal assessment, natural language processing, cognitive evaluation, plagiarism detection, and Explainable AI (XAI) to support transparent and structured recruitment.

