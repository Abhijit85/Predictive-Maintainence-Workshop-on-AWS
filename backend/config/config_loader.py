import os
import re
import yaml
import logging
from typing import Any, Dict, Optional


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


def resolve_env_variables(data: Any) -> Any:
    """
    Recursively resolves environment variables in configuration data.

    Handles both ${VAR_NAME} and ${VAR_NAME:-default_value} syntax.
    """
    if isinstance(data, dict):
        return {k: resolve_env_variables(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_variables(elem) for elem in data]
    elif isinstance(data, str):
        pattern = re.compile(r"\$\{(\w+)(:-([^}]*))?\}")

        def replace_match(match: re.Match) -> str:
            var_name = match.group(1)
            default_value = match.group(3)

            value = os.environ.get(var_name, default_value)
            if value is None:
                raise ConfigurationError(
                    f"Environment variable '{var_name}' not set and no default provided"
                )
            return value

        return pattern.sub(replace_match, data)
    return data


def load_yaml_config(config_path: str = None) -> Optional[Dict[str, Any]]:
    """Load configuration from YAML file and resolve ${VAR:-default}."""
    if config_path is None:
        # Default to config.yaml in the same directory as this file
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            raw = yaml.safe_load(file)
            return resolve_env_variables(raw) if raw else {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML configuration: {e}")
        return None


def setup_logging_from_config(config: Optional[Dict[str, Any]]) -> None:
    """Setup logging based on YAML configuration — console only for CloudWatch compatibility."""
    if not config:
        return

    logging_config = config.get('logging', {})
    if not logging_config:
        return

    log_level_str = logging_config.get('level')
    if log_level_str is None or log_level_str == '':
        log_level = logging.INFO
    else:
        log_level = getattr(logging, log_level_str.upper())

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )


class BaseConfig:
    """Base configuration with console-only logging and helpers."""
    def __init__(self):
        self.yaml_config = load_yaml_config()

    def _setup_logging(self):
        # Clear existing handlers to avoid conflicts
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )
        if self.yaml_config:
            setup_logging_from_config(self.yaml_config)


class FastAPIConfig(BaseConfig):
    """Configuration for FastAPI server."""

    def __init__(self):
        super().__init__()
        self._setup_logging()
        self._load_config()

    def _load_config(self):
        """Load FastAPI configuration values."""
        server_config = self.yaml_config['server']
        db_config = self.yaml_config['database']
        embeddings_config = self.yaml_config['embeddings']
        models_config = self.yaml_config['models']
        reranker_config = self.yaml_config.get('reranker', {})
        guardrails_config = self.yaml_config.get('guardrails', {})
        alerts_config = self.yaml_config.get('alerts', {})

        # Server configuration
        host = server_config.get('host')
        if host is None or host == '':
            raise ConfigurationError("Server host is required but not specified in configuration")
        self.HOST = host

        port = server_config.get('port')
        if port is None or port == '':
            raise ConfigurationError("Server port is required but not specified in configuration")
        self.PORT = int(port)

        reload = server_config.get('reload')
        if reload is None or reload == '':
            raise ConfigurationError("Server reload setting is required but not specified in configuration")
        self.RELOAD = str(reload).lower() == 'true'

        # Database collections
        input_db = db_config['collections']['input']
        if input_db is None or input_db == '':
            raise ConfigurationError("Input collection is required but not specified in configuration")
        self.INPUT_DB = input_db

        output_db = db_config['collections']['output']
        if output_db is None or output_db == '':
            raise ConfigurationError("Output collection is required but not specified in configuration")
        self.OUTPUT_DB = output_db

        chunks_col = db_config['collections']['chunks']
        if chunks_col is None or chunks_col == '':
            raise ConfigurationError("Chunks collection is required but not specified in configuration")
        self.CHUNKS_COL = chunks_col

        info_col = db_config['collections']['info']
        if info_col is None or info_col == '':
            raise ConfigurationError("Info collection is required but not specified in configuration")
        self.INFO_COL = info_col

        # Embeddings and MongoDB
        embedding_model = embeddings_config.get('model')
        if embedding_model is None or embedding_model == '':
            raise ConfigurationError("Embedding model is required but not specified in configuration")
        self.EMBEDDING_MODEL = embedding_model

        mongo_conn = db_config.get('connection_string')
        if mongo_conn is None or mongo_conn == '':
            raise ConfigurationError("MongoDB connection string is required but not specified in configuration")
        self.MONGO_CONN = mongo_conn

        mongo_db_name = db_config.get('name')
        if mongo_db_name is None or mongo_db_name == '':
            raise ConfigurationError("MongoDB database name is required but not specified in configuration")
        self.MONGO_DB_NAME = mongo_db_name

        # Models folder
        model_folder = models_config.get('model_folder')
        if model_folder is None or model_folder == '':
            raise ConfigurationError("Model folder is required but not specified in configuration")
        # Get the backend directory (parent of config directory)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.MODEL_FOLDER = str(os.path.join(backend_dir, model_folder))

        # Reranker
        self.RERANKER_MODEL = reranker_config.get('model', '')

        # Guardrails
        self.BEDROCK_GUARDRAIL_ID = guardrails_config.get('bedrock_guardrail_id', '')
        self.BEDROCK_GUARDRAIL_VERSION = guardrails_config.get('bedrock_guardrail_version', '')

        # Alerts
        self.SNS_ALERT_TOPIC_ARN = alerts_config.get('sns_topic_arn', '')

    def log_configuration(self):
        """Log current configuration for debugging."""
        logging.info("=== Predictions FastAPI Configuration ===")
        logging.info(f"Host: {self.HOST}")
        logging.info(f"Port: {self.PORT}")
        logging.info(f"Reload: {self.RELOAD}")
        logging.info(f"Collections: {self.INPUT_DB}, {self.OUTPUT_DB}, {self.CHUNKS_COL}, {self.INFO_COL}")
        logging.info(f"Embedding Model: {self.EMBEDDING_MODEL}")
        logging.info(f"Reranker Model: {self.RERANKER_MODEL}")
        logging.info(f"MongoDB: {self.MONGO_DB_NAME}")
        logging.info(f"Models folder: {self.MODEL_FOLDER}")
        logging.info("=========================================")


