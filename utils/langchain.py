# langchain imports
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# 1. 벡터 DB 로드
def load_vector_db():
    embedding_model = HuggingFaceEmbeddings(model_name="jhgan/ko-sbert-nli")
    vectordb = FAISS.load_local("vector_store/diet", embedding_model, allow_dangerous_deserialization=True)
    
    return vectordb

