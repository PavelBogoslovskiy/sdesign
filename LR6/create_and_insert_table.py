import pandas as pd
from pymongo import MongoClient, ASCENDING
from sqlalchemy import create_engine
import random as rd
from datetime import datetime

pg_host = 'db'
pg_port = 5432
pg_user = 'postgres'
pg_pass = 'postgres'
pg_db_name = 'db'



def data_to_mongo(df, collection_name, index=''):

    client = MongoClient("mongodb://mongodb:27017")
    db = client["db"]

    # Коллекция для хранения данных пакетов
    collection = db[collection_name]

    if index != '':
        # Создаем уникальный индекс по полю index
        collection.create_index([(index, ASCENDING)], unique=True)
    
    try:
        d = df.to_dict('records')
        collection.insert_many(d)
    except Exception as e:
        raise e
    finally:
        client.close()


engine = create_engine(f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}/{pg_db_name}", echo = True)

print('Наполнение user')
user_df = pd.read_json("user_data.json")
user_df[['username', 'hashed_password', 'login']].to_sql("user", con=engine, if_exists = 'append', index=False)


print('Наполнение package')
num_rows = 1000
df_package = pd.DataFrame()
df_package['package_id'] = range(num_rows)
df_package['user_id'] = [rd.randint(1, len(user_df)) for i in range(num_rows)]
df_package['weight'] = [rd.randint(0, 50) for i in range(num_rows)]
df_package['length'] = [rd.randint(0, 50) for i in range(num_rows)]
df_package['height'] = [rd.randint(0, 50) for i in range(num_rows)]
df_package['width'] = [rd.randint(0, 50) for i in range(num_rows)]
df_package[['user_id', 'weight', 'length', 'height', 'width']].to_sql("package", con=engine, if_exists = 'append', index=False)

print('Наполнение delivery')
statuses = [
    "Посылка отправлена",
    "В процессе сортировки",
    "Курьер назначен",
    "Доставка приостановлена",
    "Таможенный контроль",
    "Успешная доставка",
    "Ожидание получения",
    "Ошибка доставки",
    "Срок хранения истекает"
]

num_rows = 1000
df_delivery = pd.DataFrame()
df_delivery['delivery_id'] = range(num_rows)
df_delivery['package_id'] = [rd.randint(1, len(df_package)) for i in range(num_rows)]
df_delivery['package_id'] = [rd.randint(1, len(df_package)) for i in range(num_rows)]
df_delivery['recipient_id'] = [rd.randint(1, len(user_df)) for i in range(num_rows)]
df_delivery['sender_id'] = [rd.randint(1, len(user_df)) for i in range(num_rows)]
df_delivery['created_at'] = datetime.now() 
df_delivery['status'] = [rd.choice(statuses) for i in range(num_rows)]

data_to_mongo(df_delivery, 'delivery', 'delivery_id')