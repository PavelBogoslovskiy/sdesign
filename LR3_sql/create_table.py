import subprocess
import os
from dotenv import load_dotenv
load_dotenv()

pg_host = os.getenv('POSTGRS_HOST')
pg_port = os.getenv('POSTGRS_PORT')
pg_user = os.getenv('POSTGRS_USER')
pg_pass = os.getenv('POSTGRS_PASS')
pg_db_name = os.getenv('POSTGRS_DB')

# dbname = "postgres"
# user = "postgres"
# host = "172.19.0.3" # Нужно подставить свой хост
# password = "postgres"

def create_table(query):
    command = [
    "psql",
    "-d", pg_db_name,
    "-U", pg_user,
    "-h", pg_host,
    "-c", query
    ]
    try:
        result = subprocess.run(
            command, 
            check=True, 
            text=True,
            input=pg_pass,  # Передача пароля
            env={**{"PGPASSWORD": pg_pass}}, 
            capture_output=True
        )
        print("Output:", result.stdout)
    except Exception as e:
        print(f'Ошибка: {e}')


user_table_query = '''CREATE TABLE IF NOT EXISTS "user" (
	id SERIAL NOT NULL,
	username VARCHAR(256) NOT NULL,
	hashed_password VARCHAR(256) NOT NULL,
	login VARCHAR(256) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT id PRIMARY KEY (id)
);'''


package_table_query = '''CREATE TABLE IF NOT EXISTS "package" (
	package_id serial NOT NULL,
    user_id INT REFERENCES "user" (id) ON DELETE CASCADE,
	weight INT NOT NULL,
	length INT NOT NULL,
	width INT NOT NULL,
	height INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT package_id PRIMARY KEY (package_id)
);'''


delivery_table_query = '''CREATE TABLE IF NOT EXISTS "delivery" (
	delivery_id serial NOT NULL,
    package_id INT REFERENCES "package" (package_id) ON DELETE CASCADE,
	recipient_id INT REFERENCES "user" (id) ON DELETE CASCADE,
	sender_id INT REFERENCES "user" (id) ON DELETE CASCADE,
	status VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT delivery_id PRIMARY KEY (delivery_id)
);'''


print(f'Создание таблицы user')
create_table(user_table_query)

print(f'Создание таблицы package')
create_table(package_table_query)

print(f'Создание таблицы delivery')
create_table(delivery_table_query)