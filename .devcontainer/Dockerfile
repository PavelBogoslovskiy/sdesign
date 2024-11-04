# Используем официальный образ Python 3.11
FROM python:3.11-slim
COPY --from=openjdk:21-jdk-slim /usr/local/openjdk-21 /usr/local/openjdk-21
COPY --from=structurizr/lite /usr/local/structurizr-lite.war /usr/local/

ENV JAVA_HOME=/usr/local/openjdk-21
ENV LANG=C.UTF-8
ENV PATH=/usr/local/openjdk-21/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN update-alternatives --install /usr/bin/java java /usr/local/openjdk-21/bin/java 1  

# Устанавливаем рабочую директорию
WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wrk \
    iputils-ping \
    postgresql \ 
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .
COPY ./.devcontainer/bee-c4-dsl-extension.vsix /tmp/

# Открываем порт 8000 для FastAPI
EXPOSE 8000

# ENTRYPOINT ["/bin/sh", "-c" ,"while true; do sleep 1000; done"]
ENTRYPOINT ["/bin/sh", "-c" ,"java -jar /usr/local/structurizr-lite.war /workspace/01_structurizr"]

