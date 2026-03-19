import pickle
import sys
from pathlib import Path

# Add parent directory to path to import config_loader
sys.path.append(str(Path(__file__).parent.parent))
from config.config_loader import models_config

# Use configuration instead of hardcoded paths
model_folder = models_config.MODEL_FOLDER
encoder_folder = models_config.ENCODER_FOLDER

extensions = {'.pkl', '.pickle'}

model_prefixes = ["Logistic_Regression-", "Random_Forest-"]

def load_model(model_identifier):
    try:
        models_path = Path(model_folder)
        model_path = models_path / f"{model_identifier}.pkl"
        
        if not model_path.exists():
            model_path = models_path / f"{model_identifier}.pickle"
            if not model_path.exists():
                return None, f"Model '{model_identifier}' not found in {models_path}"
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model, None
    except Exception as e:
        return None, f"Error loading model: {str(e)}"
    
def load_encoder(model_identifier):
    """Load encoder for a given model identifier"""
    try:
        # Use the absolute encoder_folder path
        encoders_path = Path(encoder_folder)
        encoder_path = encoders_path / f"{model_identifier}.pkl"
        
        if not encoder_path.exists():
            encoder_path = encoders_path / f"{model_identifier}.pickle"
            if not encoder_path.exists():
                return None, f"Encoder '{model_identifier}' not found in {encoders_path}"
        
        with open(encoder_path, 'rb') as f:
            encoder = pickle.load(f)
        return encoder, None
    except Exception as e:
        return None, f"Error loading encoder: {str(e)}"

def load_scaler(model_identifier):
    """Load scaler for a given model identifier"""
    try:
        # Assuming scalers are in the same directory as models
        encoders_path = Path(encoder_folder)
        scaler_path = encoders_path / f"{model_identifier}_scaler.pkl"
        
        if not scaler_path.exists():
            scaler_path = encoders_path / f"{model_identifier}_scaler.pickle"
            if not scaler_path.exists():
                return None, f"Scaler '{model_identifier}' not found in {encoders_path}"
        
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        return scaler, None
    except Exception as e:
        return None, f"Error loading scaler: {str(e)}"

def validate_input_data(data):
    """Validate input data for prediction"""
    try:
        if not isinstance(data, dict):
            return False, "Input must be a dictionary"
        if 'independent_variables' not in data:
            return False, "Missing 'independent_variables' field"
        if 'model_identifier' not in data:
            return False, "Missing 'model_identifier' field"
        if not isinstance(data['independent_variables'], list):
            return False, "'independent_variables' must be a list"
        if not data['independent_variables']:
            return False, "'independent_variables' cannot be empty"
        return True, None
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def get_model_name(source_name):
    # Convert source_name to lowercase for case-insensitive matching
    source_name_lower = source_name.lower()
    
    # First try to find a model that exactly matches the source name
    for ext in extensions:
        for model_path in Path(model_folder).glob(f"*{ext}"):
            model_name = model_path.stem
            # Remove the model prefix (e.g., "Logistic_Regression-" or "Random_Forest-")
            for prefix in model_prefixes:
                if model_name.startswith(prefix):
                    model_base_name = model_name[len(prefix):].lower()
                    if model_base_name == source_name_lower:
                        return model_name
    
    # If no exact match, try substring matching as fallback
    for ext in extensions:
        for model_path in Path(model_folder).glob(f"*{ext}"):
            model_name = model_path.stem
            if source_name_lower in model_name.lower():
                return model_name
    return None
