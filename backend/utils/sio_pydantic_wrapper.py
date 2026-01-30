from functools import wraps
from pydantic import BaseModel, ValidationError


def siomodel(model: type[BaseModel]):
    def decorator(f):
        @wraps(f)
        async def wrapper(sid: str, data: dict):
            validated_data = model.model_validate(data)
            await f(sid, validated_data)

        return wrapper

    return decorator
