import requests

from rag_utils import load_secret_yaml

secret = load_secret_yaml()

class LawAPI:
    def __init__(self):
        self.auth = secret["law_api"]["auth"]
        self.key = secret["law_api"]["api_key"]
        self.base_url = "http://www.law.go.kr"


    def law_search_list(self, query, page_no=1, num_of_rows=100):
        service = "DRF/lawSearch.do"
        params = {
            "OC": self.auth,
            "target": "eflaw",
            "type": "JSON",
            "query": query,
            "page": page_no,
            "display": num_of_rows,
            "nw": 3
        }
        return self.__call_api(service, params)

    def get_law_detail(self, law_id):
        service = "DRF/lawService.do"
        params = {
            "OC": self.auth,
            "target": "eflaw",
            "type": "JSON",
            "ID": law_id
        }
        return self.__call_api(service, params)

    def __call_api(self, service, params):
        response = requests.get(f"{self.base_url}/{service}", params=params)
        if response.status_code == 200:
            return {
                'status': response.status_code,
                'data': response.json()
            }
        else:
            return {
                "status": response.status_code,
                "data": response.text
            }

def get_cntn(law_cntn):
    return law_cntn.strip() if isinstance(law_cntn, str) else str(law_cntn)

def change_circle_num(circle_num: str):
    if not circle_num: return circle_num
    if (len(circle_num) == 1) and (9312 <= ord(circle_num) <= 9331):
        return str(ord(circle_num) - 9312 + 1)
    else:
        return circle_num

def remove_dot(text: str):
    if not text: return text
    return text.replace('.', '')

def change_law_num(law_num: str):
    return change_circle_num(remove_dot(law_num))

def get_law_list(law_json, law_default_meta=None):
    if not law_default_meta:
        law_default_meta = {}

    law_list = []
    jo_list = law_json['법령']['조문'].get('조문단위', list())
    if isinstance(jo_list, dict):
        jo_list = [jo_list]

    for jo in jo_list:
        jo_metadata = law_default_meta.copy()
        jo_metadata['조문키'] = jo.get('조문키')
        jo_metadata['조문번호'] = change_law_num(jo.get('조문번호'))
        jo_metadata['조문시행일자'] = jo.get('조문시행일자')
        jo_metadata['조문제목'] = jo.get('조문제목')
        jo_metadata['조문가지번호'] = jo.get('조문가지번호')
        jo_metadata['조문여부'] = jo.get('조문여부')

        law_list.append({
            'text': get_cntn(jo.get('조문내용')),
            'metadata': jo_metadata,
        })

        haang_list = jo.get('항', list())
        if isinstance(haang_list, dict):
            haang_list = [haang_list]

        for haang in haang_list:
            haang_metadata = jo_metadata.copy()
            haang_metadata['항번호'] = change_law_num(haang.get('항번호'))
            if haang.get('항내용'):
                law_list.append({
                    'text': get_cntn(haang.get('항내용')),
                    'metadata': haang_metadata,
                })

            ho_list = haang.get('호', list())
            if isinstance(ho_list, dict):
                ho_list = [ho_list]

            for ho in ho_list:
                ho_metadata = haang_metadata.copy()
                ho_metadata['호번호'] = change_law_num(ho.get('호번호'))
                if ho.get('호내용'):
                    law_list.append({
                        'text': get_cntn(ho.get('호내용')),
                        'metadata': ho_metadata,
                    })

                mok_list = ho.get('목', list())
                if isinstance(mok_list, dict):
                    mok_list = [mok_list]

                for mok in mok_list:
                    mok_metadata = ho_metadata.copy()
                    mok_metadata['목번호'] = change_law_num(mok.get('목번호'))
                    if mok.get('목내용'):
                        law_list.append({
                            'text': get_cntn(mok.get('목내용')),
                            'metadata': mok_metadata,
                        })
    return law_list
