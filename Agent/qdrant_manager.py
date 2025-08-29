from langchain_qdrant import QdrantVectorStore, RetrievalMode
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, ScoredPoint
from typing import List
from langchain_core.documents import Document
from dotenv import load_dotenv
from tqdm import tqdm
from uuid import uuid4
import os
import logging
# from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = os.getenv("QDRANT_PORT", 6333)
DOCS_COLLECTION_NAME = os.getenv("DOCS_COLLECTION_NAME", "food_docs")
FOOD_COLLECTION_NAME = os.getenv("FOOD_COLLECTION_NAME", "food_name")
TAG_COLLECTION_NAME = os.getenv("TAG_COLLECTION_NAME", "food_tag")
logging_level = os.getenv("LOGGING_LEVEL", "INFO").upper()

logging.basicConfig(level={
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}[logging_level])
logger = logging.getLogger(__name__)

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.CRITICAL)

logger.info("loading embeddings")
ko_embeddings = HuggingFaceEmbeddings(model_name="Snowflake/snowflake-arctic-embed-l-v2.0")
dimension = len(ko_embeddings.embed_query("test"))
logger.info("loaded embeddings")

class Collections(BaseModel):
    food_docs_collection: str = DOCS_COLLECTION_NAME
    food_name_collection: str = FOOD_COLLECTION_NAME
    food_tag_collection: str = TAG_COLLECTION_NAME

collections = Collections()

class QdrantManager:
    def __init__(
            self, 
            host: str = QDRANT_HOST, 
            port: int = QDRANT_PORT, 
            collection_names: Collections = collections, 
            embedding_model: Embeddings = ko_embeddings,
            dim: int = dimension
        ):
        logger.info(f"initializing qdrant manager with host: {host}, port: {port}")
        self.client = QdrantClient(url=f"http://{host}:{port}")
        self.collection_names = collection_names
        self.embedding_model = embedding_model
        self.dim = dim
        for collection_name in self.collection_names.model_dump().values():
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.dim,
                        distance=Distance.COSINE
                    ),
                )
                logger.info(f"created collection: {collection_name}")

    def get_retriever(self, collection_name: str):
        return QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embedding_model,
            retrieval_mode=RetrievalMode.DENSE,
        ).as_retriever()

    def add_documents(self, documents: List[Document], collection_name: str, batch_size: int = 100):
        
        texts = list(map(lambda x: x.page_content, documents))
        metadatas = list(map(lambda x: x.metadata, documents))
        # ids = list(map(lambda x: str(uuid4()), documents))
        for i in tqdm(range(0, len(texts), batch_size), desc=f"Adding documents to qdrant {collection_name}"):
            if i + batch_size >= len(texts):
                last = -1
            else:
                last = i + batch_size
            embeddings = self.embedding_model.embed_documents(texts[i:last])
            self.client.upsert(
                collection_name=collection_name,
                wait=True,
                points=[
                    PointStruct(
                        vector=embedding,
                        payload={"page_content": text, "metadata": metadata},
                        id=str(uuid4())
                    )
                    for embedding, text, metadata in zip(embeddings, texts[i:last], metadatas[i:last])
                ]
            )

    def get_documents(self, query: str, collection_name: str) -> List[ScoredPoint]:
        return self.client.query_points(
            collection_name=collection_name,
            query=self.embedding_model.embed_query(query),
            limit=10
        ).points


qdrant_manager = QdrantManager()

