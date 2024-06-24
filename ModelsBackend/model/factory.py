from model.model import Model
from typing import Callable, Any

model_creation_funcs: dict[str, Callable[..., Model]] = {}

def register_model(model_type: str, func: Callable[..., Model]) -> None:
    model_creation_funcs[model_type] = func

def unregister_model(model_type: str) -> None:
    model_creation_funcs.pop(model_type, None)

def create_model(arguments: dict[str, Any]) -> Model:
    args_copy = arguments.copy()
    model_type = args_copy.pop("type")
    model_params = args_copy.pop("parameters")
    try:
        creation_func = model_creation_funcs[model_type]
        return creation_func(**model_params)
    except KeyError:
        raise ValueError(f"Unknown model type: {model_type}") from None