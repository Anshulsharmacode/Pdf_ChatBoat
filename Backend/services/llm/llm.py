from datetime import datetime
import requests
from litellm import completion
import os
import json
import numpy as np
from conf.db import pdf_collection, message_collection
from constant.extra import extract_text_from_pdf
from google import genai


def get_embedding(text: str, model: str = "nomic-embed-text"):
    """Get embedding vector from Ollama"""
    try:
        url = "http://localhost:11434/api/embeddings"
        response = requests.post(url, json={"model": model, "prompt": text}, timeout=30)
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"Error getting embedding: {e}")
        raise


def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def injestPdf(user_id ):
    """Process PDF: extract text, create embeddings, and generate QA pairs"""
    print(f"Processing PDF for user: {user_id}")
    
    pdf = pdf_collection.find_one({"user_id": user_id})
    if not pdf:
        return {"error": "PDF not found"}
    
    pdf_id = pdf["_id"]
    file_path = pdf.get('filePath')
    
    if not file_path:
        return {"error": "File path not found in PDF record"}
    
    # Extract text from PDF
    try:
        text = extract_text_from_pdf(file_path)
        if not text or len(text.strip()) < 50:
            return {"error": "PDF text extraction failed or insufficient content"}
    except Exception as e:
        print(f"Error extracting text: {e}")
        return {"error": f"Failed to extract text: {str(e)}"}
    
    print(f"Extracted {len(text)} characters from PDF")
    
    # Create chunks with overlap
    chunk_size = 800
    overlap = 100
    chunks = []
    
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size].strip()
        if len(chunk) > 50:  # Only add substantial chunks
            chunks.append(chunk)
    
    print(f"Created {len(chunks)} chunks")
    
    if not chunks:
        return {"error": "No valid chunks created from PDF"}
    
    # Generate embeddings for chunks
    embedding_data = []
    for idx, chunk in enumerate(chunks):
        try:
            vector = get_embedding(chunk)
            embedding_data.append({
                "index": idx,
                "chunk": chunk,
                "vector": vector
            })
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{len(chunks)} chunks")
        except Exception as e:
            print(f"Error embedding chunk {idx}: {e}")
            continue
    
    if not embedding_data:
        return {"error": "Failed to create embeddings"}
    
    print(f"Created {len(embedding_data)} embeddings")
    
    # Generate QA pairs using Gemini
    max_chunks_for_qa = 20
    sample_chunks = chunks[:max_chunks_for_qa] if len(chunks) > max_chunks_for_qa else chunks
    
    qa_prompt = f"""Based on the following document content, generate relevant Question-Answer pairs.

Document content:
{' '.join(sample_chunks)}

Generate comprehensive Q&A pairs covering:
- Main topics and concepts
- Important facts and details
- Definitions and explanations
- Key relationships and connections

Return ONLY a valid JSON array with this exact format:
[
    {{"question": "What is...", "answer": "..."}},
    {{"question": "How does...", "answer": "..."}}
]

Generate 20-30 Q&A pairs. Make questions specific and answers detailed based strictly on the document content."""
    
    qa_pairs = []
    qa_embeddings = []
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=qa_prompt,
        )
        
        # Parse QA pairs
        qa_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if qa_text.startswith("```json"):
            qa_text = qa_text.replace("```json", "").replace("```", "").strip()
        elif qa_text.startswith("```"):
            qa_text = qa_text.replace("```", "").strip()
        
        qa_pairs = json.loads(qa_text)
        print(f"Generated {len(qa_pairs)} QA pairs")
        
        # Create embeddings for QA pairs
        for idx, qa in enumerate(qa_pairs):
            try:
                # Combine question and answer for better semantic search
                combined_text = f"Q: {qa['question']} A: {qa['answer']}"
                qa_vector = get_embedding(combined_text)
                qa_embeddings.append({
                    "index": idx,
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "vector": qa_vector
                })
            except Exception as e:
                print(f"Error embedding QA pair {idx}: {e}")
                continue
        
        print(f"Created {len(qa_embeddings)} QA embeddings")
        
    except Exception as e:
        print(f"Error generating QA pairs: {e}")
        # Continue without QA pairs if generation fails
    
    # Update database with embeddings and QA pairs
    try:
        pdf_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "embeddings": embedding_data,
                    "qa_pairs": qa_pairs,
                    "qa_embeddings": qa_embeddings,
                    "processed_at": datetime.utcnow(),
                    "text_length": len(text),
                    "chunk_count": len(chunks)
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"Error updating database: {e}")
        return {"error": f"Failed to save to database: {str(e)}"}
    
    return {
        "status": "success",
        "chunks_created": len(chunks),
        "embeddings_created": len(embedding_data),
        "qa_pairs_created": len(qa_pairs),
        "qa_embeddings_created": len(qa_embeddings)
    }


