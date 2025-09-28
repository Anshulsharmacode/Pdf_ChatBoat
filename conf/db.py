from pymongo import MongoClient
from conf.confilg import Mongo_DB

client = MongoClient(Mongo_DB)
db= client['chat_pdf']


user_collection = db['users']
pdf_collection = db ['pdfs']
message_collection = db['messages']
