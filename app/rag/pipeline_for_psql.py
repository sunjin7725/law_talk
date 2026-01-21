import psycopg2

from utils import load_secret_yaml
from rag.extract_from_api import LawAPI, get_law_list

NTS_LAW_LIST = [
    '국세기본법', '국세징수법', '조세특례제한법',
    '농ㆍ축산ㆍ임ㆍ어업용 기자재 및 석유류에 대한 부가가치세 영세율 및 면세 적용 등에 관한 특례규정',
    '외국인관광객 등에 대한 부가가치세 및 개별소비세 특례규정',
    '소득세법', '법인세법', '국제조세조정에 관한 법률', '상속세 및 증여세법',
    '종합부동산세법', '부가가치세법', '개별소비세법', '주세법', '주류 면허 등에 관한 법률',
    '교통ㆍ에너지ㆍ환경세법', '인지세법', '증권거래세법', '과세자료의 제출 및 관리에 관한 법률',
    '관세법', '교육세법', '국세청과 그 소속기관 직제', '금융실명거래 및 비밀보장에 관한 법률',
    '농어촌특별세법', '부동산 실권리자명의 등기에 관한 법률', '상가건물 임대차보호법',
    '자산재평가법', '조세범 처벌법', '조세범 처벌절차법', '지방세법', '지방세기본법',
    '지방세징수법', '지방세특례제한법', '질서위반행위규제법', '취업 후 학자금 상환 특별법',
]

INSERT_TARGET_LAW = '조세특례제한법'

def get_meta(x, key):
    _data = x['metadata'].get(key, "")
    if _data:
        return x['metadata'].get(key, "")
    else: return ""


if __name__ == '__main__':
    secret = load_secret_yaml()
    psql_secret = secret["postgresql"]
    conn = psycopg2.connect(host=psql_secret['host'],
                            port=psql_secret['port'],
                            dbname=psql_secret['database'],
                            user=psql_secret['username'],
                            password=psql_secret['password'])

    api = LawAPI()

    find_law_list = []
    for i in NTS_LAW_LIST:
        result = api.law_search_list(i, num_of_rows=10)
        result_data = result.get('data')

        if isinstance(result_data['LawSearch']['law'], list):
            find_law_list += result_data['LawSearch']['law']
        elif isinstance(result_data['LawSearch']['law'], dict):
            find_law_list.append(result_data['LawSearch']['law'])

    for law in find_law_list:
        print(f"{law.get('법령명한글')} 적재 시작...")
        law_default_meta = {
            '법령명': law.get('법령명한글'),
            '공포일자': law.get('공포일자'),
            '법령구분명': law.get('법령구분명'),
            '법령상세링크': f"{api.base_url}{law.get('법령상세링크')}",
            '소관부처명': law.get('소관부처명'),
            '시행일자': law.get('시행일자'),
            '재개정구분명': law.get('재개정구분명'),
            '현행연혁코드': law.get('현행연혁코드'),
        }
        law_json = api.get_law_detail(law.get('법령ID'))
        if law_json.get('status') == 200:
            law_list = get_law_list(law_json.get('data'), law_default_meta)
            ids = [(f'{law.get('법령ID')}{law.get('법령일련번호')}'
                    f'{get_meta(x, '조문키')}'f'{get_meta(x, '항번호').zfill(3)}'
                    f'{get_meta(x, '호번호').zfill(3)}{get_meta(x, '목번호').zfill(3)}')
                   for x in law_list]
            texts = [x['text'] for x in law_list]

            data = [
                (
                    x[0],
                    get_meta(x[2], '법령명'),
                    get_meta(x[2], '조문제목'),
                    get_meta(x[2], '조문번호'),
                    get_meta(x[2], '조문가지번호'),
                    get_meta(x[2], '항번호'),
                    get_meta(x[2], '호번호'),
                    get_meta(x[2], '목번호'),
                    get_meta(x[2], '시행일자'),
                    x[1],
                    get_meta(x[2], '소관부처명'),
                    get_meta(x[2], '법령상세링크'),
                    get_meta(x[2], '조문여부')
                )
                for x in zip(ids, texts, law_list)
            ]

            cursor = conn.cursor()
            cursor.executemany("""
                               INSERT INTO public.laws VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               """, data)
            conn.commit()
            cursor.close()
            print(f"{law.get('법령명한글')} 적재 완료!")


