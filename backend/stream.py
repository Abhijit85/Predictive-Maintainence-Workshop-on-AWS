import logging
import os
import sys
from pathlib import Path
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import requests
import threading
import time
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from utils.utils import get_model_name, model_prefixes
from config.config_loader import StreamingConfig

# Create our own config instance to avoid logging conflicts
streaming_config = StreamingConfig()
streaming_config.log_configuration()

# Initialize SNS client for critical alerts
sns_client = None
SNS_TOPIC_ARN = streaming_config.SNS_ALERT_TOPIC_ARN
if SNS_TOPIC_ARN:
    try:
        import boto3
        sns_client = boto3.client('sns')
        logging.info(f"SNS alerting enabled: {SNS_TOPIC_ARN}")
    except Exception as e:
        logging.warning(f"Failed to initialize SNS client: {e}")


def publish_alert(subject, message):
    """Publish a critical alert to SNS."""
    if sns_client and SNS_TOPIC_ARN:
        try:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject[:100],
                Message=message
            )
            logging.info(f"SNS alert published: {subject}")
        except Exception as e:
            logging.error(f"Failed to publish SNS alert: {e}")


def ping(client):
    try:
        client.admin.command('ping')
        logging.info("Pinged your deployment. Successfully connected to MongoDB!")
    except Exception as e:
        logging.error(f"Connection error: {e}")
        raise

def stream_prediction(server_uri, model, source_col, description_col, target_col, prediction_name='prediction'):
    try:
        with source_col.watch([{"$match": {"operationType": "insert"}}]) as stream:
            for change in stream:
                data = change['fullDocument']
                doc_id = data.pop('_id', None)
                logging.info(f"[{source_col.full_name}] Processing id {doc_id}")

                body = {
                    'independent_variables': list(data.values()),
                    'model_identifier': model
                }

                try:
                    response = requests.post(f"{server_uri}/api/predict", json=body, timeout=10)
                    response.raise_for_status()
                    result = response.json()

                    if 'error' in result:
                        error = result['error']
                        logging.error(f"API error: {error}")
                        continue

                    model_type = result.get('model_used', '').replace(model_prefixes[0], '').replace(model_prefixes[1], '')
                    value = result.get('prediction')
                    result.pop('prediction', None)

                    result[prediction_name] = value

                    if value is not None:
                        description_doc = description_col.find_one({ "type": model_type.lower(), "min": { "$lte": value }, "max": { "$gte": value } })

                        if description_doc:
                            result['description'] = description_doc.get('description', "Description not found")
                            result['color'] = description_doc.get('color', "#6c757d")
                            result['icon'] = description_doc.get('icon', "⚙️")
                        else:
                            result['description'] = "Description not found"
                            result['color'] = "#6c757d"
                            result['icon'] = "⚙️"

                    result["datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                except requests.RequestException as api_err:
                    logging.error(f"API error: {api_err}")
                    continue
                except Exception as e:
                    logging.error(f"Unexpected error during API call: {e}")
                    continue

                enriched_data = {**data, **result}

                try:
                    target_col.insert_one(enriched_data)
                    print(enriched_data)
                    logging.info(f"[{target_col.full_name}] New document inserted with prediction: {enriched_data.get('prediction')}")

                    # Publish SNS alert for critical predictions (red = failure)
                    if enriched_data.get('color') == '#dc3545':
                        publish_alert(
                            f"Critical Alert: {enriched_data.get('description', 'Unknown')}",
                            f"Critical prediction detected!\n\n"
                            f"Model: {enriched_data.get('model_used', 'N/A')}\n"
                            f"Prediction: {enriched_data.get('prediction', 'N/A')}\n"
                            f"Description: {enriched_data.get('description', 'N/A')}\n"
                            f"Timestamp: {enriched_data.get('datetime', 'N/A')}\n"
                            f"Collection: {target_col.full_name}"
                        )
                except Exception as db_err:
                    logging.error(f"MongoDB error: {db_err}")

    except Exception as stream_err:
        logging.error(f"Error in change stream: {stream_err}")

if __name__ == "__main__":
    mongo_uri = streaming_config.MONGO_CONN
    if not mongo_uri:
        logging.error("MONGODB_CONNECTION_STRING not set in environment variable or config.yaml")
        exit(1)

    server_uri = "http://" + streaming_config.HOST + ":" + str(streaming_config.PORT)
    INPUT_DB_NAME = streaming_config.INPUT_DB
    OUTPUT_DB_NAME = streaming_config.OUTPUT_DB
    INFO_COLLECTION = streaming_config.INFO_COL
    CHUNKS_COLLECTION = streaming_config.CHUNKS_COL

    try:
        with MongoClient(mongo_uri, server_api=ServerApi('1'), tlsCAFile=certifi.where()) as client:
            ping(client)
            input_db = client[INPUT_DB_NAME]
            output_db = client[OUTPUT_DB_NAME]
            description_col = input_db[INFO_COLLECTION]

            # Wait for collections to appear (simulation or indexing may not have run yet)
            MAX_RETRIES = 20
            RETRY_INTERVAL = 30  # seconds
            source_collections = []

            for attempt in range(1, MAX_RETRIES + 1):
                source_collections = [
                    c for c in input_db.list_collection_names()
                    if c not in (INFO_COLLECTION, CHUNKS_COLLECTION)
                ]
                if source_collections:
                    break
                logging.warning(
                    f"No source collections found in '{INPUT_DB_NAME}' "
                    f"(attempt {attempt}/{MAX_RETRIES}). Retrying in {RETRY_INTERVAL}s..."
                )
                time.sleep(RETRY_INTERVAL)

            if not source_collections:
                logging.error(
                    f"No source collections found in '{INPUT_DB_NAME}' after "
                    f"{MAX_RETRIES * RETRY_INTERVAL}s. Exiting."
                )
                exit(1)

            threads = []
            for source_name in source_collections:
                model = get_model_name(source_name)

                # Model not found
                if model is None:
                    logging.warning(f"Model not found for {source_name}. Ignoring this collection.")
                    continue

                source_collection = input_db[source_name]
                target_collection = output_db[source_name]

                t = threading.Thread(
                    target=stream_prediction,
                    args=(server_uri, model, source_collection, description_col, target_collection),
                    daemon=True
                )
                t.start()
                threads.append(t)

            # Keep the main thread alive while worker threads run
            for t in threads:
                t.join()

    except Exception as e:
        logging.error(f"Fatal error: {e}")
