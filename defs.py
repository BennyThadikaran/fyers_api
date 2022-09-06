from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen
from urllib.parse import urlparse, parse_qs
from fyers_api import accessToken
from os.path import dirname, realpath, getmtime
from secrets import token_urlsafe
from json import load, dump
from datetime import datetime
from time import sleep
import webbrowser


basePath = dirname(realpath(__file__))
config_file = f'{basePath}/config.json'
dt = datetime.combine(datetime.today(), datetime.min.time()).isoformat()

with open(f'{basePath}/config.json') as f:
    config = load(f)

auth_fpath = config['credentials_path']

if auth_fpath == '':
    auth_fpath = f'{basePath}/credentials.json'

try:
    with open(auth_fpath) as f:
        auth = load(f)
except FileNotFoundError:
    exit(f'{auth_fpath} does not exist')

if auth['lastAuth'] == dt:
    exit('Authenthication Done.')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        dct = parse_qs(urlparse(self.path).query)

        self.send_response(200)
        self.end_headers()

        if not dct:
            # No query parameters we respond 200 OK and close
            # User likely took too long to authorise
            print('Timeout: Authorization failed. Please try again')
            return

        if dct['s'][0] != 'ok':
            msg = f"ERROR: {dct['code'][0]}, {dct['message'][0]}"

            self.wfile.write(bytes(msg, "utf-8"))
        else:
            auth['auth_code'] = dct['auth_code'][0]
            auth['state'] = dct['state'][0]
            auth['lastAuth'] = dt

            with open(auth_fpath, 'w') as f:
                dump(auth, f, indent=3)

            msg = 'Success: Auth Code generated'

            self.wfile.write(bytes(msg, "utf-8"))


def checkErrors(response):
    if response['s'] == 'ok':
        return

    exit(f"ERROR: {response['code']}, {response['message']}")


def runServer():
    host = config['hostname']
    port = config['port']
    webServer = HTTPServer((host, port), Handler)
    print(f'Server http://{host}:{port}')

    webServer.handle_request()

    webServer.server_close()
    print('\nServer closed')


def authorise():
    timestamp = getmtime(auth_fpath)

    state = token_urlsafe()

    redirect_uri = f"http://{config['hostname']}:{config['port']}/"

    # Start authenthication
    session = accessToken.SessionModel(client_id=auth['appid'],
                                       secret_key=auth['secret'],
                                       redirect_uri=redirect_uri,
                                       response_type=config['type'],
                                       grant_type=config['grant'],
                                       state=state,
                                       nonce=token_urlsafe())

    token_url = session.generate_authcode()

    webbrowser.open(token_url, new=1)

    # Wait for Authenthication
    secondsToWait = config['server_timeout']

    while secondsToWait > 0:
        sleep(1)

        secondsToWait -= 1

        if getmtime(auth_fpath) > timestamp:
            break

    if secondsToWait == 0:
        urlopen(redirect_uri)
        return

    with open(auth_fpath) as f:
        new_auth = load(f)

    if state != new_auth['state']:
        exit('State mismatch. Reset account password if problem persists.')

    session.set_token(new_auth['auth_code'])

    res = session.generate_token()

    checkErrors(res)

    new_auth['access_token'] = res['access_token']

    with open(auth_fpath, 'w') as f:
        dump(new_auth, f, indent=3)

    print('Authenthication Success')

