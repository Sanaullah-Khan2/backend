import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

import zipfile

print("Step 1: Loading Local Dataset...")

try:
    dataset_path = r"D:\University\FYP\eduAiMS claud\backend\predict+students+dropout+and+academic+success.zip"
    z = zipfile.ZipFile(dataset_path)
    df = pd.read_csv(z.open('data.csv'), sep=';')
    
    # Map UCI 36 features to the 5 specific features expected by our AI Engine
    X = pd.DataFrame()
    
    # 1. attendance_pct (Proxy: Ratio of approved units to enrolled units, scaled to 100)
    approved = df['Curricular units 1st sem (approved)'] + df['Curricular units 2nd sem (approved)']
    enrolled = df['Curricular units 1st sem (enrolled)'] + df['Curricular units 2nd sem (enrolled)']
    enrolled = enrolled.replace(0, 1) # Avoid division by zero
    X['attendance_pct'] = (approved / enrolled) * 100
    X['attendance_pct'] = X['attendance_pct'].clip(upper=100).fillna(50)
    
    # 2. grade_avg (UCI uses 0-20 scale, multiply by 5 for 0-100)
    avg_grade = (df['Curricular units 1st sem (grade)'] + df['Curricular units 2nd sem (grade)']) / 2
    X['grade_avg'] = avg_grade * 5
    
    # 3. grade_trend (Difference between 2nd sem and 1st sem)
    X['grade_trend'] = (df['Curricular units 2nd sem (grade)'] - df['Curricular units 1st sem (grade)']) * 5
    
    # 4. fee_default (Inverse of 'Tuition fees up to date')
    X['fee_default'] = 1 - df['Tuition fees up to date']
    
    # 5. behavior_count (Proxy using Debtor and Age just to create a distribution)
    X['behavior_count'] = df['Debtor'] * 3
    
    y = df['Target']
    print(f"Dataset loaded: {X.shape[0]} students, {X.shape[1]} features")
except Exception as e:
    print(f"Failed to load local dataset: {e}")
    sys.exit(1)

print("Step 2: Preparing features...")

# Use only numeric columns
X_numeric = X.select_dtypes(include=[np.number])
X_numeric = X_numeric.fillna(X_numeric.median())

# Encode target
le = LabelEncoder()
if hasattr(y, 'values'):
    y_flat = y.values.ravel()
else:
    y_flat = y.ravel()
y_encoded = le.fit_transform(y_flat)

print(f"Classes: {le.classes_}")
print(f"Features used: {list(X_numeric.columns)}")

print("Step 3: Training Random Forest model...")

X_train, X_test, y_train, y_test = train_test_split(
    X_numeric, y_encoded, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced'
)
model.fit(X_train, y_train)

print("Step 4: Evaluating model...")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {accuracy * 100:.1f}%\n")
print("Detailed Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

print("Step 5: Saving model...")
os.makedirs('apps/ai_engine/model', exist_ok=True)

model_data = {
    'model':        model,
    'label_encoder': le,
    'feature_names': list(X_numeric.columns),
    'accuracy':     accuracy,
    'classes':      list(le.classes_),
}

with open('apps/ai_engine/model/risk_model.pkl', 'wb') as f:
    pickle.dump(model_data, f)

print(f"\nModel saved to: apps/ai_engine/model/risk_model.pkl")
print(f"Final accuracy: {accuracy * 100:.1f}%")
print("Training complete!")
