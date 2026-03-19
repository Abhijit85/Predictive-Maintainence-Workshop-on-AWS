import os
import logging
import pandas as pd
import random
import sys
from pathlib import Path
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import certifi

sys.path.append(str(Path(__file__).parent))
from config.config_loader import SimulationConfig

# Create our own config instance to avoid logging conflicts
simulation_config = SimulationConfig()
simulation_config.log_configuration()

dataset_folder = simulation_config.DATASET_FOLDER
INPUT_DB_NAME = simulation_config.INPUT_DB
INFO_COLLECTION = simulation_config.INFO_COL
CHUNKS_COLLECTION = simulation_config.CHUNKS_COL

if __name__ == "__main__":
    mongo_uri = simulation_config.MONGO_CONN
    if not mongo_uri:
        logging.error("MONGODB_CONNECTION_STRING not set in environment variable or config.yaml")
        exit(1)

    csv_files = [f for f in os.listdir(dataset_folder) if f.endswith('.csv')]
    if not csv_files:
        logging.error("No CSV files found in the dataset folder.")
        exit(1)

    datasets = {}

    # Obtain full dataset for random sampling in specified folder
    for file in csv_files:
        path = os.path.join(dataset_folder, file)
        try:
            df = pd.read_csv(path)
            if df.shape[1] < 2:
                logging.warning(f"Skipping file {file} due to insufficient columns.")
                continue

            independent_cols = df.columns[:-1]
            dependent_col = df.columns[-1]
            datasets[dependent_col.lower()] = df[independent_cols]

        except Exception as e:
            logging.error(f"Error processing file {file}: {e}")

    try:
        with MongoClient(mongo_uri, server_api=ServerApi('1'), tlsCAFile=certifi.where()) as client:
            db = client[INPUT_DB_NAME]

            source_collections = [
                c for c in db.list_collection_names()
                if c not in (INFO_COLLECTION, CHUNKS_COLLECTION)
            ]

            # Ensure every dataset has a matching collection.
            # On a fresh DB this bootstraps all collections from CSV filenames.
            # On an existing DB this creates collections for any newly added datasets
            # (e.g. stable_flag, motor_power) that don't have collections yet.
            missing = [k for k in datasets.keys() if k not in source_collections]
            if missing:
                logging.info(f"Creating missing collections from datasets: {missing}")
                for name in missing:
                    db.create_collection(name)
                source_collections.extend(missing)

            logging.info("/// SIMULATION ROUND ///")
            for collection_name in source_collections:
                coll = db[collection_name]
                df = datasets.get(collection_name)
                if df is None or df.empty:
                    logging.warning(f"No dataset available for collection '{collection_name}'. Skipping.")
                    continue

                row = random.randint(0, df.shape[0]-1)
                data = df.iloc[row]
                data = data.to_dict()

                logging.info(f"[{coll._full_name}]: {data}")
                coll.insert_one(data)

            logging.info("Simulation round complete.")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
