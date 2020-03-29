from pymongo import MongoClient

def get_connection(user='', password='', mongo_uri='mongodb://localhost:27017/'):
    client = MongoClient(mongo_uri)
    return client


