import time
from confluent_kafka import Consumer, KafkaError
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, declarative_base
import json

pg_host = 'db'
pg_port = 5432
pg_user = 'postgres'
pg_pass = 'postgres'
pg_db_name = 'db'


def writer_def():
    while True:  # Цикл для повторного запуска при ошибке
        try:
            # Настройка SQLAlchemy
            engine = create_engine(f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}/{pg_db_name}", echo=True)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base = declarative_base()

            # Модель пользователя
            class User(Base):
                __tablename__ = "user"
                id = Column(Integer, primary_key=True, index=True)
                username = Column(String(256), nullable=False)
                hashed_password = Column(String(256), nullable=False)
                login = Column(String(256), nullable=False, unique=True)
                created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

            # Создание таблиц
            Base.metadata.create_all(bind=engine)

            # Настройка Kafka Consumer
            conf = {
                'bootstrap.servers': 'kafka1:9092,kafka2:9092',
                'group.id': 'user_group',
                'auto.offset.reset': 'earliest'
            }
            print("Попытка запуска Kafka Writer...")
            consumer = Consumer(conf)
            consumer.subscribe(['user_topic'])

            db = SessionLocal()
            print("Kafka Writer успешно запущен.")

            # Основной цикл обработки сообщений
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                        print(f"Ошибка: Топик {msg.error()}. Перезапуск через 5 секунд")
                        raise Exception("Топик отсутствует. Перезапуск")
                    else:
                        print(f"Kafka Error: {msg.error()}")
                        raise Exception("Неизвестная ошибка Kafka. Перезапуск")

                # Десериализация и запись в БД
                user_data = json.loads(msg.value().decode('utf-8'))
                db_user = User(**user_data)
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                print(f"Получены данные пользователя: {user_data}")

        except Exception as e:
            print(f"Ошибка: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)

        finally:
            try:
                if 'consumer' in locals():
                    consumer.close()
                if 'db' in locals():
                    db.close()
            except Exception as close_error:
                print(f"Ошибка при закрытии ресурсов: {close_error}")


writer_def()
