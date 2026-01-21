from typing import List
from dataclasses import dataclass, field


@dataclass
class Law:
    law_id: str
    law_name: str
    jo_title: str
    jo_num: str
    jo_branch_num: str
    haang_num: str
    ho_num: str
    mok_num: str
    public_date: str
    law_cntn: str
    ministry: str
    link: str
    jo_type: str
    dense_embedding: list = field(default_factory=list, init=False)

    def to_dict(self, include: List[str] = None, exclude: List[str] = None):
        if include:
            return {k: v for k, v in self.__dict__.items() if k in include}
        if exclude:
            return {k: v for k, v in self.__dict__.items() if k not in exclude}
        return self.__dict__
