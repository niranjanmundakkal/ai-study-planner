import pandas as pd
import numpy as np

def generate_synthetic_data(num_records=5000):
    np.random.seed(42)  # For reproducibility

    # Generate features
    study_hours_per_week = np.random.randint(0, 45, num_records)
    sleep_hours_per_night = np.random.randint(4, 11, num_records)
    extracurricular_hours_per_week = np.random.randint(0, 25, num_records)
    attendance_percentage = np.random.randint(50, 101, num_records)
    midterm_score = np.random.randint(40, 101, num_records)
    stress_level = np.random.randint(1, 11, num_records)

    # DataFrame creation
    df = pd.DataFrame({
        'study_hours_per_week': study_hours_per_week,
        'sleep_hours_per_night': sleep_hours_per_night,
        'extracurricular_hours_per_week': extracurricular_hours_per_week,
        'attendance_percentage': attendance_percentage,
        'midterm_score': midterm_score,
        'stress_level': stress_level
    })

    # Realistic burnout generation logic
    # Burnout is more likely with high stress, low sleep, low attendance, and extreme study hours or low score.
    burnout_score = (
        (df['stress_level'] * 8) + 
        ((10 - df['sleep_hours_per_night']) * 6) + 
        ((100 - df['attendance_percentage']) * 0.5) +
        ((df['study_hours_per_week'] > 30) * 15) -
        (df['study_hours_per_week'] < 10) * 10 
    )

    # Normalize score
    # Introduce some noise to make model training realistic
    noise = np.random.normal(0, 10, num_records)
    burnout_score = burnout_score + noise

    # Threshold for burnout
    threshold = np.percentile(burnout_score, 70) # Top 30% are considered at risk of burnout
    df['burnout'] = (burnout_score >= threshold).astype(int)

    return df

if __name__ == "__main__":
    print("Generating synthetic dataset (5000 records)...")
    dataset = generate_synthetic_data(5000)
    dataset.to_csv('data/student_data.csv', index=False)
    print("Data successfully saved to 'data/student_data.csv'")
    print("Burnout distribution:")
    print(dataset['burnout'].value_counts())
