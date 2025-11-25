from pymongo import MongoClient


class MongoDBManager:
    """
    Handles saving processed data to MongoDB.
    """

    def __init__(self):
        self.mongo_uri = "mongodb://mongoadmin:Hackathon2025@mongo:27017/"
        self.db_name = "data_quality_service"
        self.collection_name = "records"

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def save(self, data: dict):
        self.collection.insert_one(data)
