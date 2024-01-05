FROM chaozi/wx-ai-collect:v1

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

RUN playwright install

CMD ["sh", "docker_entry.sh"]
