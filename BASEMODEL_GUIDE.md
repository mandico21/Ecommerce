# Расширенная BaseModel: Полный гайд

## Что было добавлено

Ваша `BaseModel` теперь имеет 5 основных методов для удобной работы с моделями:

```python
from app.pkg.models.base import BaseModel
from pydantic import Field, SecretStr

class User(BaseModel):
    id: int = Field(description="User ID")
    name: str = Field(description="User name")
    email: str = Field(description="Email")
    password: SecretStr = Field(description="Encrypted password")
    phone: str | None = None
```

---

## 1️⃣ `to_dict()` - Преобразование в словарь

### Базовое использование

```python
user = User(
    id=1,
    name="John Doe",
    email="john@example.com",
    password="secret123",
    phone="+1234567890"
)

# Базовый дамп (SecretStr маскируется)
user.to_dict()
# {
#     'id': 1,
#     'name': 'John Doe',
#     'email': 'john@example.com',
#     'password': '**********',
#     'phone': '+1234567890'
# }
```

### С раскрытием секретов

```python
# Раскрыть SecretStr/SecretBytes
user.to_dict(show_secrets=True)
# {
#     'id': 1,
#     'name': 'John Doe',
#     'email': 'john@example.com',
#     'password': 'secret123',  ← Видно!
#     'phone': '+1234567890'
# }
```

### Пропуск None значений

```python
# Исключить None значения
user.to_dict(skip_nulls=True)
# {
#     'id': 1,
#     'name': 'John Doe',
#     'email': 'john@example.com',
#     'password': '**********',
#     'phone': '+1234567890'
# }

# Если бы phone было None:
user_no_phone = User(..., phone=None)
user_no_phone.to_dict(skip_nulls=True)
# {
#     'id': 1,
#     'name': 'John Doe',
#     'email': 'john@example.com',
#     'password': '**********'
#     # phone исключён!
# }
```

### С дополнительными параметрами

```python
# Исключить определённые поля
user.to_dict(exclude={'password', 'phone'})
# {
#     'id': 1,
#     'name': 'John Doe',
#     'email': 'john@example.com'
# }

# Включить только определённые поля
user.to_dict(include={'id', 'name', 'email'})
# {
#     'id': 1,
#     'name': 'John Doe',
#     'email': 'john@example.com'
# }

# Комбинировать параметры
user.to_dict(show_secrets=True, skip_nulls=True, exclude={'password'})
```

---

## 2️⃣ `to_query_params()` - Преобразование в URL параметры

### Базовое использование

```python
user = User(
    id=1,
    name="John Doe",
    email="john@example.com",
    password="secret123",
    phone=None
)

# Базовый дамп
user.to_query_params()
# 'id=1&name=John+Doe&email=john%40example.com&password=**********&phone=None'
```

### Исключить None

```python
# Исключить None значения (по умолчанию без_none=True)
user.to_query_params(without_none=True)
# 'id=1&name=John+Doe&email=john%40example.com&password=**********'
# phone исключён, т.к. None

# Включить None
user.to_query_params(without_none=False)
# 'id=1&name=John+Doe&email=john%40example.com&password=**********&phone=None'
```

### С раскрытием секретов

```python
# Раскрыть пароль (осторожно!)
user.to_query_params(show_secrets=True, without_none=True)
# 'id=1&name=John+Doe&email=john%40example.com&password=secret123'
```

### Практическое применение

```python
# Использование в API запросах
import httpx

query = user.to_query_params(without_none=True)
response = httpx.get(f"https://api.example.com/search?{query}")

# Или с httpx параметрами
response = httpx.get(
    "https://api.example.com/search",
    params=user.to_dict(skip_nulls=True, exclude={'password'})
)
```

---

## 3️⃣ `without()` - Копия без указанных полей

### Базовое использование

```python
user = User(
    id=1,
    name="John Doe",
    email="john@example.com",
    password="secret123",
    phone="+1234567890"
)

# Копия без пароля (для логирования)
user_safe = user.without('password')
# User(id=1, name='John Doe', email='john@example.com', phone='+1234567890')

# Копия без нескольких полей
user_minimal = user.without('password', 'phone')
# User(id=1, name='John Doe', email='john@example.com')
```

### Глубокая копия

```python
# Без аргументов = глубокая копия
user_copy = user.without()
# Это полная копия объекта

# Проверка, что это разные объекты
user.phone = "modified"
print(user_copy.phone)  # "+1234567890" (не изменилось)
```

