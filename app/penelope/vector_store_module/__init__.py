"""
# Initialization of the vector store package
"""

from .vector_store import VectorStoreManager

__all__ = ['VectorStoreManager']
__version__ = '0.1.0'
__author__ = 'David'



# Vector store manager initialization
manager = VectorStoreManager()

# Example usage of the vector store manager

# create a vector store
# new_vector_store = manager.create_vector_store(
#     name="protocols",
# )
# print("new_vector_store: ", new_vector_store)

# List vector stores
# vector_stores = manager.list_vector_stores()
# print("\nList of Vector Stores:", vector_stores)

# Update a vector store
# vector_store_id = ""
# updated_vector_store = manager.update_vector_store_name(
#     vector_store_id=vector_store_id,
#     name="protocols_updated"
# )
# print("\nUpdated Vector Store:", updated_vector_store)