class ModelsConfig(BaseConfig):
    """Configuration for model training and operations."""

    def __init__(self):
        super().__init__()
        self._setup_logging()
        self._load_config()

    def _load_config(self):
        """Load models configuration values."""
        models_config = self.yaml_config['models']
        db_config = self.yaml_config['database']
        embeddings_config = self.yaml_config['embeddings']

        # Get the backend directory (parent of config directory)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_folder = models_config.get('model_folder')
        if model_folder is None or model_folder == '':
            raise ConfigurationError("Model folder is required but not specified in configuration")
        self.MODEL_FOLDER = str(os.path.join(backend_dir, model_folder))

        encoder_folder = models_config.get('encoder_folder')
        if encoder_folder is None or encoder_folder == '':
            raise ConfigurationError("Encoder folder is required but not specified in configuration")
        self.ENCODER_FOLDER = str(os.path.join(backend_dir, encoder_folder))

        dataset_folder = models_config.get('dataset_folder')
        if dataset_folder is None or dataset_folder == '':
            raise ConfigurationError("Dataset folder is required but not specified in configuration")
        self.DATASET_FOLDER = str(os.path.join(backend_dir, dataset_folder))

        test_size = models_config.get('test_size')
        if test_size is None or test_size == '':
            raise ConfigurationError("Test size is required but not specified in configuration")
        self.TEST_SIZE = float(test_size)

        random_state = models_config.get('random_state')
        if random_state is None or random_state == '':
            raise ConfigurationError("Random state is required but not specified in configuration")
        self.RANDOM_STATE = int(random_state)

        # Database collections
        input_db = db_config['collections']['input']
        if input_db is None or input_db == '':
            raise ConfigurationError("Input collection is required but not specified in configuration")
        self.INPUT_DB = input_db

        output_db = db_config['collections']['output']
        if output_db is None or output_db == '':
            raise ConfigurationError("Output collection is required but not specified in configuration")
        self.OUTPUT_DB = output_db

        chunks_col = db_config['collections']['chunks']
        if chunks_col is None or chunks_col == '':
            raise ConfigurationError("Chunks collection is required but not specified in configuration")
        self.CHUNKS_COL = chunks_col

        info_col = db_config['collections']['info']
        if info_col is None or info_col == '':
            raise ConfigurationError("Info collection is required but not specified in configuration")
        self.INFO_COL = info_col

        # Embeddings and MongoDB
        embedding_model = embeddings_config.get('model')
        if embedding_model is None or embedding_model == '':
            raise ConfigurationError("Embedding model is required but not specified in configuration")
        self.EMBEDDING_MODEL = embedding_model

        mongo_conn = db_config.get('connection_string')
        if mongo_conn is None or mongo_conn == '':
            raise ConfigurationError("MongoDB connection string is required but not specified in configuration")
        self.MONGO_CONN = mongo_conn

        mongo_db_name = db_config.get('name')
        if mongo_db_name is None or mongo_db_name == '':
            raise ConfigurationError("MongoDB database name is required but not specified in configuration")
        self.MONGO_DB_NAME = mongo_db_name

    def log_configuration(self):
        """Log current configuration for debugging."""
        logging.info("=== Models Configuration ===")
        logging.info(f"Model Folder: {self.MODEL_FOLDER}")
        logging.info(f"Encoder Folder: {self.ENCODER_FOLDER}")
        logging.info(f"Dataset Folder: {self.DATASET_FOLDER}")
        logging.info(f"Test Size: {self.TEST_SIZE}")
        logging.info(f"Random State: {self.RANDOM_STATE}")
        logging.info(f"Collections: {self.INPUT_DB}, {self.OUTPUT_DB}, {self.CHUNKS_COL}, {self.INFO_COL}")
        logging.info(f"Embedding Model: {self.EMBEDDING_MODEL}")
        logging.info(f"MongoDB: {self.MONGO_DB_NAME}")
        logging.info("============================")