### Практическое применение

```python
# Безопасное логирование без пароля
logger.info(f"User created: {user.without('password').to_dict()}")

# Отправка в API без sensitive данных
response = httpx.post(
    "https://api.example.com/users",
    json=user.without('password', 'phone').model_dump()
)

# Сохранение в кеш без некоторых полей
cache.set(f"user:{user.id}", user.without('password').to_json())
```

---

## 4️⃣ `migrate()` - Миграция между моделями

### Простая миграция

```python
# Исходная модель
class UserDB(BaseModel):
    user_id: int
    full_name: str
    email_address: str
    is_active: bool

# Целевая модель
class UserAPI(BaseModel):
    id: int
    name: str
    email: str

user_db = UserDB(
    user_id=1,
    full_name="John Doe",
    email_address="john@example.com",
    is_active=True
)

# Миграция с маппингом полей
user_api = user_db.migrate(
    UserAPI,
    match_keys={
        "id": "user_id",
        "name": "full_name",
        "email": "email_address"
    }
)
# UserAPI(id=1, name="John Doe", email="john@example.com")
```

### Миграция с дополнительными полями

```python
class UserWithTimestamp(BaseModel):
    id: int
    name: str
    email: str
    created_at: str

user_api = user_db.migrate(
    UserWithTimestamp,
    match_keys={"id": "user_id", "name": "full_name", "email": "email_address"},
    extra_fields={"created_at": "2026-02-26T00:00:00"}
)
# UserWithTimestamp(id=1, name="John Doe", email="john@example.com", created_at="2026-02-26T00:00:00")
```

### Использование в преобразованиях

```python
# Получение из БД
user_from_db: UserDB = db.get_user(user_id=1)

# Преобразование для API ответа
user_response: UserAPI = user_from_db.migrate(
    UserAPI,
    match_keys={
        "id": "user_id",
        "name": "full_name",
        "email": "email_address"
    }
)

# Возврат клиенту
return user_response
```

---

## 5️⃣ `field_getter()` - Получение типа поля

### Базовое использование

```python
class Product(BaseModel):
    id: int
    name: str
    price: float
    description: str | None = None

# Получить тип поля
Product.field_getter("id")      # <class 'int'>
Product.field_getter("name")    # <class 'str'>
Product.field_getter("price")   # <class 'float'>
Product.field_getter("description")  # str | None
```

### Обработка ошибок

```python
# Поле не существует
Product.field_getter("invalid_field")
# AttributeError: Поле 'invalid_field' не найдено в Product.
# Доступные поля: ['id', 'name', 'price', 'description']
```

### Практическое применение

```python
# Динамическое создание полей в Pydantic
from pydantic import Field

class DynamicModel(BaseModel):
    id: int = Field(description="ID")
    name: str = Field(description="Name")

# Получить тип поля и использовать
field_type = DynamicModel.field_getter("id")
print(f"Тип поля 'id': {field_type}")

# Проверка типов
def validate_field_type(model_class, field_name, expected_type):
    actual_type = model_class.field_getter(field_name)
    return actual_type == expected_type

validate_field_type(DynamicModel, "id", int)  # True
```

---

## 📋 Полная иерархия методов

```
BaseModel
├── to_dict()           ← Преобразование в словарь
├── to_json()           ← Преобразование в JSON (встроено в Pydantic)
├── to_query_params()   ← Преобразование в URL параметры
├── without()           ← Копия без полей
├── migrate()           ← Миграция в другую модель
└── field_getter()      ← Получение типа поля (classmethod)
```

---

## 🎯 Примеры из реальной жизни

### Пример 1: REST API обработчик

```python
from fastapi import FastAPI, HTTPException
from app.pkg.models.base import BaseModel

class UserDB(BaseModel):
    user_id: int
    full_name: str
    email_address: str

class UserAPIResponse(BaseModel):
    id: int
    name: str
    email: str

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> UserAPIResponse:
    # Получить из БД
    user_db = await db.get_user(user_id)
    
    # Мигрировать в API модель
    return user_db.migrate(
        UserAPIResponse,
        match_keys={
            "id": "user_id",
            "name": "full_name",
            "email": "email_address"
        }
    )
```

### Пример 2: Безопасное логирование

