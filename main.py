from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# Модель данных для пользователя
class User(BaseModel):
    id: int
    username: str
    email: str
    hashed_password: str
    age: Optional[int] = None

class Package(BaseModel):
    package_id: int
    user_id: int
    weight: int
    length: int
    width: int
    height: int

class Delivery(BaseModel):
    delivery_id: int
    package_id: int
    recipient_id: int
    sender_id: int
    status: str

# Временное хранилище для пользователей
users_db = []

# Временное хранилище посылок
package_db = []

# Временное хранилище доставок
delivery_db = []

# Псевдо-база данных пользователей
client_db = {
    "admin":  "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # hashed "secret"
}

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Зависимости для получения текущего пользователя
async def get_current_client(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        else:
            return username
    except JWTError:
        raise credentials_exception


# Создание и проверка JWT токенов
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Маршрут для получения токена
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    password_check = False
    if form_data.username in client_db:
        password = client_db[form_data.username]
        if pwd_context.verify(form_data.password, password):
            password_check = True

    if password_check:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


########## User
# GET /users - Получить всех пользователей (требует аутентификации)
@app.get("/users", response_model=List[User])
def get_users(current_user: str = Depends(get_current_client)):
    return users_db


# GET /users/{user_id} - Получить пользователя по ID (требует аутентификации)
@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, current_user: str = Depends(get_current_client)):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


# POST /users - Создать нового пользователя (требует аутентификации)
@app.post("/users", response_model=User)
def create_user(user: User, current_user: str = Depends(get_current_client)):
    for u in users_db:
        if u.id == user.id:
            raise HTTPException(status_code=404, detail="User already exist")
    users_db.append(user)
    return user


# PUT /users/{user_id} - Обновить пользователя по ID (требует аутентификации)
@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, updated_user: User, current_user: str = Depends(get_current_client)):
    for index, user in enumerate(users_db):
        if user.id == user_id:
            users_db[index] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")


# DELETE /users/{user_id} - Удалить пользователя по ID (требует аутентификации)
@app.delete("/users/{user_id}", response_model=User)
def delete_user(user_id: int, current_user: str = Depends(get_current_client)):
    for index, user in enumerate(users_db):
        if user.id == user_id:
            deleted_user = users_db.pop(index)
            return deleted_user
    raise HTTPException(status_code=404, detail="User not found")


########## package
# GET /package/{package_id} - Получить посылку по id (требует аутентификации)
@app.get("/package/{package_id}", response_model=Package)
def get_package_by_id(package_id: int, current_user: str = Depends(get_current_client)):
    for el in package_db:
        if el.package_id == package_id:
            return el
    raise HTTPException(status_code=404, detail="Package not found")


# POST /package - Создать новую посылку (требует аутентификации)
@app.post("/package", response_model=Package)
def create_package(package: Package, current_user: str = Depends(get_current_client)):
    for el in package_db:
        if el.package_id == package.package_id:
            raise HTTPException(status_code=404, detail="Package already exist")
    # Если бы были авторизованы под пользователем, а не админом, то проверка была бы не нужна
    # Хотя можно считать, что это проверяется на уровне хранилища
    for el in users_db:
        if el.id == package.user_id: 
            package_db.append(package)
            return package
    raise HTTPException(status_code=404, detail="User not found")


# PUT /package/{package_id} - Обновить посылку по ID (требует аутентификации)
@app.put("/package/{package_id}", response_model=Package)
def update_package(package_id: int, updated_package: Package, current_user: str = Depends(get_current_client)):
    for index, package in enumerate(package_db):
        if package.package_id == package_id:
            package_db[index] = updated_package
            return updated_package
    raise HTTPException(status_code=404, detail="Package not found")


# DELETE /package/{package_id} - Удалить посылку по ID (требует аутентификации)
@app.delete("/package/{package_id}", response_model=Package)
def delete_user(package_id: int, current_user: str = Depends(get_current_client)):
    for index, package in enumerate(package_db):
        if package.package_id == package_id:
            deleted_package = package_db.pop(index)
            return deleted_package
    raise HTTPException(status_code=404, detail="Package not found")


########## delivery
# POST /package - Создать новую доставку (требует аутентификации)
@app.post("/delivery", response_model=Delivery)
def create_delivery(delivery: Delivery, current_user: str = Depends(get_current_client)):
    for el in delivery_db:
        if el.delivery_id == delivery.delivery_id:
            raise HTTPException(status_code=404, detail="Delivery already exist")
    # Если бы были авторизованы под пользователем, а не админом, то проверка была бы не нужна
    # Хотя можно считать, что это проверяется на уровне хранилища
    flag = False
    for el in users_db:
        if el.id == delivery.recipient_id: 
            flag = True
    if flag:
        for el in users_db:
            if el.id == delivery.sender_id:
                delivery_db.append(delivery)
                return delivery
    else:
        raise HTTPException(status_code=404, detail="Recipient not found")
    raise HTTPException(status_code=404, detail="Sender not found")

## smth
# GET /user_package/{user_id} - Получить посылки по ID пользователя(требует аутентификации)
@app.get("/user_package/{user_id}", response_model=List[Package])
def get_package_by_user_id(user_id: int, current_user: str = Depends(get_current_client)):
    all_el = []
    for el in package_db:
        if el.user_id == user_id:
            all_el.append(el)
    if len(all_el):
        return all_el
    raise HTTPException(status_code=404, detail="User has no packages")


# GET /user_delivery/{user_id} - Узнать информацию по доставке по ID получателя(требует аутентификации)
@app.get("/user_delivery/{user_id}", response_model=List[Delivery])
def get_package_by_recipient(user_id: int, current_user: str = Depends(get_current_client)):
    all_el = []
    for el in delivery_db:
        if el.recipient_id == user_id:
            all_el.append(el)
    if len(all_el):
        return all_el
    raise HTTPException(status_code=404, detail="User has no deliveries")


# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)