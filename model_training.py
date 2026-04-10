import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import os

def train_and_save_model():
    data_path = 'data/student_data.csv'
    model_path = 'model/rf_model.joblib'

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Please run data_generation.py first.")
        return

    print("Loading data...")
    df = pd.read_csv(data_path)

    # Separate features and target
    X = df.drop('burnout', axis=1)
    y = df['burnout']

    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest Classifier...")
    # Initialize and train model
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    rf_model.fit(X_train, y_train)

    # Evaluate
    print("Evaluating model...")
    y_pred = rf_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save model
    print(f"Saving model to {model_path}...")
    joblib.dump(rf_model, model_path)
    
    # Save the feature names to ensure order in the web app
    feature_names_path = 'model/feature_names.joblib'
    joblib.dump(X.columns.tolist(), feature_names_path)
    print("Model and metadata saved successfully!")

if __name__ == "__main__":
    train_and_save_model()
