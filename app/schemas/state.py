from typing import TypedDict, Tuple

class State(TypedDict):
    user_message:str
    last_messages:list[Tuple]
    is_index:bool