def retrieve_relevant_content(user_id, user_question, top_k=3):
    """
    Retrieve relevant content using hybrid approach:
    1. Search QA pairs first (faster, pre-generated)
    2. Fall back to chunk search if needed
    """
    try:
        query_vector = get_embedding(user_question)
    except Exception as e:
        print(f"Error getting query embedding: {e}")
        return {"qa_matches": [], "chunk_matches": [], "error": "Failed to process question"}
    
    pdf = pdf_collection.find_one({"user_id": user_id})
    if not pdf:
        return {"qa_matches": [], "chunk_matches": [], "error": "PDF not found"}
    
    qa_matches = []
    chunk_matches = []
    
    # Search in QA embeddings first
    if "qa_embeddings" in pdf and pdf["qa_embeddings"]:
        qa_similarities = []
        for qa_emb in pdf["qa_embeddings"]:
            try:
                score = cosine_similarity(query_vector, qa_emb["vector"])
                qa_similarities.append({
                    "score": float(score),
                    "question": qa_emb["question"],
                    "answer": qa_emb["answer"]
                })
            except Exception as e:
                print(f"Error calculating QA similarity: {e}")
                continue
        
        # Sort and get top matches
        qa_similarities.sort(reverse=True, key=lambda x: x["score"])
        qa_matches = qa_similarities[:top_k]
        print(f"Found {len(qa_matches)} QA matches")
    else:
        print("No QA embeddings found")
    
    # Search in chunk embeddings
    if "embeddings" in pdf and pdf["embeddings"]:
        chunk_similarities = []
        for emb in pdf["embeddings"]:
            try:
                score = cosine_similarity(query_vector, emb["vector"])
                chunk_similarities.append({
                    "score": float(score),
                    "chunk": emb["chunk"]
                })
            except Exception as e:
                print(f"Error calculating chunk similarity: {e}")
                continue
        
        # Sort and get top matches
        chunk_similarities.sort(reverse=True, key=lambda x: x["score"])
        chunk_matches = chunk_similarities[:top_k]
        print(f"Found {len(chunk_matches)} chunk matches")
    else:
        print("No chunk embeddings found")
    
    return {
        "qa_matches": qa_matches,
        "chunk_matches": chunk_matches
    }


def takeLLMresponse(user_id, user_question):
    """Generate answer using retrieved context"""
    if not user_id:
        return {"Error": "User not found"}
    
    if not user_question or len(user_question.strip()) < 3:
        return {"Error": "Question is too short or empty"}
    
    pdf = pdf_collection.find_one({"user_id": user_id})
    if not pdf:
        return {"Error": "PDF not found. Please upload a PDF first."}
    
    # Check if PDF has been processed
    if "embeddings" not in pdf or not pdf["embeddings"]:
        return {"Error": "PDF has not been processed yet. Please wait for processing to complete."}
    
    pdf_id = pdf["_id"]
    
    # Retrieve relevant content
    retrieved = retrieve_relevant_content(user_id, user_question, top_k=3)
    
    if "error" in retrieved:
        return {"Error": retrieved["error"]}
    
    # Build context from retrieved information
    context_parts = []
    has_relevant_content = False
    
    # Add QA matches (prioritize these as they're pre-generated answers)
    if retrieved["qa_matches"]:
        relevant_qa = [qa for qa in retrieved["qa_matches"][:3] if qa["score"] > 0.5]
        if relevant_qa:
            has_relevant_content = True
            context_parts.append("Previously answered questions from the document:")
            for idx, qa in enumerate(relevant_qa, 1):
                context_parts.append(f"\n{idx}. Q: {qa['question']}")
                context_parts.append(f"   A: {qa['answer']}")
                context_parts.append(f"   (Relevance: {qa['score']:.2f})")
    
    # Add chunk matches for additional context
    if retrieved["chunk_matches"]:
        relevant_chunks = [chunk for chunk in retrieved["chunk_matches"][:3] if chunk["score"] > 0.3]
        if relevant_chunks:
            has_relevant_content = True
            context_parts.append("\n\nRelevant sections from the document:")
            for idx, chunk in enumerate(relevant_chunks, 1):
                # Use more of the chunk text for better context
                chunk_text = chunk['chunk'][:500]
                context_parts.append(f"\n{idx}. {chunk_text}...")
                context_parts.append(f"   (Relevance: {chunk['score']:.2f})")
    
    # Debug: Print context to see what's being used
    context = "\n".join(context_parts)
    print(f"\n=== CONTEXT BEING SENT ===")
    print(f"Has relevant content: {has_relevant_content}")
    print(f"Context length: {len(context)}")
    print(f"Context preview:\n{context[:500]}...")
    print(f"=== END CONTEXT ===\n")
    
    if not has_relevant_content:
        context = "No highly relevant content found in the document for this question."
    
    # Build prompt
    final_prompt = f"""You are a helpful assistant answering questions about a document.

Context from the document:
{context}

User question: {user_question}

Instructions:
- Provide a clear, concise answer based ONLY on the context above
- If the context contains relevant information, synthesize it into a helpful answer
- If the context doesn't contain enough information, clearly state that and suggest what information might be needed
- Use natural language and be conversational
- Keep your answer focused and avoid unnecessary details

Answer:"""
    
    # Get response from Gemini
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=final_prompt,
        )
        answer = response.text.strip()
        
        if not answer:
            answer = "I apologize, but I couldn't generate a response. Please try again."
            
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        answer = "Sorry, I encountered an error generating a response. Please try again."
    
    # Save to message history
    try:
        message_collection.insert_one({
            "user_id": user_id,
            "pdf_id": pdf_id,
            "question": user_question,
            "answer": answer,
            "context_used": context[:1000],  # Store first 1000 chars of context
            "qa_matches_count": len(retrieved.get("qa_matches", [])),
            "chunk_matches_count": len(retrieved.get("chunk_matches", [])),
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        print(f"Error saving to message history: {e}")
    
    return answer