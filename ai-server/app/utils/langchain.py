# langchain imports
from langchain_community.vectorstores import FAISS
from langchain.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
import torch
from heapq import nlargest
import json
from langchain.schema import Document
from langchain.retrievers import BM25Retriever

#1. 벡터 DB 로드
def load_vector_db_disease():
    #embedding_model = HuggingFaceEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
    embedding_model = HuggingFaceEmbeddings(model_name="jhgan/ko-sbert-nli")
    vectordb_disease = FAISS.load_local("vector_store/diet", embedding_model, allow_dangerous_deserialization=True)
    
    return vectordb_disease

# BM25 리트리버 로드
def load_bm25_retriever():
    #bm25_document 로드
    with open("vector_store/recipe/bm25_documents.json", "r", encoding="utf-8") as f:
        loaded_data = json.load(f)

    # 다시 Document 리스트로 변환
    bm25_documents_loaded = [
        Document(page_content=item["page_content"], metadata=item["metadata"])
        for item in loaded_data
        ]

    bm25_retriever = BM25Retriever.from_documents(bm25_documents_loaded)
    bm25_retriever.k = 100

    return bm25_retriever


def load_faiss_vectorstore():
    embedding_model = HuggingFaceEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
    
    faiss_loaded = FAISS.load_local(
        folder_path="vector_store/recipe",  # 네가 저장한 벡터 DB 경로
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )
    return faiss_loaded
    