```python
class User(BaseModel):
    id: int
    name: str
    email: str
    password: SecretStr
    api_key: SecretStr

user = User(...)

# Логировать только безопасные данные
logger.info(f"User login: {user.without('password', 'api_key').to_dict()}")

# Более лаконично
logger.info(f"User: {user.without('password', 'api_key')}")
```

### Пример 3: Кеширование в Redis

```python
class Product(BaseModel):
    id: int
    name: str
    price: float
    inventory_count: int
    last_updated: datetime

product = Product(...)

# Кешировать без частых обновлений
cache_key = f"product:{product.id}"
cache_value = product.without('last_updated').to_json()
redis.set(cache_key, cache_value, ex=3600)
```

### Пример 4: Внешние API запросы

```python
class SearchFilters(BaseModel):
    query: str
    min_price: float | None = None
    max_price: float | None = None
    category: str | None = None
    sort_by: str | None = None

filters = SearchFilters(query="laptop", min_price=500)

# Отправить в API (None значения исключаются)
response = httpx.get(
    "https://api.example.com/search",
    params=filters.to_dict(skip_nulls=True)
)
# URL: https://api.example.com/search?query=laptop&min_price=500

# Или через to_query_params
url = f"https://api.example.com/search?{filters.to_query_params()}"
response = httpx.get(url)
```

### Пример 5: Конвертация между форматами

```python
class UserFormData(BaseModel):
    user_id: int
    first_name: str
    last_name: str

class UserDatabase(BaseModel):
    id: int
    name: str

form_data = UserFormData(user_id=1, first_name="John", last_name="Doe")

# Конвертировать для сохранения в БД
db_user = form_data.migrate(
    UserDatabase,
    match_keys={"id": "user_id", "name": None},  # name не маппируется
    extra_fields={"name": f"{form_data.first_name} {form_data.last_name}"}
)
# UserDatabase(id=1, name="John Doe")
```

---

## ⚠️ Важные замечания

### SecretStr/SecretBytes

```python
from pydantic import SecretStr

class User(BaseModel):
    password: SecretStr

user = User(password="secret123")

# SecretStr автоматически маскируется
print(user.to_dict())
# {'password': '**********'}

# Раскрыть только для безопасных операций
print(user.to_dict(show_secrets=True))
# {'password': 'secret123'}

# НИКОГДА не логируйте с show_secrets=True в production!
```

### None vs пропуск поля

```python
class Model(BaseModel):
    field1: str
    field2: str | None = None

model = Model(field1="value")

# to_dict() вернёт field2: None
model.to_dict()  # {'field1': 'value', 'field2': None}

# to_dict(skip_nulls=True) исключит field2
model.to_dict(skip_nulls=True)  # {'field1': 'value'}

# to_query_params() по умолчанию исключает None
model.to_query_params()  # 'field1=value'
```

---

## 🧪 Тестирование

```python
from app.pkg.models.base import BaseModel

def test_to_dict():
    model = Model(id=1, name="test", email=None)
    
    # Базовый тест
    assert model.to_dict() == {'id': 1, 'name': 'test', 'email': None}
    
    # С пропуском None
    assert model.to_dict(skip_nulls=True) == {'id': 1, 'name': 'test'}
    
    # С исключением поля
    assert model.to_dict(exclude={'email'}) == {'id': 1, 'name': 'test'}

def test_migrate():
    source = SourceModel(a=1, b=2)
    target = source.migrate(TargetModel, match_keys={"x": "a", "y": "b"})
    
    assert target.x == 1
    assert target.y == 2

def test_field_getter():
    assert Model.field_getter("id") == int
    assert Model.field_getter("name") == str
    
    with pytest.raises(AttributeError):
        Model.field_getter("invalid")
```

---

## 📚 Резюме

| Метод | Назначение | Пример |
|-------|-----------|--------|
| `to_dict()` | Преобразование в dict | `model.to_dict(skip_nulls=True)` |
| `to_json()` | Преобразование в JSON | `model.to_json()` |
| `to_query_params()` | Преобразование в URL параметры | `model.to_query_params(without_none=True)` |
| `without()` | Копия без полей | `model.without('password', 'api_key')` |
| `migrate()` | Миграция в другую модель | `model.migrate(OtherModel, match_keys={...})` |
| `field_getter()` | Получить тип поля | `Model.field_getter('id')` |

---

✅ **Теперь у вас есть мощная и гибкая BaseModel!** 🎉

