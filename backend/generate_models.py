import os
import platform
import warnings
import pickle
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from sklearn.model_selection import train_test_split, cross_val_score, RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from tabulate import tabulate
import logging
import certifi

warnings.filterwarnings('ignore')

sys.path.append(str(Path(__file__).parent))
from config.config_loader import ModelsConfig

# Create our own config instance to avoid logging conflicts
models_config = ModelsConfig()
models_config.log_configuration()

model_folder = models_config.MODEL_FOLDER
encoder_folder = models_config.ENCODER_FOLDER
dataset_folder = models_config.DATASET_FOLDER
test_size = models_config.TEST_SIZE
random_state = models_config.RANDOM_STATE
INPUT_DB_NAME = models_config.INPUT_DB

os.makedirs(model_folder, exist_ok=True)
os.makedirs(encoder_folder, exist_ok=True)


def load_and_scale_datasets(db):
    datasets = []
    scaler = StandardScaler()
    csv_files = [f for f in os.listdir(dataset_folder) if f.endswith('.csv')]

    if not csv_files:
        logging.error("No CSV files found in the dataset folder.")
        raise FileNotFoundError("No CSV files found.")

    for file in csv_files:
        path = os.path.join(dataset_folder, file)
        try:
            df = pd.read_csv(path)
            if df.shape[1] < 2:
                logging.warning(f"Skipping file {file} due to insufficient columns.")
                continue

            independent_cols = df.columns[:-1]
            dependent_col = df.columns[-1]

            df[independent_cols] = scaler.fit_transform(df[independent_cols])
            df[dependent_col] = df[dependent_col].astype('int64')
            datasets.append(df)

            with open(os.path.join(encoder_folder, f'{dependent_col.lower()}_scaler.pkl'), 'wb') as f:
                pickle.dump(scaler, f)

            # Create mongo collection if it doesn't exist
            if dependent_col.lower() not in db.list_collection_names():
                db.create_collection(dependent_col.lower())
                logging.info(f"Created collection {dependent_col.lower()} in database {INPUT_DB_NAME}.")

        except Exception as e:
            logging.error(f"Error processing file {file}: {e}")

    return datasets

def calculate_metrics(y_true, y_pred, model_name):
    average_method = 'binary' if len(np.unique(y_true)) == 2 else 'weighted'
    return {
        'model': model_name,
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average=average_method, zero_division=0),
        'recall': recall_score(y_true, y_pred, average=average_method, zero_division=0),
        'f1_score': f1_score(y_true, y_pred, average=average_method, zero_division=0)
    }

def delete_model_file(model_path):
    try:
        if os.path.exists(model_path):
            os.remove(model_path)
            logging.info(f"Deleted model file: {model_path}")
            return True
        else:
            logging.warning(f"Model file not found for deletion: {model_path}")
            return False
    except Exception as e:
        logging.error(f"Error deleting model file {model_path}: {e}")
        return False

def calculate_composite_score(metrics):
    weights = {
        'accuracy': 0.3,
        'precision': 0.2,
        'recall': 0.2,
        'f1_score': 0.3
    }
    
    composite_score = (
        metrics['accuracy'] * weights['accuracy'] +
        metrics['precision'] * weights['precision'] +
        metrics['recall'] * weights['recall'] +
        metrics['f1_score'] * weights['f1_score']
    )
    
    return composite_score

