FROM python:3.11.1-buster

ENV TZ=America/Sao_Paulo

# Atualizações e instalação de dependências
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./django_bet /app

WORKDIR /app

#RUN mkdir -p /app/logs

COPY ./entrypoint.sh /
ENTRYPOINT ["sh", "/entrypoint.sh"]

