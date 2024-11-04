from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import pandas as pd
import psycopg2 as pg
import os
from dotenv import load_dotenv
load_dotenv()


pg_host = os.getenv('POSTGRS_HOST')
pg_port = os.getenv('POSTGRS_PORT')
pg_user = os.getenv('POSTGRS_USER')
pg_pass = os.getenv('POSTGRS_PASS')
pg_db_name = os.getenv('POSTGRS_DB')


# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_data_postrs(query_postrs_pattern):
    """
    Функция для получения порции данных по запросу query_postrs_pattern 
    из пг. Возвращает таблицу в виде пандас датафрейма
    """
    engine = pg.connect("dbname='{}' user='{}' host='{}' port='{}' password='{}'".format(pg_db_name, pg_user, 
                                                                                pg_host, pg_port, pg_pass))
    try:
        return pd.read_sql_query(query_postrs_pattern,con=engine)
    except Exception as e:
        raise e
    finally:
        engine.close()


def insert_data_pg(query, new_val):
    engine = pg.connect("dbname='{}' user='{}' host='{}' port='{}' password='{}'".format(pg_db_name, pg_user, 
                                                                                pg_host, pg_port, pg_pass))
    try:
        cursor = engine.cursor()
        cursor.execute(query, new_val)
        engine.commit()
    except Exception as e:
        raise e
    finally:
        engine.close()


def del_data_pg(query, id):
    engine = pg.connect("dbname='{}' user='{}' host='{}' port='{}' password='{}'".format(pg_db_name, pg_user, 
                                                                                pg_host, pg_port, pg_pass))
    try:
        cursor = engine.cursor()
        cursor.execute(query, (id,))
        engine.commit()
    except Exception as e:
        engine.rollback()
        raise e
    finally:
        engine.close()


app = FastAPI()

# Модель данных для пользователя
class User(BaseModel):
    username: str
    login: str
    hashed_password: str

class Package(BaseModel):
    user_id: int
    weight: int
    length: int
    width: int
    height: int

class Delivery(BaseModel):
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
    return get_data_postrs('SELECT id FROM "user";').to_json(orient='records')


# GET /users/{user_id} - Получить пользователя по ID (требует аутентификации)
@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT * FROM "user" WHERE id={user_id}; ').to_dict(orient='records')
    if len(data) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        return data[0]


# POST /users - Создать нового пользователя (требует аутентификации)
@app.post("/users", response_model=User)
def create_user(user: User, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT id FROM "user" WHERE login={user.login}; ').to_dict(orient='records')
    if len(data):
        raise HTTPException(status_code=404, detail="User already exist")
    else:
        insert_data_pg( """
        INSERT INTO "user" (username, hashed_password, login)
        VALUES (%s, %s, %s)
        """,
        [user.username, user.hashed_password, user.login])
    return user


# DELETE /users/{user_id} - Удалить пользователя по ID (требует аутентификации)
@app.delete("/users/{user_id}", response_model=User)
def delete_user(user_id: int, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT id FROM "user" WHERE id={user_id}; ').to_dict(orient='records')
    if len(data):
        del_data_pg('DELETE FROM "user" WHERE id = %s;',  user_id)
        return 'ok'
    else:
        raise HTTPException(status_code=404, detail="User not found")


########## package
# GET /package/{package_id} - Получить посылку по id (требует аутентификации)
@app.get("/package/{package_id}", response_model=Package)
def get_package_by_id(package_id: int, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT * FROM "package" WHERE package_id={package_id}; ').to_dict(orient='records')
    if len(data) == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    else:
        return data[0]


# POST /package - Создать новую посылку (требует аутентификации)
@app.post("/package", response_model=Package)
def create_package(package: Package, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT id FROM "user" WHERE id={package.user_id}; ').to_dict(orient='records')
    if len(data) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        insert_data_pg( """
        INSERT INTO "package" (user_id, weight, length, width, height)
        VALUES (%s, %s, %s, %s, %s)
        """, 
        [package.user_id, package.weight, package.length, package.width, package.height])
        return package


########## delivery
# POST /package - Создать новую доставку (требует аутентификации)
@app.post("/delivery", response_model=Delivery)
def create_delivery(delivery: Delivery, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT id FROM "user" WHERE id={delivery.recipient_id}; ').to_dict(orient='records')
    if len(data) == 0:
        raise HTTPException(status_code=404, detail="Recipient not found")
    data = get_data_postrs(f'SELECT id FROM "user" WHERE id={delivery.sender_id}; ').to_dict(orient='records')
    if len(data) == 0:
        raise HTTPException(status_code=404, detail="Sender not found")
    data = get_data_postrs(f'SELECT package_id FROM "package" WHERE package_id={delivery.package_id}; ').to_dict(orient='records')
    if len(data) == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    insert_data_pg( """
    INSERT INTO "delivery" (package_id, recipient_id, sender_id, status)
    VALUES (%s, %s, %s, %s)
    """,
    [delivery.package_id, delivery.recipient_id , delivery.sender_id , delivery.status])
    return delivery


## smth
# GET /package/user/{user_id} - Получить посылки по ID пользователя(требует аутентификации)
@app.get("/package/user/{user_id}", response_model=List[Package])
def get_package_by_user_id(user_id: int, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT * FROM "package" WHERE user_id={user_id}; ').to_dict(orient='records')
    if len(data):
        return data
    raise HTTPException(status_code=404, detail="User has no packages")


# GET /delivery/user/{user_id} - Узнать информацию по доставке по ID получателя(требует аутентификации)
@app.get("/delivery/user/{user_id}", response_model=List[Delivery])
def get_package_by_recipient(user_id: int, current_user: str = Depends(get_current_client)):
    data = get_data_postrs(f'SELECT * FROM "delivery" WHERE recipient_id={user_id}; ').to_dict(orient='records')
    if len(data):
        return data
    raise HTTPException(status_code=404, detail="Recipient has no deliveries")


# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)