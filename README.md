# Fyers_api
---
Implementation of real-time stock tick data using Fyers WebSocket API and Redis.

## Dependencies
Docker - To run a Redis Timeseries container

Python modules: [fyers-apiv2](https://pypi.org/project/fyers-apiv2/) [Redis](https://pypi.org/project/redis/)

## Installation
`git clone https://github.com/BennyThadikaran/fyers_api.git`

Install Docker using your Linux package manager or from the [Docker website](https://www.docker.com/).

`pip install fyers-apiv2 redis`

Register for a [Fyers account](https://fyers.in/).

Once registered, follow the [instructions here](https://myapi.fyers.in/docs/#tag/App-Creation) to generate 'app id' and 'secret keys'.

> Note: Use `http://localhost:5010` as a redirect URI. You may replace 5010 (default port) with any number between 5000 and 65000. (Make sure to update this in 'config.json')

### Configuration
Open **config.json** in a text editor.

**_Port_** defaults to _5010_. If you used a different port number update it here.

**_server_timeout_** defaults to 120 seconds. By default, the redirect server will wait for 2 mins (120 seconds) for login/authorization before closing the server.

**_credentials_path_** if left blank, looks for 'credentials.json' in the currently installed folder.

> **Warning:** _credentials.json_ stores the app id, secret id, and other confidential details. Do not share this file or upload it online.

> For added security, move the 'credentials.json' file to your home holder or .config. Update the **_credentials_path_** with the full path.

```json
{
   "server_timeout": 120,
   "port": 5010,
   "credentials_path": "",
   "type": "code",
   "grant": "authorization_code",
   "hostname": "localhost"
}
```

Open **credentials.json** in a text editor and add your app id and secret. Leave all other fields blank. They are auto-updated by **auth.py**
```json
{
   "appid": "<YOUR APP ID>",
   "secret": "<YOUR SECRET ID>",
   "auth_code": "",
   "state": "",
   "lastAuth": "",
   "access_token": ""
}
```

Lastly, edit the watchlist.txt to add your symbols. Each symbol is on a separate line.

> All symbols must be in the format as explained in [fyers documentation - Symbol formats](https://myapi.fyers.in/docs/#section/Symbology-Format)

# Usage
Run **auth.py** to get access_token. This will open a web browser to Fyers login. Once authorized, you will be redirected to localhost with the access token stored in 'credentials.json'. The token will be valid till midnight.

`python3 auth.py`

**rt_demo.py** will initialize a docker container with the Redis Timeseries module running in the background. This will also initialize a WebSocket connection steaming real-time tick data into Redis. Every minute the tick data is compacted to 1 min OHLC data.

`python3 rt_demo.py`

Ctrl - C to exit the script

See the below code on how to access 1 min data

```python
import redis
from datetime import datetime

# initialise redis
r = redis.Redis(db=0)

# redis timeseries
ts = r.ts()

ts.get('NSE:HDFCBANK-EQ_O') # get the last 1 min open
(1662454260000, 1496.0)

ts.get('NSE:HDFCBANK-EQ_H') # get the last 1 min high
(1662454260000, 1496.5)

ts.get('NSE:HDFCBANK-EQ_L') # get the last 1 min low
(1662454260000, 1495.9)

ts.get('NSE:HDFCBANK-EQ_C') # get the last 1 min close
(1662454260000, 1496.1)

ts.get('NSE:HDFCBANK-EQ_V') # get the last 1 min volume
(1662454345685, 6.0)

# Get all data within a datetime range
dt = datetime.today()

# start and end time in milliseconds
start = int(datetime(dt.year, dt.month, dt.day, 9, 15).timestamp() * 1000)
end = int(datetime(dt.year, dt.month, dt.day, 15, 30).timestamp() * 1000)

# returns all 1 min open values between 9:15 and 15:30
ts.range(start, end, 'NSE:HDFCBANK-EQ_O')
[(1662454260000, 1496.1), (1662454320000, 1496.8), (1662454380000, 1496.25)]
```




