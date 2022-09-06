import redis
from fyers_api.Websocket import ws
from subprocess import run
from os.path import dirname, realpath
from json import load
import ctypes



def generateRedisKey(sym):
    try:
        ts.create(sym, retention_msecs=300000)
    except redis.exceptions.ResponseError as e:
        return

    tick_vol = sym + '_TV'
    ts.create(tick_vol)

    _open, high, low, close, vol = tuple(f'{sym}_{x}' for x in 'OHLCV')

    ts.create(_open)
    ts.create(high)
    ts.create(low)
    ts.create(close)
    ts.create(vol)

    ts.createrule(sym, _open, 'first', bucket_size_msec=60000)
    ts.createrule(sym, high, 'max', bucket_size_msec=60000)
    ts.createrule(sym, low, 'min', bucket_size_msec=60000)
    ts.createrule(sym, close, 'last', bucket_size_msec=60000)
    ts.createrule(tick_vol, vol, 'sum', bucket_size_msec=60000)


def process_tick(msg):
    sym = msg[0]['symbol']
    vol = sym + '_V'

    for tick in msg[0]['market_pic']:
        ts.add(sym, '*', tick['price'])
        ts.add(vol, '*', tick['qty'])


# run docker.
# Returns long code of which first 12 digits is container id
# used to stop the container
docker = run(['/usr/bin/docker', 'run',  '-d', '-p', '6379:6379',
             '-it', '--rm', 'redislabs/redistimeseries'], capture_output=True)

# Initialise redis
r = redis.Redis(db=0)
ts = r.ts()

basePath = dirname(realpath(__file__))

# load config and credentials
with open(f'{basePath}/config.json') as f:
    config = load(f)

auth_fpath = config['credentials_path']

# By default, we look for credentials.json in script folder
if auth_fpath == '':
    auth_fpath = f'{basePath}/credentials.json'

try:
    with open(auth_fpath) as f:
        auth = load(f)
except FileNotFoundError:
    exit(f'File not found: {auth_fpath}')

# load the symbol list
with open(f'{basePath}/watchlist.txt') as f:
    symList = f.read().strip().split('\n')

for sym in symList:
    generateRedisKey(sym)

# (appId:access_token)
access_token = f"{auth['appid']}:{auth['access_token']}"


try:
    fs = ws.FyersSocket(access_token=access_token,
                        run_background=False, log_path=f'{basePath}/log')

    fs.websocket_data = process_tick

    fs.subscribe(symbol=symList, data_type="symbolData")
    fs.keep_running()


except KeyboardInterrupt:
    # CTRL - C to exit
    fs.unsubscribe(symbol=symList)
    fs.stop_running()

    run(['/usr/bin/docker', 'stop', docker.stdout.decode()[:12]])

    threadId = ctypes.c_long(fs.t.ident)

    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        threadId, ctypes.py_object(SystemExit))

    print('\nShutdown')
