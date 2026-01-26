from datetime import datetime
from typing import Annotated

from pydantic import Field

__all__ = ["CreatedAt", "UpdatedAt", "IsDeleted", "CreateUser", "UpdateUser", "IsActive"]

CreatedAt = Annotated[datetime, Field(description="Время создания (tz-aware)")]
UpdatedAt = Annotated[datetime, Field(description="Время обновления (tz-aware)")]
IsDeleted = Annotated[bool, Field(description="Удалено", default=False)]
CreateUser = Annotated[int, Field(description="ID пользователя, создавшего запись", ge=1)]
UpdateUser = Annotated[int, Field(description="ID пользователя, обновившего запись", ge=1)]
IsActive = Annotated[bool, Field(description="Активен", default=True)]
