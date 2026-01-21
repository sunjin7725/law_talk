import yaml

from pymilvus import (
    FieldSchema, CollectionSchema, DataType,
    Collection, connections, Function, FunctionType
)

from settings import secret_path

with open(secret_path, "r") as f:
    secret = yaml.safe_load(f)
milvus_secret = secret["milvus"]

connections.connect("default", host=milvus_secret.get("host"), port=milvus_secret.get("port"))

fields = [
    FieldSchema(name="law_id", dtype=DataType.VARCHAR, max_length=400, is_primary=True),
    FieldSchema(name="law_name", dtype=DataType.VARCHAR, max_length=400),
    FieldSchema(name="jo_title", dtype=DataType.VARCHAR, max_length=400),
    FieldSchema(name="jo_num", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="jo_branch_num", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="haang_num", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="ho_num", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="mok_num", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="public_date", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(
        name="dense_embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=3072  # ⚠️ 사용하는 embedding 모델 차원
    ),
    FieldSchema(
        name="sparse_embedding",
        dtype=DataType.SPARSE_FLOAT_VECTOR
    ),
    FieldSchema(
        name="law_cntn",
        dtype=DataType.VARCHAR,
        max_length=20000,
        enable_analyzer=True
    ),
    FieldSchema(name="ministry", dtype=DataType.VARCHAR, max_length=50),
    FieldSchema(name="link", dtype=DataType.VARCHAR, max_length=200),
]

bm25_func = Function(name="bm25_fn", function_type=FunctionType.BM25,
                     input_field_names=["law_cntn"], output_field_names=["sparse_embedding"])

schema = CollectionSchema(
    fields=fields,
    description="Korean Law Hybrid RAG",
    functions=[bm25_func]

)

collection = Collection(
    name="law_hybrid_rag",
    schema=schema
)
# collection.drop()

collection.create_index(
    field_name="dense_embedding",
    index_params={
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {
            "M": 16,
            "efConstruction": 200
        }
    }
)

collection.create_index(
    field_name="sparse_embedding",
    index_params={
        "index_type": "SPARSE_INVERTED_INDEX",
        "metric_type": "BM25"
    }
)

collection.load()