class DataProcessingConfig(BaseConfig):
    """Configuration for data processing operations."""

    def __init__(self, script_type: str = "generate_csv"):
        super().__init__()
        self._setup_logging()
        self._load_config()

    def _load_config(self):
        """Load data processing configuration values."""
        models_config = self.yaml_config['models']
        db_config = self.yaml_config['database']
        embeddings_config = self.yaml_config['embeddings']
        data_processing_config = self.yaml_config.get('data_processing', {})

        # Model configuration - resolve paths relative to backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.MODEL_FOLDER = str(os.path.join(backend_dir, models_config['model_folder']))
        self.ENCODER_FOLDER = str(os.path.join(backend_dir, models_config['encoder_folder']))
        self.DATASET_FOLDER = str(os.path.join(backend_dir, models_config['dataset_folder']))
        self.TEST_SIZE = float(models_config['test_size'])
        self.RANDOM_STATE = int(models_config['random_state'])

        # Database collections
        self.INPUT_DB = db_config['collections']['input']
        self.OUTPUT_DB = db_config['collections']['output']
        self.CHUNKS_COL = db_config['collections']['chunks']
        self.INFO_COL = db_config['collections']['info']

        # Embeddings and MongoDB
        self.EMBEDDING_MODEL = embeddings_config['model']
        self.MONGO_CONN = db_config['connection_string']
        self.MONGO_DB_NAME = db_config['name']

        # Embedding parameters
        chunk_size = embeddings_config.get('chunk_size')
        if chunk_size is None or chunk_size == '':
            raise ConfigurationError("Chunk size is required but not specified in configuration")
        self.CHUNK_SIZE = int(chunk_size)

        overlap_size = embeddings_config.get('overlap_size')
        if overlap_size is None or overlap_size == '':
            raise ConfigurationError("Overlap size is required but not specified in configuration")
        self.OVERLAP_SIZE = int(overlap_size)

        # Data processing specific
        folder = data_processing_config.get('folder')
        if folder is None or folder == '':
            raise ConfigurationError("Data processing folder is required but not specified in configuration")
        self.DATA_PROCESSING_FOLDER = folder

        info_path = data_processing_config.get('info_path')
        if info_path is None or info_path == '':
            raise ConfigurationError("Info path is required but not specified in configuration")
        self.INFO_PATH = info_path

    def log_configuration(self):
        """Log current configuration for debugging."""
        logging.info("=== Data Processing Configuration ===")
        logging.info(f"Model Folder: {self.MODEL_FOLDER}")
        logging.info(f"Encoder Folder: {self.ENCODER_FOLDER}")
        logging.info(f"Dataset Folder: {self.DATASET_FOLDER}")
        logging.info(f"Test Size: {self.TEST_SIZE}")
        logging.info(f"Random State: {self.RANDOM_STATE}")
        logging.info(f"Collections: {self.INPUT_DB}, {self.OUTPUT_DB}, {self.CHUNKS_COL}, {self.INFO_COL}")
        logging.info(f"Embedding Model: {self.EMBEDDING_MODEL}")
        logging.info(f"Chunk Size: {self.CHUNK_SIZE}")
        logging.info(f"Overlap Size: {self.OVERLAP_SIZE}")
        logging.info(f"MongoDB: {self.MONGO_DB_NAME}")
        logging.info(f"Data Processing Folder: {self.DATA_PROCESSING_FOLDER}")
        logging.info(f"Info Path: {self.INFO_PATH}")
        logging.info("=====================================")


