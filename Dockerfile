FROM chaozi/wx-ai-collect:v1

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["sh", "docker_entry.sh"]
