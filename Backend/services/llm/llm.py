from datetime import datetime
from fastapi import UploadFile
import requests
from litellm import completion, embedding
import os
# from Backend.services.file.fileService import upload_file
from services.file.fileService import upload_file
from conf.db import pdf_collection , message_collection
from constant.extra import extract_text_from_pdf
from google import genai
from google.genai import Client 


def get_embedding(text: str, model: str = "nomic-embed-text"):
    url = "http://localhost:11434/api/embeddings"
    response = requests.post(url, json={"model": model, "prompt": text})
    return response.json()["embedding"]



# def injestPdf(user_id):
#     print(user_id)
#     pdf = pdf_collection.find_one({"user_id":user_id})
#     pdf_id = pdf["_id"]

#     if not pdf :
#         return{"error":"pdf not found"}
    
#     file_path = pdf['filePath']
#     text = extract_text_from_pdf(file_path)

#     chunks = [text[i:i+800]for i in range(0, len(text),800)]
    
#     print("chunks",chunks)

#     embedding_data =[]
#     for idk , chunk in enumerate(chunks):
#         vector = get_embedding(chunk)
#         embedding_data.append({
#             "index":idk,
#             "chunk": chunk,
#             "vector": vector
#         })

#     print("embeding",embedding_data)

#     pdf_collection.update_one(
#         {"user_id":user_id},
#         {"$set":{"embeddings":embedding_data}},
#         upsert=True
#         )
#     return {"status":"vector done"}


def retrive_chunks(user_id, user_question, top_k=5):
    query_vector = get_embedding(user_question)

    # LOCAL vector search (no Atlas $search)
    pdf = pdf_collection.find_one({"user_id": user_id})
    if not pdf or "embeddings" not in pdf:
        return []

    import numpy as np
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    similarities = []
    for emb_doc in pdf["embeddings"]:
        score = cosine_similarity(np.array(query_vector), np.array(emb_doc["vector"]))
        similarities.append((score, emb_doc["chunk"]))

    # Sort by similarity
    similarities.sort(reverse=True, key=lambda x: x[0])
    return [chunk for _, chunk in similarities[:top_k]] 

    


def takeLLMresponse(user_id, user_question, file: UploadFile):
    if not user_id:
        return {"Error": "user not found"}

    # Upload and extract text
    pdf = upload_file(file , user_id)
    text = extract_text_from_pdf(pdf["saved path"])

    # Chunk and embed in-memory
    chunks = [text[i:i+800] for i in range(0, len(text), 800)]
    embedding_data = []
    for idx, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        embedding_data.append({
            "index": idx,
            "chunk": chunk,
            "vector": vector
        })

    # Embed the user question
    query_vector = get_embedding(user_question)

    # Find top-k similar chunks (local, in-memory)
    import numpy as np
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    similarities = []
    for emb_doc in embedding_data:
        score = cosine_similarity(np.array(query_vector), np.array(emb_doc["vector"]))
        similarities.append((score, emb_doc["chunk"]))

    similarities.sort(reverse=True, key=lambda x: x[0])
    top_chunks = [chunk for _, chunk in similarities[:5]]

    # LLM prompt construction
    qa_prompt = f"""
    Based on the following document context:

    {top_chunks}

    Generate 10 related Question-Answer pairs in JSON format.
    Each item should look like:
    {{
        "question": "...",
        "answer": "..."
    }}
    """
    os.environ["GEMINI_API_KEY"]
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=qa_prompt,
    )
    qa_pairs = response.text
    print(qa_pairs)
    final_prompt = f"""
    You are an intelligent assistant. 

    Based on the following context from the user's PDF document:

    {qa_pairs}

    The user asked: "{user_question}"

    Provide a clear and concise answer in **plain text**, structured in **short paragraphs**. 
    Keep it brief and to the point. 
    Do NOT return JSON, lists, or any other structured format. 
    """

    ollama_response = completion(
        model="ollama/gemma3:270m",
        messages=[{"role": "user", "content": final_prompt}]
    )
    answer = ollama_response.choices[0].message.content

    print(answer)

    # Optionally save only the final Q&A for history
    pdfId = pdf.get("_id", None)
    message_collection.insert_one({
        "user_id": user_id,
        "pdf_id": pdfId,
        "question": user_question,
        "answer": answer,
        "created_at": datetime.utcnow()
    })

    return answer