FROM chaozi/wx-ai-collect

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["sh", "docker_entry.sh"]
