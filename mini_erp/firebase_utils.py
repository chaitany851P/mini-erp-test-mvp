"""
Firebase utility functions for Firestore operations
"""
import firebase_admin
from firebase_admin import credentials, firestore
from django.conf import settings
import os
import logging
import time
import threading

logger = logging.getLogger(__name__)

# Initialize Firebase app
_firebase_app = None
_firestore_client = None

# Simple in-process cache for collection reads
_collection_cache = {}
_cache_lock = threading.Lock()

# Optional background snapshot listeners (best-effort)
_watchers_started = set()


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global _firebase_app, _firestore_client
    
    if _firebase_app is None:
        try:
            # Check if credentials file exists
            cred_path = str(settings.FIREBASE_ADMIN_SDK_PATH)
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                _firebase_app = firebase_admin.initialize_app(cred)
            else:
                # For development/testing without actual Firebase credentials
                logger.warning("Firebase credentials file not found. Using default credentials.")
                _firebase_app = firebase_admin.initialize_app()
            
            _firestore_client = firestore.client()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            _firestore_client = None
    
    return _firestore_client


def get_firestore_client():
    """Get Firestore client instance"""
    if _firestore_client is None:
        return initialize_firebase()
    return _firestore_client


def _update_cache(collection_name: str, data: list):
    with _cache_lock:
        _collection_cache[collection_name] = {
            'data': data,
            'ts': time.time(),
        }


def get_all_documents(collection_name):
    """
    Get all documents from a Firestore collection
    
    Args:
        collection_name (str): Name of the collection
    
    Returns:
        list: List of dictionaries containing document data with id field
    """
    try:
        db = get_firestore_client()
        if db is None:
            return []
            
        docs = db.collection(collection_name).stream()
        result = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            result.append(doc_data)
        
        # keep cache updated for bare reads as well
        _update_cache(collection_name, result)
        return result
    except Exception as e:
        logger.error(f"Error getting documents from {collection_name}: {e}")
        return []


def get_all_documents_cached(collection_name: str, ttl_seconds: int = 15) -> list:
    """Return collection documents using an in-process cache to reduce Firestore reads.
    If the cache is older than ttl_seconds, fetch from Firestore and refresh the cache.
    """
    now = time.time()
    with _cache_lock:
        entry = _collection_cache.get(collection_name)
        if entry and (now - entry.get('ts', 0) <= ttl_seconds):
            return entry.get('data', [])
    # stale or missing -> fetch fresh
    fresh = get_all_documents(collection_name)
    return fresh


def start_snapshot_watch(collection_name: str):
    """Start a background on_snapshot listener to keep cache hot. Best-effort.
    Safe to call multiple times; starts only once per collection.
    """
    if collection_name in _watchers_started:
        return
    db = get_firestore_client()
    if db is None:
        return
    try:
        col_ref = db.collection(collection_name)
        def on_snapshot(col_snapshot, changes, read_time):
            try:
                result = []
                for doc in col_snapshot:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    result.append(data)
                _update_cache(collection_name, result)
            except Exception as e:
                logger.error(f"Snapshot update failed for {collection_name}: {e}")
        # Start listener in background thread managed by SDK
        col_ref.on_snapshot(on_snapshot)
        _watchers_started.add(collection_name)
        logger.info(f"Started snapshot watch for collection: {collection_name}")
    except Exception as e:
        # If snapshot fails (e.g., emulator or permissions), we silently ignore
        logger.warning(f"Could not start snapshot watch for {collection_name}: {e}")


def add_document(collection_name, document_data, document_id=None):
    """
    Add a document to a Firestore collection
    
    Args:
        collection_name (str): Name of the collection
        document_data (dict): Data to store in the document
        document_id (str, optional): Document ID. If None, Firestore will generate one
    
    Returns:
        str: Document ID if successful, None otherwise
    """
    try:
        db = get_firestore_client()
        if db is None:
            return None
            
        if document_id:
            doc_ref = db.collection(collection_name).document(document_id)
            doc_ref.set(document_data)
            # refresh cache opportunistically
            start_snapshot_watch(collection_name)
            return document_id
        else:
            doc_ref = db.collection(collection_name).add(document_data)
            start_snapshot_watch(collection_name)
            return doc_ref[1].id
    except Exception as e:
        logger.error(f"Error adding document to {collection_name}: {e}")
        return None


def get_document(collection_name, document_id):
    """
    Get a document from Firestore
    
    Args:
        collection_name (str): Name of the collection
        document_id (str): Document ID
    
    Returns:
        dict: Document data if found, None otherwise
    """
    try:
        db = get_firestore_client()
        if db is None:
            return None
            
        doc_ref = db.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting document from {collection_name}: {e}")
        return None


def update_document(collection_name, document_id, update_data):
    """
    Update a document in Firestore
    
    Args:
        collection_name (str): Name of the collection
        document_id (str): Document ID
        update_data (dict): Data to update
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        if db is None:
            return False
            
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.update(update_data)
        start_snapshot_watch(collection_name)
        return True
    except Exception as e:
        logger.error(f"Error updating document in {collection_name}: {e}")
        return False


def delete_document(collection_name, document_id):
    """
    Delete a document from Firestore
    
    Args:
        collection_name (str): Name of the collection
        document_id (str): Document ID
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        if db is None:
            return False
            
        db.collection(collection_name).document(document_id).delete()
        start_snapshot_watch(collection_name)
        return True
    except Exception as e:
        logger.error(f"Error deleting document from {collection_name}: {e}")
        return False


def query_collection(collection_name, field, operator, value):
    """
    Query a collection with a simple filter
    
    Args:
        collection_name (str): Name of the collection
        field (str): Field to filter by
        operator (str): Comparison operator ('==', '>', '<', '>=', '<=', '!=', 'in', 'not-in')
        value: Value to compare against
    
    Returns:
        list: List of matching documents with id field
    """
    try:
        db = get_firestore_client()
        if db is None:
            return []
            
        docs = db.collection(collection_name).where(field, operator, value).stream()
        result = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            result.append(doc_data)
            
        return result
    except Exception as e:
        logger.error(f"Error querying collection {collection_name}: {e}")
        return []


def get_collection_count(collection_name):
    """
    Get the count of documents in a collection
    
    Args:
        collection_name (str): Name of the collection
    
    Returns:
        int: Number of documents in the collection
    """
    try:
        # Prefer cached to avoid scanning every time
        docs = get_all_documents_cached(collection_name, ttl_seconds=15)
        return len(docs)
    except Exception as e:
        logger.error(f"Error counting documents in {collection_name}: {e}")
        return 0
