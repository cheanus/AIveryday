import time
import pytz
import psutil
import logging
from openai import OpenAI
from datetime import datetime
from utils import get_free_gpu_memory
from ActivityWatcher import ActivityWatcher

class Chat:
    def __init__(self, aw: ActivityWatcher, args) -> None:
        self.aw = aw
        self.aw.set_rules()
        self.args = args

    def prompt(self, scope: int):
        start_time = datetime.fromtimestamp(time.time()-self.args['time']['scope'], pytz.utc)
        end_time = datetime.fromtimestamp(time.time(), pytz.utc)
        timeperiods = f"{start_time.strftime('%Y-%m-%dT%H:%M:%S')}/{end_time.strftime('%Y-%m-%dT%H:%M:%S')}"
        data = self.aw.get_data(timeperiods)

        if data is None:
            return None
        
        basic_info = {
            "scope_hour": scope/3600,
            "top_app": self.aw.top_events(data, 'app'),
            "top_title": self.aw.top_events(data, 'title'),
            "top_cat": self.aw.top_events(data, 'cat'),
            "duration_min": data['duration']/60,
            "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')
        }

        prompt = self.args['prompts']['notify'].format(**basic_info)
        
        return prompt
    
    def chatgpt(self, prompt: str):
        is_use_remote = False
        # 检查是否有足够的内存
        if self.args['openai']['local']['is_GPU']:
            if get_free_gpu_memory() >= self.args['openai']['local']['min_memory']:
                is_use_remote = False
            else:
                is_use_remote = True
        else:
            if psutil.virtual_memory().available >= self.args['openai']['local']['min_memory']:
                is_use_remote = False
            else:
                is_use_remote = True

        if not self.args['openai']['remote']['base_url'] and is_use_remote:
            return None

        if is_use_remote:
            args = self.args['openai']['remote']
            logging.info("使用远程大模型")
        else:
            args = self.args['openai']['local']
            logging.info("使用本地大模型")

        client = OpenAI(api_key=args['api_key'], base_url=args['base_url'])

        response = client.chat.completions.create(
            model=args['model'],
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        content = response.choices[0].message.content
        return content