class IngestionConfig(BaseConfig):
    """Configuration for data ingestion operations."""

    def __init__(self):
        super().__init__()
        self._setup_logging()
        self._load_config()

    def _load_config(self):
        """Load ingestion configuration values."""
        db_config = self.yaml_config['database']
        embeddings_config = self.yaml_config['embeddings']

        # Database collections
        self.INPUT_DB = db_config['collections']['input']
        self.OUTPUT_DB = db_config['collections']['output']
        self.CHUNKS_COL = db_config['collections']['chunks']
        self.INFO_COL = db_config['collections']['info']

        # Embeddings and MongoDB
        self.EMBEDDING_MODEL = embeddings_config['model']
        self.MONGO_CONN = db_config['connection_string']
        self.MONGO_DB_NAME = db_config['name']

    def log_configuration(self):
        """Log current configuration for debugging."""
        logging.info("=== Ingestion Configuration ===")
        logging.info(f"Collections: {self.INPUT_DB}, {self.OUTPUT_DB}, {self.CHUNKS_COL}, {self.INFO_COL}")
        logging.info(f"Embedding Model: {self.EMBEDDING_MODEL}")
        logging.info(f"MongoDB: {self.MONGO_DB_NAME}")
        logging.info("===============================")


class SimulationConfig(BaseConfig):
    """Configuration for simulation operations."""

    def __init__(self):
        super().__init__()
        self._setup_logging()
        self._load_config()

    def _load_config(self):
        """Load simulation configuration values."""
        models_config = self.yaml_config['models']
        db_config = self.yaml_config['database']
        embeddings_config = self.yaml_config['embeddings']

        # Model configuration - resolve paths relative to backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.MODEL_FOLDER = str(os.path.join(backend_dir, models_config['model_folder']))
        self.ENCODER_FOLDER = str(os.path.join(backend_dir, models_config['encoder_folder']))
        self.DATASET_FOLDER = str(os.path.join(backend_dir, models_config['dataset_folder']))

        # Database collections
        self.INPUT_DB = db_config['collections']['input']
        self.OUTPUT_DB = db_config['collections']['output']
        self.CHUNKS_COL = db_config['collections']['chunks']
        self.INFO_COL = db_config['collections']['info']

        # Embeddings and MongoDB
        self.EMBEDDING_MODEL = embeddings_config['model']
        self.MONGO_CONN = db_config['connection_string']
        self.MONGO_DB_NAME = db_config['name']

    def log_configuration(self):
        """Log current configuration for debugging."""
        logging.info("=== Simulation Configuration ===")
        logging.info(f"Model Folder: {self.MODEL_FOLDER}")
        logging.info(f"Encoder Folder: {self.ENCODER_FOLDER}")
        logging.info(f"Dataset Folder: {self.DATASET_FOLDER}")
        logging.info(f"Collections: {self.INPUT_DB}, {self.OUTPUT_DB}, {self.CHUNKS_COL}, {self.INFO_COL}")
        logging.info(f"Embedding Model: {self.EMBEDDING_MODEL}")
        logging.info(f"MongoDB: {self.MONGO_DB_NAME}")
        logging.info("================================")


class StreamingConfig(BaseConfig):
    """Configuration for streaming operations."""

    def __init__(self):
        super().__init__()
        self._setup_logging()
        self._load_config()

    def _load_config(self):
        """Load streaming configuration values."""
        server_config = self.yaml_config['server']
        db_config = self.yaml_config['database']
        embeddings_config = self.yaml_config['embeddings']
        alerts_config = self.yaml_config.get('alerts', {})

        # Server configuration
        host = server_config.get('host')
        if host is None or host == '':
            raise ConfigurationError("Server host is required but not specified in configuration")
        self.HOST = host

        port = server_config.get('port')
        if port is None or port == '':
            raise ConfigurationError("Server port is required but not specified in configuration")
        self.PORT = int(port)

        # Database collections
        self.INPUT_DB = db_config['collections']['input']
        self.OUTPUT_DB = db_config['collections']['output']
        self.CHUNKS_COL = db_config['collections']['chunks']
        self.INFO_COL = db_config['collections']['info']

        # Embeddings and MongoDB
        self.EMBEDDING_MODEL = embeddings_config['model']
        self.MONGO_CONN = db_config['connection_string']
        self.MONGO_DB_NAME = db_config['name']

        # Alerts
        self.SNS_ALERT_TOPIC_ARN = alerts_config.get('sns_topic_arn', '')

    def log_configuration(self):
        """Log current configuration for debugging."""
        logging.info("=== Streaming Configuration ===")
        logging.info(f"Host: {self.HOST}")
        logging.info(f"Port: {self.PORT}")
        logging.info(f"Collections: {self.INPUT_DB}, {self.OUTPUT_DB}, {self.CHUNKS_COL}, {self.INFO_COL}")
        logging.info(f"Embedding Model: {self.EMBEDDING_MODEL}")
        logging.info(f"MongoDB: {self.MONGO_DB_NAME}")
        logging.info("===============================")


# Global configuration instances
fastapi_config = FastAPIConfig()
models_config = ModelsConfig()
data_processing_config = DataProcessingConfig()
ingestion_config = IngestionConfig()
simulation_config = SimulationConfig()
streaming_config = StreamingConfig()
