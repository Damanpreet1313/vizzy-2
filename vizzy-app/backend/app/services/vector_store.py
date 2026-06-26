import os

# pymilvus 3.x reads MILVUS_URI from the environment at module import time.
# Remove it before importing so the module-level singleton doesn't reject
# a local file path. MilvusClient receives the path directly instead.
os.environ.pop("MILVUS_URI", None)

from pymilvus import MilvusClient  # noqa: E402
from langchain_community.embeddings import HuggingFaceEmbeddings  # noqa: E402

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MILVUS_LOCAL_PATH = "./data/milvus_vizzy.db"
VECTOR_DIM = 384  # all-MiniLM-L6-v2 output dimension


def _get_client() -> MilvusClient:
    """Return a MilvusClient connected to the local Milvus Lite database."""
    return MilvusClient(uri=MILVUS_LOCAL_PATH)


def _ensure_collection(client: MilvusClient, collection_name: str) -> None:
    """Create the collection if it doesn't already exist."""
    if client.has_collection(collection_name):
        return
    # pymilvus 3.x / milvus-lite 3.x simplified API:
    # pass dimension directly — no manual FieldSchema required.
    client.create_collection(
        collection_name=collection_name,
        dimension=VECTOR_DIM,
        metric_type="L2",
        auto_id=True,
    )


class _VectorStoreWrapper:
    def __init__(self, client: MilvusClient, collection_name: str, embeddings: HuggingFaceEmbeddings):
        self.client = client
        self.collection_name = collection_name
        self.embeddings = embeddings

    def add_texts(self, texts: list[str]) -> None:
        vectors = self.embeddings.embed_documents(texts)
        data = [
            {"vector": vectors[i], "text": texts[i]}
            for i in range(len(texts))
        ]
        self.client.insert(collection_name=self.collection_name, data=data)
        # Keep collection loaded so it's immediately searchable
        self.client.load_collection(self.collection_name)

    def similarity_search(self, query: str, k: int = 4):
        query_vec = self.embeddings.embed_query(query)
        # pymilvus 3.x requires the collection to be loaded before searching
        self.client.load_collection(self.collection_name)
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vec],
            limit=k,
            output_fields=["text"],
        )

        class SimpleDoc:
            def __init__(self, content: str):
                self.page_content = content

        docs = []
        for hits in results:
            for hit in hits:
                content = hit.get("entity", {}).get("text", "")
                docs.append(SimpleDoc(content))
        return docs


def get_vector_store(collection_name: str = "vizzy_book_chunks") -> _VectorStoreWrapper:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    client = _get_client()
    _ensure_collection(client, collection_name)
    return _VectorStoreWrapper(client, collection_name, embeddings)