def train_and_evaluate_models(datasets):
    results = ""

    for df in datasets:
        dependent_col = df.columns[-1]
        x = df.drop(columns=[dependent_col])
        y = LabelEncoder().fit_transform(df[dependent_col])

        encoder_path = os.path.join(encoder_folder, f'{dependent_col.lower()}.pkl')
        with open(encoder_path, 'wb') as f:
            pickle.dump(LabelEncoder().fit(df[dependent_col]), f)

        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=random_state)
        cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=random_state)

        models = {
            "Logistic Regression": LogisticRegression(penalty="l1", C=1.0, max_iter=1000, multi_class='multinomial', solver='saga'),
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=random_state)
        }

        table_data = [["Model", "CV Mean ± Std", "Accuracy", "Precision", "Recall", "F1 Score"]]
        model_performances = {}  # Store performance data for comparison
        model_paths = {}  # Store model file paths

        for name, model in models.items():
            try:
                logging.info(f"=== Training {name} on target {dependent_col}...")
                n_jobs = 1 if platform.system() == "Windows" else -1
                scores = cross_val_score(model, x_train, y_train, scoring='accuracy', cv=cv, n_jobs=n_jobs)
                model.fit(x_train, y_train)
                y_pred = model.predict(x_test)
                metrics = calculate_metrics(y_test, y_pred, name)

                # Calculate composite score for comparison
                composite_score = calculate_composite_score(metrics)
                
                model_path = os.path.join(model_folder, f"{name.replace(' ', '_')}-{dependent_col.lower()}.pkl")
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)

                model_performances[name] = {
                    'metrics': metrics,
                    'composite_score': composite_score,
                    'cv_mean': scores.mean(),
                    'cv_std': scores.std()
                }
                model_paths[name] = model_path

                table_data.append([
                    name,
                    f"{scores.mean():.4f} ± {scores.std():.4f}",
                    f"{metrics['accuracy']:.4f}",
                    f"{metrics['precision']:.4f}",
                    f"{metrics['recall']:.4f}",
                    f"{metrics['f1_score']:.4f}",
                    f"{composite_score:.4f}"
                ])
            except Exception as e:
                logging.error(f"Error training {name} on target {dependent_col}: {e}")

        if len(model_performances) >= 2:
            # Sort models by composite score (descending order)
            sorted_models = sorted(model_performances.items(), 
                                 key=lambda x: x[1]['composite_score'], 
                                 reverse=True)
            
            best_model_name, best_model_data = sorted_models[0]
            worst_model_name, worst_model_data = sorted_models[-1]
            
            # Check if there's actually a difference in performance
            score_difference = best_model_data['composite_score'] - worst_model_data['composite_score']
            
            if score_difference > 1e-6:  # Only delete if there's a meaningful difference
                # Delete the worst performing model
                worst_model_path = model_paths[worst_model_name]
                if delete_model_file(worst_model_path):
                    logging.info(f"Deleted worst performing model: {worst_model_name} (Composite Score: {worst_model_data['composite_score']:.6f})")
                    logging.info(f"Kept best performing model: {best_model_name} (Composite Score: {best_model_data['composite_score']:.6f})")
                
                # Add information about which model was kept/deleted to results
                results += f"\n== Target: {dependent_col} ==\n"
                results += f"BEST MODEL KEPT: {best_model_name} (Composite Score: {best_model_data['composite_score']:.6f})\n"
                results += f"WORST MODEL DELETED: {worst_model_name} (Composite Score: {worst_model_data['composite_score']:.6f})\n"
                results += f"Performance difference: {score_difference:.6f}\n"
            else:
                # Models perform equally - keep the simpler/faster one (Logistic Regression)
                if "Logistic Regression" in model_performances and "Random Forest" in model_performances:
                    model_to_delete = "Random Forest"
                    model_to_keep = "Logistic Regression"
                else:
                    # Fallback: delete the second model alphabetically
                    model_to_delete = sorted_models[-1][0]
                    model_to_keep = sorted_models[0][0]
                
                delete_model_path = model_paths[model_to_delete]
                if delete_model_file(delete_model_path):
                    logging.info(f"Models perform equally. Deleted more complex model: {model_to_delete}")
                    logging.info(f"Kept simpler model: {model_to_keep}")
                
                results += f"\n== Target: {dependent_col} ==\n"
                results += f"MODELS PERFORM EQUALLY (Score: {best_model_data['composite_score']:.6f})\n"
                results += f"KEPT SIMPLER MODEL: {model_to_keep}\n"
                results += f"DELETED COMPLEX MODEL: {model_to_delete}\n"
            
            results += "\nModel Performance Comparison:\n"
        else:
            results += f"\n== Target: {dependent_col} ==\n"
            if model_performances:
                remaining_model = list(model_performances.keys())[0]
                logging.info(f"Only one model trained successfully: {remaining_model}")
                results += f"Only one model available: {remaining_model}\n"
        
        results += tabulate(table_data[1:], headers=table_data[0], tablefmt="grid")
        results += "\n"

    return results

if __name__ == "__main__":
    mongo_uri = models_config.MONGO_CONN
    if not mongo_uri:
        logging.error("MONGODB_CONNECTION_STRING not set in environment variable or config.yaml")
        exit(1)

    client = MongoClient(mongo_uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

    input_db = client[INPUT_DB_NAME]
    
    try:
        datasets = load_and_scale_datasets(input_db)

        logging.info("Starting model training from CSV datasets...")
        results = train_and_evaluate_models(datasets)

        results_path = os.path.join(model_folder, 'results.txt')
        with open(results_path, 'w') as f:
            f.write(results)

        logging.info(f"Training complete. Results saved to {results_path}")
        logging.info("*Note: Worst performing models have been automatically deleted.")
    except Exception as e:
        logging.exception(f"Failed to complete model training: {e}")
        exit(1)