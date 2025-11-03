import pandas as pd
import joblib
import warnings
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings('ignore')

# ADD THIS CORRECT VERSION
def prepare_data(filepath, target_column):
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.lower()
    target_column = target_column.lower()

    # Use all columns *except* the target column as features
    X = df.drop(target_column, axis=1) 
    y = df[target_column]

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    # Automatically get the feature names from the columns
    feature_names = X.columns.tolist() 
    return X, y_encoded, encoder, feature_names

def train_all_models(X, y, encoder, dataset_num):
    """Trains and evaluates an expanded list of models."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    models = {
        'Logistic Regression': LogisticRegression(max_iter=2000),
        'Random Forest': RandomForestClassifier(random_state=42),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Support Vector Machine': SVC(),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42)
    }
    trained_models = {}
    
    print(f"\n--- Training and Evaluating Models on Dataset {dataset_num} ---")
    
    for name, model in models.items():
        print(f"\n===== Evaluating: {name} =====")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"   -> Accuracy Score: {acc:.4f}")
        # Re-train on all data for production
        model.fit(X, y) 
        trained_models[name] = model
        
    return trained_models

if __name__ == '__main__':
    print("Starting model training for Crop Recommender...")
    
    # --- Train and Save Models for Dataset 1 ---
    print("Processing Dataset 1 (data1.csv)...")
    X1, y1, encoder1, features1 = prepare_data('data1.csv', target_column='Crop')
    trained_models_ds1 = train_all_models(X1, y1, encoder1, dataset_num=1)
    
    joblib.dump(trained_models_ds1, 'crop_models_ds1.joblib')
    joblib.dump(encoder1, 'crop_encoder1.joblib')
    joblib.dump(features1, 'crop_features1.joblib')
    print("✅ Saved models, encoder, and features for Dataset 1.")

    # --- Train and Save Models for Dataset 2 ---
    print("\nProcessing Dataset 2 (data2.csv)...")
    X2, y2, encoder2, features2 = prepare_data('data2.csv', target_column='label')
    trained_models_ds2 = train_all_models(X2, y2, encoder2, dataset_num=2)
    
    joblib.dump(trained_models_ds2, 'crop_models_ds2.joblib')
    joblib.dump(encoder2, 'crop_encoder2.joblib')
    joblib.dump(features2, 'crop_features2.joblib')
    print("✅ Saved models, encoder, and features for Dataset 2.")

    print("\n--- 🚀 Model Training Complete! ---")
    print("You can now run the main Streamlit app: streamlit run Pahari_Khet_Sahayak.py")