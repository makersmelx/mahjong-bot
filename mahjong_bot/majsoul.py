import random
from sys import stderr
import requests

URL_BASE = 'https://game.maj-soul.com/1/'
MAX_ATTEMPT_PER_SERVER = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "If-Modified-Since": "0",
    "Referer": URL_BASE,
    "sec-ch-ua": '"Chromium";v="100", "Google Chrome";v="100"',
    "sec-ch-ua-platform": "Windows",
}

class Majsoul:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.set_requests_session()

    def set_requests_session(self):
        self.session.headers= HEADERS

    # Expected to be hard-coded according to mahjong soul api (2022-07-14)
    # notify the author if this part throws Error
    def get_majsoul_resource(self, path: str):
        url = URL_BASE + path
        return self.session.get(url).json()

    def connect(self):
        # Parts below are hard-coded according to mahjong soul api (2022-07-14)
        # notify the author if this part throws KeyError
        try:
            ws_scheme = 'wss'
            version = self.get_majsoul_resource("version.json")
            resversion = self.get_majsoul_resource('resversion{}.json'.format(version['version']))
            protobuf_version = resversion['res']["res/proto/liqi.json"]['prefix']
            protobuf_schema = self.get_majsoul_resource('{}/res/proto/liqi.json'.format(protobuf_version))
            config = self.get_majsoul_resource('{}/config.json'.format(resversion['res']['config.json']['prefix']))
            ip_config = [x for x in config['ip'] if x['name'] == 'player'][0]
            # a list of urls where we can request for game server information
            request_game_server_url_list = ip_config['region_urls']
        except KeyError as e:
            print(e, stderr)
            print("Majsoul api may have changed. Please notify the author.")

        last_error: Exception = None

        for attempt in range(len(request_game_server_url_list) * MAX_ATTEMPT_PER_SERVER):
            request_game_server_url = request_game_server_url_list[attempt // MAX_ATTEMPT_PER_SERVER]['url']
            # the final url where we request for game server info
            # javascript float type has 17 digits after the dot.
            request_game_server_url \
                += "?service=ws-gateway&protocol=ws&ssl=true&rv=" \
                + str(random.random())[2:].ljust(17, '0');

            try:
                game_server_info = self.session.get(request_game_server_url).json()
                print(game_server_info)
                # check maintenance
                if 'maintenance' in game_server_info:
                    print("Majsoul is in maintenance")
                    return

                game_server_url = random.choice(game_server_info["servers"])

                if 'maj-soul' not in game_server_url:
                    game_server_url += '/gateway'
                print(game_server_url)

                break
            except Exception as e:
                last_error = e
                print(e, stderr)
                continue
        # failed to fetch game servers
        if last_error:
            print(e, stderr)
            return last_error


if __name__ == '__main__':
    majsoul = Majsoul()
    majsoul.connect()