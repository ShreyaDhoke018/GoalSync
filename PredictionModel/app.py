from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np
import pickle

# Initialize the Flask app
app = Flask(__name__)

# Load the models and metadata
try:
    # Load the saved model
    with open('model_gb.pkl', 'rb') as model_file:
        model_gb = pickle.load(model_file)
    
    # Load classification model
    model_classify = joblib.load('model_classify.pkl')
    classifier = model_classify['classifier']
    regressor = model_classify['regressor']
    label_encoders = model_classify['label_encoders']  # Loaded label encoders for categorical features
    cat_features = model_classify['metadata']['categorical_features']
    print("Classification model loaded successfully.")

except Exception as e:
    print(f"Error loading models: {str(e)}")
    raise

# Function to calculate required study hours based on CGPA
def calculate_study_hours(target_cgpa):
    try:
        predicted_study_hours = model_gb.predict([[target_cgpa]])  
        return predicted_study_hours[0]
    except Exception as e:
        return f"Error: {str(e)}"

# Routes
@app.route('/')
def home():
    """Root route providing API details."""
    return jsonify({
        "message": "Welcome to the CGPA and Learning Skill Prediction API!",
        "endpoints": {
            "/predict_cgpa": "GET - Predict required study hours for a target CGPA.",
            "/predict": "POST - Predict learning skill level and CGPA."
        }
    })

@app.route('/predict_cgpa', methods=['GET'])
def predict_cgpa():
    target_cgpa = request.args.get('target_cgpa', type=float)
    
    if target_cgpa is None:
        return jsonify({"error": "Target CGPA is required."}), 400
    
    if target_cgpa < 0 or target_cgpa > 10:
        return jsonify({"error": "CGPA must be between 0 and 10."}), 400

    required_study_hours = calculate_study_hours(target_cgpa)
    return jsonify({
        "message": f"To achieve a CGPA of {target_cgpa}, you should study for {required_study_hours:.2f} hours."
    })


# API endpoint to predict learning skill level and CGPA
@app.route('/predict', methods=['POST'])
def predict_learning_skill():
    try:
        # Validate input
        data = request.json
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Expected fields
        required_fields = [
            "productive_time", "learning_preference", "focus_span",
            "review_frequency", "exam_preparation", "note_taking",
            "question_asking", "concept_handling", "organization"
        ]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

        # Create a DataFrame for the input
        user_features = pd.DataFrame([data])

        # Apply label encoding to categorical features in the user's input
        for col in cat_features:
            if user_features[col].iloc[0] not in label_encoders[col].classes_:
                user_features[col] = -1  # Assign a placeholder value for unknown categories
            else:
                user_features[col] = label_encoders[col].transform(user_features[col])

        # Convert categorical columns to a numeric format (dense array)
        user_encoded = user_features.values  # Use the values as a numpy array

        # Predict learning skill level and CGPA
        y_class_pred = classifier.predict(user_encoded)[0]
        y_reg_pred = regressor.predict(user_encoded)[0]

        # Return predicted CGPA as the result
        return jsonify({
            "predicted_cgpa": round(y_reg_pred, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
