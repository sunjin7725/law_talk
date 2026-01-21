from langchain_core.tools import tool
from pymilvus import AnnSearchRequest, RRFRanker, Collection, connections
from rag.rag_utils import embed_text
from utils import load_secret_yaml

from langchain_core.documents import Document


secret = load_secret_yaml()
milvus_secret = secret["milvus"]
connections.connect("default", host=milvus_secret.get("host"), port=milvus_secret.get("port"))
collection = Collection(name='law_hybrid_rag')


def format_result(results):
    docs = []
    for hit in results[0]:
        meta = {
            "법령명": hit.entity.get("law_name"),
            "조번호": hit.entity.get("jo_num"),
            "조가지번호": hit.entity.get("jo_branch_num"),
            "항번호": hit.entity.get("haang_num"),
            "호번호": hit.entity.get("ho_num"),
            "목번호": hit.entity.get("mok_num"),
            "시행일자": hit.entity.get("public_date"),
            "시행부처명": hit.entity.get("ministry"),
            "상세링크": hit.entity.get("link"),
            # "score": hit.score
        }

        docs.append(
            Document(
                page_content=hit.entity.get("law_cntn"),
                metadata=meta
            )
        )
    return docs

def serialize(docs):
    return "\n".join([
        f"""
        {doc.metadata}
        {doc.page_content}
        """ for doc in docs
    ])

@tool
def filter_search(law_name: str,
                  query: str,
                  jo_num: str=None,
                  jo_branch_num: str=None,
                  haang_num: str=None,
                  ho_num: str=None,
                  mok_num: str=None) -> str:
    """
    특정 법령(law_name)이 명확하고 부가적으로 조, 항, 호, 목의 정확한 번호값이 주어졌을 때 사용하는 검색 도구.
    law_name을 고정하고 query를 통해 추가적인 검색 조건을 제공할 수 있다.
    jo_num, jo_branch_num, haang_num, ho_num, mok_num은 각각 조, 항, 호, 목의 번호를 나타낸다.
    query는 추가적인 검색 조건을 제공할 수 있는 문자열.

    :param law_name: 법령명
    :param query: 검색어
    :param jo_num: 조번호
    :param jo_branch_num: 조가지번호
    :param haang_num: 행번호
    :param ho_num: 호번호
    :param mok_num: 목번호
    :return: 문자열화된 검색 정보
    """
    expr = f'law_name == "{law_name}"'
    if jo_num: expr += f' and jo_num == "{jo_num}"'
    if jo_branch_num: expr += f' and jo_branch_num == "{jo_branch_num}"'
    if haang_num: expr += f' and haang_num == "{haang_num}"'
    if ho_num: expr += f' and ho_num == "{ho_num}"'
    if mok_num: expr += f' and mok_num == "{mok_num}"'

    results = collection.search(
        data=[embed_text(query)],
        anns_field="dense_embedding",
        expr=expr,
        param={"metric_type": "COSINE"},
        limit=30,
        output_fields=["law_cntn", "law_name", "jo_num", "jo_branch_num", "haang_num",
                       "ho_num", "mok_num", "public_date", "ministry", "link"]
    )
    docs = format_result(results)
    serialized_docs = serialize(docs)
    return serialized_docs

@tool
def query_search(query: str) -> str:
    """
    법령이 특정되지 않았을 때 사용하는 전체 법령 대상의 검색 도구.
    :param query: 검색어
    :return: 문자열화된 검색정보
    """
    query_dense = embed_text(query)
    dense_req = AnnSearchRequest(
        data=[query_dense],
        anns_field="dense_embedding",
        param={"metric_type": "COSINE"},
        limit=20
    )

    sparse_req = AnnSearchRequest(
        data=[query],  # 🔥 raw query text 그대로
        anns_field="sparse_embedding",
        param={"metric_type": "BM25"},
        limit=20
    )

    rrf = RRFRanker()
    results = collection.hybrid_search(
        reqs=[dense_req, sparse_req],
        rerank=rrf,
        limit=10,
        output_fields=["law_cntn", "law_name", "jo_num", "jo_branch_num", "haang_num",
                       "ho_num", "mok_num", "public_date", "ministry", "link"]
    )
    docs = format_result(results)
    serialized_docs = serialize(docs)
    return serialized_docs
