from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from config import uri_mongodb
import ssl
uri = uri_mongodb # Create a new client and connect to the server
client = MongoClient(
    uri, 
    server_api=ServerApi('1'),)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["iot_database"]
#collections = db.list_collection_names()
#print("\nDanh sách bảng (collections):")
#for collection in collections:
#    print(f" - {collection}")
    
#collection = db["mqtt_messages"]

# Lấy tất cả các documents từ collection
#documents = collection.find()

#print(f"\nDanh sách giá trị trong collection '{collection.name}':")
#for doc in documents:
#    print(doc)
    
#collection = db["env_monitor"]

# Lấy tất cả các documents từ collection
#documents = collection.find()

print(f"\nDanh sách giá trị trong collection '{collection.name}':")
for doc in documents:
    print(doc)