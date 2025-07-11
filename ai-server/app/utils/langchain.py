# langchain imports
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings

#1. 벡터 DB 로드
def load_vector_db_disease():
    #embedding_model = HuggingFaceEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
    embedding_model = HuggingFaceEmbeddings(model_name="jhgan/ko-sbert-nli")
    vectordb_disease = FAISS.load_local("vector_store/diet", embedding_model, allow_dangerous_deserialization=True)
    
    return vectordb_disease

def load_vector_db_recipe():
    # 1. 임베딩 모델 로드
    model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS", device="cuda")

    # 2. 저장된 벡터 DB 로드 (embedding_function 없이 직접 임베딩 방식)
    vectordb_recipe = FAISS.load_local(
        "vector_store/recipe",
        embeddings=None,
        allow_dangerous_deserialization=True
    )

    return model, vectordb_recipe
    