import requests
import os


def post_feishu_webhook(message):
    url = os.getenv('FEISHU_WEBHOOK')
    data = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }

    requests.post(url=url, json=data)
