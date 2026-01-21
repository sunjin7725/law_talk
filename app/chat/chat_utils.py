import inspect

from typing import Callable, TypeVar

from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_openai import ChatOpenAI

from utils import load_secret_yaml


def load_chat_model(model="gpt-5-mini", temperature=None, stream=True):
    secret = load_secret_yaml()
    model = ChatOpenAI(api_key=secret["openai"]["api_key"], model=model, temperature=temperature, streaming=stream)
    return model

def get_streamlit_cb(parent_container: DeltaGenerator) -> BaseCallbackHandler:
    fn_return_type = TypeVar('fn_return_type')
    def add_streamlit_context(fn: Callable[..., fn_return_type]) -> Callable[..., fn_return_type]:
        ctx = get_script_run_ctx()
        def wrapper(*args, **kwargs) -> fn_return_type:
            add_script_run_ctx(ctx=ctx)
            return fn(*args, **kwargs)
        return wrapper

    st_cb = StreamlitCallbackHandler(parent_container)

    for method_name, method_func in inspect.getmembers(st_cb, predicate=inspect.ismethod):
        if method_name.startswith('on_'):
            setattr(st_cb, method_name, add_streamlit_context(method_func))
    return st_cb
