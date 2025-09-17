"""
Firebase utility functions for Firestore operations
"""
import firebase_admin
from firebase_admin import credentials, firestore
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase app
_firebase_app = None
_firestore_client = None

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global _firebase_app, _firestore_client
    
    if _firebase_app is None:
        try:
            # Check if credentials file exists
            if os.path.exists(settings.FIREBASE_ADMIN_SDK_PATH):
                cred = credentials.Certificate(settings.FIREBASE_ADMIN_SDK_PATH)
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
            return document_id
        else:
            doc_ref = db.collection(collection_name).add(document_data)
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
            
        return result
    except Exception as e:
        logger.error(f"Error getting documents from {collection_name}: {e}")
        return []

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
        docs = get_all_documents(collection_name)
        return len(docs)
    except Exception as e:
        logger.error(f"Error counting documents in {collection_name}: {e}")
        return 0