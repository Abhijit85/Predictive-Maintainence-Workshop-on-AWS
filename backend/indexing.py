import logging
import os
import sys
from pathlib import Path
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.operations import SearchIndexModel
import certifi

sys.path.append(str(Path(__file__).parent))

from data_processing.DocumentChunker import DocumentChunker
from utils.llm_utils import generate_embeddings
from config.config_loader import DataProcessingConfig

if __name__ == "__main__":
    # Create our own config instance to avoid logging conflicts
    data_processing_config = DataProcessingConfig()
    data_processing_config.log_configuration()
    mongo_uri = data_processing_config.MONGO_CONN
    if not mongo_uri:
        logging.error("MONGODB_CONNECTION_STRING not set in environment variable or config.yaml")
        exit(1)

    client = MongoClient(mongo_uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

    # Folder and info file paths
    folder = data_processing_config.DATA_PROCESSING_FOLDER
    info_file = data_processing_config.INFO_PATH

    # MongoDB configurations
    INPUT_DB_NAME = data_processing_config.INPUT_DB
    CHUNKS_COL_NAME = data_processing_config.CHUNKS_COL
    INFO_COL_NAME = data_processing_config.INFO_COL

    # Embedding configurations
    embedding_model = data_processing_config.EMBEDDING_MODEL
    chunk_size = data_processing_config.CHUNK_SIZE
    overlap_size = data_processing_config.OVERLAP_SIZE
    
    if not os.path.exists(folder):
        logging.error(f"Folder {folder} does not exist")
        exit(1)
    
    chunker = DocumentChunker(chunk_size=chunk_size, overlap_size=overlap_size)

    files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

    if not files:
        logging.warning(f"No files found in {folder}")
        exit(1)

    logging.info(f"Processing {len(files)} files from {folder}")
    chunks = chunker.process_multiple_files(files, "paragraph")

    docs = []
    for file_path, result in chunks.items():
        if result["error"]:
            logging.error(f"Error processing {file_path}: {result['error']}")
            continue
            
        for i, chunk in enumerate(result["chunks"]):
            try:
                embeddings = generate_embeddings(embedding_model, chunk)
                EMBEDDING_DIMENSIONS = len(embeddings)
                
                doc = {
                    "file": file_path,
                    "chunk": chunk,
                    "embeddings": embeddings
                }
                
                docs.append(doc)
                logging.info(f"Generated embeddings for chunk {i+1}/{len(result['chunks'])} for file '{file_path}'")
                
            except Exception as e:
                logging.error(f"Error generating embeddings for chunk {i+1} in {file_path}: {e}")
                continue
            
    if not docs:
        logging.error("No documents processed successfully")
        exit(1)
        
    try:
        input_db = client[INPUT_DB_NAME]

        if CHUNKS_COL_NAME not in input_db.list_collection_names():
            input_db.create_collection(CHUNKS_COL_NAME)

        if INFO_COL_NAME not in input_db.list_collection_names():
            input_db.create_collection(INFO_COL_NAME)

        chunks_col = input_db[CHUNKS_COL_NAME]
        info_col = input_db[INFO_COL_NAME]

        try:
            df = pd.read_csv(info_file)
            info_records = df.to_dict(orient="records")

            if info_records:
                # Upsert each record so re-running indexing doesn't crash with
                # duplicate key errors. Records are matched by _id (if present)
                # or by (type, min, max) as a natural key.
                inserted = 0
                skipped = 0
                for record in info_records:
                    filter_key = {"_id": record["_id"]} if "_id" in record else {
                        "type": record.get("type"),
                        "min": record.get("min"),
                        "max": record.get("max"),
                    }
                    result = info_col.update_one(filter_key, {"$set": record}, upsert=True)
                    if result.upserted_id:
                        inserted += 1
                    else:
                        skipped += 1
                logging.info(
                    f"Info collection synced from {info_file}: "
                    f"{inserted} inserted, {skipped} already existed"
                )

        except Exception as err:
            logging.error(f"Error adding the information documents: {err}")

        search_index_model = SearchIndexModel(
            definition = {
                "fields": [
                    {
                        "type": "vector",
                        "numDimensions": EMBEDDING_DIMENSIONS,
                        "path": "embeddings",
                        "similarity":  "cosine"
                    }
                ]
            },
            name="embeddings",
            type="vectorSearch",
        )

        existing_indexes = [index["name"] for index in chunks_col.list_search_indexes()]

        if "embeddings" not in existing_indexes:
            chunks_col.create_search_index(model=search_index_model)
            logging.info("Created search index for embeddings")

        # Create full-text search index for hybrid search
        if "text_search" not in existing_indexes:
            text_search_index = SearchIndexModel(
                definition={
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "chunk": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            }
                        }
                    }
                },
                name="text_search",
                type="search",
            )
            chunks_col.create_search_index(model=text_search_index)
            logging.info("Created full-text search index 'text_search' on chunk field")

        # Clear existing chunks before re-indexing to prevent duplicates.
        # Search indexes (embeddings, text_search) are preserved — they are
        # defined on the collection, not tied to individual documents.
        existing_count = chunks_col.count_documents({})
        if existing_count > 0:
            chunks_col.delete_many({})
            logging.info(f"Cleared {existing_count} existing chunks from {chunks_col.full_name}")

        doc_batches = [docs[x:x+100] for x in range(0, len(docs), 100)]
        for i, batch in enumerate(doc_batches):
            chunks_col.insert_many(batch)
            logging.info(f"Successfully saved batch {i+1}/{len(doc_batches)} into {chunks_col.full_name}")

        logging.info(f"Successfully processed {len(docs)} chunks from {len(chunks)} files")

    except Exception as db_err:
        logging.error(f"MongoDB error: {db_err}")
        exit(1)