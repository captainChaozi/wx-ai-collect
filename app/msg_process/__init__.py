import time
import requests
import datetime
import os
import re
import uuid
from urllib.parse import quote_plus
from dotenv import load_dotenv
from app.msg_process.llm_chains import url_ask_google_genai, msg_ask_google_genai
from requests_toolbelt import MultipartEncoder

load_dotenv()


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
        expire_time = datetime.timedelta(
            seconds=(response.json()['expire']-10)) + datetime.datetime.now()
        # 返回token 和过期具体时间
        return access_token, expire_time

    @property
    def lark_token(self):
        if self._lark_token_tmp is None or self._lark_token_tmp[1] < datetime.datetime.now():
            self._lark_token_tmp = self._tenenant_access_token()
        return self._lark_token_tmp[0]

    def create_image_block(self, document_id, image_url):

        # 随机文件名
        filename = str(uuid.uuid4()) + '.jpg'
        try:
            response = requests.get(image_url)
        except:
            return
        if 'image' not in response.headers.get('Content-Type', ''):
            return

        # 确保请求成功
        if response.status_code == 200:
            # 打开一个文件用于写入
            with open(filename, 'wb') as file:
                file.write(response.content)
        else:
            return
        # 创建图片块
        block_id = document_id
        url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.lark_token}'
        }
        data = {
            "index": 0,
            "children": [
                {
                    "block_type": 27,
                    "image": {
                        "token": ""
                    }
                }
            ]
        }
        res = requests.post(url, headers=headers, json=data)

        image_block_id = res.json()['data']['children'][0]['block_id']

        # 上传图片
        file_size = os.path.getsize(filename)
        url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
        form = {'file_name': filename,
                'parent_type': 'docx_image',
                'parent_node': image_block_id,
                'size': str(file_size),
                'file': (open(filename, 'rb'))}
        multi_form = MultipartEncoder(form)
        headers = {
            # 获取tenant_access_token, 需要替换为实际的token
            'Content-Type': 'multipart/form-data',

            'Authorization': f'Bearer {self.lark_token}'
        }
        headers['Content-Type'] = multi_form.content_type
        response = requests.request(
            "POST", url, headers=headers, data=multi_form)
        media_id = response.json()['data']['file_token']
        # 更新图片块
        url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{image_block_id}'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.lark_token}'
        }
        data = {
            "replace_image": {
                "token": media_id  # 图片素材 ID
            }
        }
        res = requests.patch(url, headers=headers, json=data)

        os.remove(filename)

    def create_text_block(self, document_id,  block_type, msg='', text_url=''):
        # 创建文档块

        block_id = document_id
        url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.lark_token}'
        }
        text_element_style = {}
        if text_url:
            text_element_style = {
                "link": {"url": quote_plus(text_url)}
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
        if text_type == 'driver':
            data = {
                "index": 0,
                "children": [
                    {
                        "block_type": 22,
                        "divider": {
                        }
                    }
                ]
            }
        res = requests.post(url, headers=headers, json=data)

    def process(self, wechat_data):

        if wechat_data.get('MsgType') == 49 and wechat_data.get('AppMsgType') == 5:
            msg = wechat_data.get('FileName')
            url = wechat_data.get('Url')
        elif wechat_data.get('MsgType') == 1:
            msg = wechat_data.get('Content')
            url = ''
            pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(pattern, msg)
            if urls:
                url = urls[0]

        else:
            return
        if url:
            ai_process_data = url_ask_google_genai(msg=msg, url=url)
        else:
            ai_process_data = msg_ask_google_genai(msg)
        print(ai_process_data)

        # 保存到飞书
        self.save_feishu(ai_process_data)

    # 分类

    def save_feishu(self, ai_process_data):
        document_id = ai_process_data.get('document_id')
        title = ai_process_data.get('title')
        msg = ai_process_data.get('msg')
        url = ai_process_data.get('url')
        summary = ai_process_data.get('summary')
        image = ai_process_data.get('image')
        inspire = ai_process_data.get('inspire')
        self.create_text_block(document_id=document_id, block_type=22)

        if image:
            self.create_image_block(document_id=document_id, image_url=image)

        if inspire:
            self.create_text_block(
                document_id=document_id, block_type=2, msg=inspire)

        # self.create_text_block(
        #     document_id=document_id, block_type=2, msg='标签: '+','.join(tags))
        self.create_text_block(document_id=document_id,
                               block_type=2, msg=summary)

        if msg != title:
            self.create_text_block(
                document_id=document_id, block_type=2, msg=msg)

        if url:
            self.create_text_block(
                document_id=document_id, block_type=5, msg=title, text_url=url)
        else:
            self.create_text_block(
                document_id=document_id, block_type=5, msg=title)


if __name__ == '__main__':
    msg_process = MsgProcess()
    msg_process.create_image_block(
        image_url="https://i.ytimg.com/vi/Dl53poAkbZo/maxresdefault.jpg", document_id='KvLado1XOoMDz3x4Ssncj6QAnrb')
