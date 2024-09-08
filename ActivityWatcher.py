import time
import requests

class ActivityWatcher:
    def __init__(self, args) -> None:
        self.host = args['ActivityWatch']['host']+'/'
        self.data = {
            'query': [
                f'events = flood(query_bucket(find_bucket(\"{args['ActivityWatch']['window_bucket']}\")));',
                f'not_afk = flood(query_bucket(find_bucket(\"{args['ActivityWatch']['afk_bucket']}\")));',
                'not_afk = filter_keyvals(not_afk, \"status\", [\"not-afk\"]);',
                'browser_events = [];',
                'audible_events = filter_keyvals(browser_events, \"audible\", [true]);',
                'not_afk = period_union(not_afk, audible_events);',
                'events = filter_period_intersect(events, not_afk);',
                'events = categorize(events, null);',
                'title_events = sort_by_duration(merge_events_by_keys(events, [\"app\", \"title\"]));',
                'app_events   = sort_by_duration(merge_events_by_keys(title_events, [\"app\"]));',
                'cat_events   = sort_by_duration(merge_events_by_keys(events, [\"$category\"]));',
                'app_events  = limit_events(app_events, 100);',
                'title_events  = limit_events(title_events, 100);',
                'duration = sum_durations(events);',
                'browser_events = split_url_events(browser_events);',
                'browser_urls = merge_events_by_keys(browser_events, [\"url\"]);',
                'browser_urls = sort_by_duration(browser_urls);',
                'browser_urls = limit_events(browser_urls, 100);',
                'browser_domains = merge_events_by_keys(browser_events, [\"$domain\"]);',
                'browser_domains = sort_by_duration(browser_domains);',
                'browser_domains = limit_events(browser_domains, 100);',
                'browser_duration = sum_durations(browser_events);',
                ('RETURN = {\n        \"window\": {\n            \"app_events\": app_events,\n            '
                '\"title_events\": title_events,\n            \"cat_events\": cat_events,\n            '
                '\"active_events\": not_afk,\n            \"duration\": duration\n        },\n        '
                '\"browser\": {\n            \"domains\": browser_domains,\n            \"urls\": browser_urls,\n            '
                '\"duration\": browser_duration\n        }\n    };')
            ],
            'timeperiods': None
        }
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.args = args
        self.is_activitywatch_alive()

    def is_activitywatch_alive(self):
        # 检查ActivityWatch是否在线，尝试连接三次
        for _ in range(3):
            try:
                response = requests.get(self.host, timeout=3)
                if response.status_code == 200:
                    return
            except Exception as e:
                time.sleep(5)
                continue
        raise Exception("ActivityWatch未响应")
    
    def set_rules(self):
        setting_url = self.host + 'api/0/settings'
        response = requests.get(setting_url, headers=self.headers).json()
        data = response['classes']
        settings = [[item['name'], item['rule']] for item in data]
        settings = str(settings).replace('\'', '\"').replace("True", "true").replace("False", "false")
        self.data['query'][7] = f'events = categorize(events, {settings});'

        if "always_active_pattern" in response:
            extra_codes = [
                f'not_treat_as_afk = filter_keyvals_regex(events, \"app\", \"{response['always_active_pattern']}\");',
                'not_afk = period_union(not_afk, not_treat_as_afk);',
                f'not_treat_as_afk = filter_keyvals_regex(events, \"title\", \"{response['always_active_pattern']}\");',
                'not_afk = period_union(not_afk, not_treat_as_afk);'
            ]
            self.data['query'] = self.data['query'][:3] + extra_codes + self.data['query'][3:]

    def get_data(self, timeperiods=None):
        self.data['timeperiods'] = [timeperiods]
        query_url = self.host + 'api/0/query'
        response = requests.post(query_url, json=self.data, headers=self.headers)
        data = response.json()[0]['window']
        if data['duration'] > self.args['time']['min_duration_alive']:
            return data
        else:
            return None

    def top_events(self, events_datas, type):
        def format_name(name, type):
            if type == 'app':
                return name['app']
            elif type == 'cat':
                return '->'.join(name['$category'])
            elif type == 'title':
                return name['title']
            else:
                return name
        events = [f'- {format_name(item['data'], type)}: 耗时 {item['duration']/60:.1f} min' 
                  for item in events_datas[type+'_events']
                  if item['duration'] > self.args['time']['min_time_event']]
        return '\n'.join(events[:self.args['ActivityWatch']['num_top']])