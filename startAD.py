import sys
import time
import yaml
import random
import logging
import argparse
from GPT import Chat
from utils import notify
from ActivityWatcher import ActivityWatcher

def request():
    with open('config.yaml', 'r') as f:
        args = yaml.safe_load(f)
    
    if args['power']:
        aw = ActivityWatcher(args)
        chat = Chat(aw, args)
        prompt = chat.prompt(args['time']['scope'])
        if prompt:
            # 避免各种网络错误
            try:
                response = chat.chatgpt(prompt)
            except Exception as e:
                logging.error(f"请求出错: {e}")
                return
            if response is None:
                logging.info("跳过此次请求")
                return
            logging.info(response)
            notify(response, args)
        else:
            logging.info("目标未活动")
    else:
        logging.info("您的女友暂时离开了")

def wait():
    with open('config.yaml', 'r') as f:
        args = yaml.safe_load(f)

    # 生成一个正态分布的随机时间间隔（以秒为单位）
    mean = args['time']['delta']['mean']
    std = args['time']['delta']['std']
    sleep_time = random.normalvariate(mean, std)
    sleep_time = max(min(sleep_time, args['time']['delta']['max']),
                        args['time']['delta']['min'], 0)
    
    logging.info(f"下一次运行将在 {sleep_time / 60:.2f} 分钟后")

    # 暂停指定的随机时间
    time.sleep(sleep_time)

def main():
    while True:
        wait()
        request()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', default=False, help='尝试一次请求')
    args = parser.parse_args()

    if args.test:
        request()
    else:
        main()
