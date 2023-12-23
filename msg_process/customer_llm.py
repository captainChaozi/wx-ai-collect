from pprint import pprint
import requests
import os
from typing import Any, List, Optional


from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM


class CustomGeminiLLM(LLM):

    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")
        base_url = os.environ.get(
            'GOOGLE_GEMINI_PROXY', 'https://generativelanguage.googleapis.com')
        url = f"{base_url}/v1beta/models/gemini-pro:generateContent?key={os.environ.get('GOOGLE_API_KEY')}"
        data = {"contents": [
            {"parts": [{"text": prompt}]}
        ]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=data, headers=headers)
        res_data = response.json()
        pprint(res_data)
        res = res_data['candidates'][0]['content']['parts'][0]['text']
        return res


if __name__ == "__main__":
    llm = CustomGeminiLLM()
    print(llm("你好"))
