# database/__init__.py

from database.mongo_impl import MongoDB

db = MongoDB()  # Default to MongoDB. You can switch this easily.
