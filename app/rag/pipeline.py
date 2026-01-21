import psycopg2

from pymilvus import connections, Collection

from utils import load_secret_yaml
from rag.model import Law


def get_law_data():
    psql_secret = load_secret_yaml()["postgresql"]
    conn = psycopg2.connect(host=psql_secret['host'],
                            port=psql_secret['port'],
                            dbname=psql_secret['database'],
                            user=psql_secret['username'],
                            password=psql_secret['password'])

    sql = fr"""
        SELECT *
          FROM laws
         WHERE law_cntn !~ '\s*삭제\s*<\d{4}\.\d{2}\.\d{2}>'
           AND jo_type <> '전문'   
        """
    cur = conn.cursor()
    cur.execute(sql)
    data = []
    for row in cur:
        data.append(Law(
            law_id=row[0],
            law_name=row[1],
            jo_title=row[2],
            jo_num=row[3],
            jo_branch_num=row[4],
            haang_num=row[5],
            ho_num=row[6],
            mok_num=row[7],
            public_date=row[8],
            law_cntn=row[9],
            ministry=row[10],
            link=row[11],
            jo_type=row[12],
        ))
    cur.close()
    conn.close()
    return data


def data_insert(data, batch_size=100):
    for i in range(0, len(data), batch_size):
        collection.upsert(data[i:i + batch_size])
    collection.flush()
    collection.load()


if __name__ == '__main__':
    secret = load_secret_yaml()
    milvus_secret = secret["milvus"]

    connections.connect("default", host=milvus_secret.get("host"), port=milvus_secret.get("port"))
    collection = Collection(name="law_hybrid_rag")

    laws = get_law_data()
    data_insert([row.to_dict(exclude=['jo_type']) for row in laws])