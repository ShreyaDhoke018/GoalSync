import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from catboost import CatBoostClassifier, CatBoostRegressor
import joblib
from dataloader import load_data2
from sklearn.preprocessing import LabelEncoder

# Load the data
df = load_data2()

# Encode the classification target
df["learning_skill_encoded"] = df["learning_skill_level"].map({
    "Below Average": 0,
    "Average": 1,
    "Above Average": 2
})

# Define features and targets
X = df.drop(columns=["learning_skill_level", "learning_skill_encoded", "capable_cgpa"])
y_class = df["learning_skill_encoded"]
y_reg = df["capable_cgpa"]

# Detect categorical columns
cat_features = X.select_dtypes(include=['object']).columns.tolist()

# Apply Label Encoding to categorical columns
label_encoders = {}
for col in cat_features:
    label_encoders[col] = LabelEncoder()
    X[col] = label_encoders[col].fit_transform(X[col])

# Train/test split
X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
    X, y_class, y_reg, test_size=0.2, random_state=42
)

# Apply SMOTE to balance the classification target in the training set
smote = SMOTE(random_state=42)
X_train_smote, y_class_train_smote = smote.fit_resample(X_train, y_class_train)

# Classification Model
classifier = CatBoostClassifier(
    iterations=200,
    learning_rate=0.1,
    depth=6,
    verbose=0,
    random_seed=42
)
classifier.fit(X_train_smote, y_class_train_smote)

# Regression Model
regressor = CatBoostRegressor(
    iterations=200,
    learning_rate=0.1,
    depth=6,
    verbose=0,
    random_seed=42
)
regressor.fit(X_train, y_reg_train)

# Save models and metadata
model_data = {
    'classifier': classifier,
    'regressor': regressor,
    'label_encoders': label_encoders,  # Save label encoders for future use
    'metadata': {
        'categorical_features': cat_features
    }
}

joblib.dump(model_data, 'model_classify.pkl')
print("Models and label encoders saved to 'model_classify.pkl'")
