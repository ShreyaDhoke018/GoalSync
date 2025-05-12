import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import pickle
from dataloader import load_data

# Load the data
df = load_data()


# Adding Percentage and CGPA columns (if not already done)
unique_values = df['Grades'].unique()
max_value = max(unique_values).item()
df["Percentage"] = (df["Grades"] / max_value) * 100
df["CGPA"] = (df["Grades"] / max_value) * 10
df["Target CGPA"] = (df["CGPA"]) + 3
df['Improvement_Gap'] = df['Target CGPA'] - df['CGPA']

# Selecting relevant columns for model training
df2 = df[['Study Hours', 'Percentage', 'CGPA', 'Target CGPA', 'Improvement_Gap']]
X2 = df2[['Study Hours']]  # Study hours as feature
y2 = df2[['CGPA']]         # CGPA as target

# Train the Gradient Boosting Regressor model
model_gb = GradientBoostingRegressor()
model_gb.fit(X2, y2)

# Save the trained model to a .pkl file
with open('model_gb.pkl', 'wb') as model_file:
    pickle.dump(model_gb, model_file)

# Load the model from the .pkl file (for future use)
with open('model_gb.pkl', 'rb') as model_file:
    model_gb_loaded = pickle.load(model_file)

# Now you can use the loaded model for predictions
def calculate_study_hours(target_cgpa):
    try:
        predicted_study_hours = model_gb_loaded.predict([[target_cgpa]])  
        return predicted_study_hours[0]
    except Exception as e:
        return f"Error: {str(e)}"

# Example of using the loaded model
target_cgpa = 9.0
required_study_hours = calculate_study_hours(target_cgpa)
print(f"To achieve a CGPA of {target_cgpa}, you should study for {required_study_hours:.2f} hours.")
