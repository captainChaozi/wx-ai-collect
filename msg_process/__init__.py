import requests
import datetime
import os
import google.generativeai as genai
from dotenv import load_dotenv
from urllib.parse import quote_plus


load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_GEMINI_KEY"])


class MsgProcess:
    def __init__(self):
        self._lark_token_tmp = None

    def _tenenant_access_token(self):
        # 获取tenenant_access_token
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'app_id': os.getenv('LARK_APP_ID'),
            'app_secret': os.getenv('LARK_APP_SECRET')
        }
        response = requests.post(url, headers=headers, json=data)
        access_token = response.json()['tenant_access_token']
        print(response.json())
        expire_time = datetime.timedelta(
            seconds=(response.json()['expire']-10)) + datetime.datetime.now()
        # 返回token 和过期具体时间
        print(access_token, expire_time)
        return access_token, expire_time

    @property
    def lark_token(self):
        if self._lark_token_tmp is None or self._lark_token_tmp[1] < datetime.datetime.now():
            self._lark_token_tmp = self._tenenant_access_token()
        return self._lark_token_tmp[0]

    def create_text_block(self, document_id,  block_type, msg='', url=''):
        # 创建文档块

        block_id = document_id
        url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.lark_token}'
        }
        text_element_style = {}
        if url:
            text_element_style = {
                "link": {"url": quote_plus(url)}
            }
        if block_type == 5:
            text_type = "heading3"
        elif block_type == 22:
            text_type = "driver"
        else:
            text_type = "text"

        data = {
            "index": 0,
            "children": [
                {
                    "block_type": block_type,
                    text_type: {
                        "elements": [
                            {
                                "text_run": {
                                    "content": msg,
                                    "text_element_style": text_element_style

                                }
                            },

                        ],
                        "style": {}
                    }
                }
            ]
        }
        requests.post(url, headers=headers, json=data)

    def process(self, wechat_data):

        if wechat_data.get('MsgType') == 49 and wechat_data.get('AppMsgType') == 5:
            title = wechat_data.get('FileName')
            url = wechat_data.get('Url')
        elif wechat_data.get('MsgType') == 1:
            title = wechat_data.get('Content')
            url = ''
        else:
            return

        # openai 进行分类
        ai_process_data = self.classify(title=title, url=url)

        # 保存到飞书
        self.save_feishu(ai_process_data)

    # 分类

    def classify(self, title, url) -> dict:

        prompt = f"标题：{title}\n链接：{url},请访问这个链接，并且给出摘要"

        model = genai.GenerativeModel('gemini-pro')

        response = model.generate_content(prompt)
        print(response.text)  # cold.

    def save_feishu(self, ai_process_data):
        document_id = ai_process_data['document_id']
        title = ai_process_data['title']
        url = ai_process_data.get('url')
        summary = ai_process_data['summary']
        tags = ai_process_data['tags']
        self.create_text_block(document_id=document_id, block_type=22)
        for tag in tags:
            self.create_text_block(
                document_id=document_id, block_type=5, msg=tag)
        self.create_text_block(document_id=document_id,
                               block_type=22, msg=summary)

        if url:
            self.create_text_block(
                document_id=document_id, block_type=5, msg=title, url=url)
        else:
            self.create_text_block(
                document_id=document_id, block_type=5, msg=title)


if __name__ == '__main__':
    msg_process = MsgProcess()
    msg_process.classify(
        title='SEO 竞争策略分享', url='https://mp.weixin.qq.com/s/ILzpMWW8M4ELj66Bfh8P7w')
