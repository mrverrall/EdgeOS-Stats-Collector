from datetime import datetime
import asyncio
import json
import requests
import ssl
import threading
import time
import urllib3
import websockets

urllib3.disable_warnings()


class Session():

    def __init__(self, server: str, credetials: dict, heartbeat_interval=None):
        self._base_uri = f'https://{server}/'
        self._heartbeat_uri = f'{self._base_uri}/api/edge/heartbeat.json'
        self._creds = credetials

        self._last_heartbeat = None
        self._observers = []
        self._session_id = None
        self._session = None

        if isinstance(heartbeat_interval, int):
            self._heartbeat_interval = heartbeat_interval
        else:
            self._heartbeat_interval = 5

    def start_session(self):
        "Start an session ephemeral session that will not re-establish, raises an exception on fail"
        self._session = self._get_new_session()

        if self._session_id:
            t = threading.Thread(target=self._heartbeat)
            t.start()
        else:
            raise Exception('Unable to establish session')

    def start_persistant_session(self):
        "Start a session resistant to error which will continue to retry regardless"
        t = threading.Thread(target=self._persistant_session)
        t.start()

    def _persistant_session(self):
        "Check for session every second and try to create a new one if needed"
        while True:
            try:
                if not self.session_id:
                    self.start_session()
            except Exception:
                pass

            time.sleep(1)

    def _get_new_session(self) -> requests.session:
        "Authenticate a new session with an EdgeOS device"
        session = requests.session()

        # attemp an auth request
        ar = session.post(self._base_uri, data=self._creds, verify=False, allow_redirects=False)

        if ar.status_code == 303:
            self.session_id = ar.cookies.get('PHPSESSID')
            return session

        return None

    def _destroy_session(self):
        "Destroy any existing session properties"
        self.session_id = None
        self._last_heartbeat = None

    def _heartbeat(self) -> bool:
        "Send a keepalive heartbeat to the existing session and tear it down if it ends"
        while True:
            try:
                self._last_heartbeat = self._session.get(self._heartbeat_uri, verify=False)
                if self._last_heartbeat.status_code != 200:
                    raise Exception(f'Last heartbeat: {self._last_heartbeat.status_code}')
            except ConnectionError:
                # don't panic, try and reuse the session when this come back...
                pass
            except Exception:
                # most likely the session has expired, our job is done.
                self._destroy_session()
                return

            time.sleep(self._heartbeat_interval)

    @property
    def last_heartbeat(self) -> int:
        "The status code returned from the last heartbeat"
        return self._last_heartbeat

    @property
    def session_id(self) -> str:
        "Current session_id"
        return self._session_id

    @session_id.setter
    def session_id(self, value):
        "This should not be set externally"
        self._session_id = value
        asyncio.run(self.notitify_subscribers())

    async def notitify_subscribers(self):
        if self._session_id:
            for callback in self._observers:
                await callback(self._session_id)

    def subscribe_to_session_id(self, callback):
        self._observers.append(callback)


class WS():

    def __init__(self, server: str, credetials: dict, subscriptions: list, callback=None):
        self._server = server
        self._websocket = None
        self._callback = callback
        self._subscriptions = subscriptions

        self._session = Session(server, credetials)
        self._session.start_persistant_session()
        self._session.subscribe_to_session_id(self._subscribe_to_ws_stats)

        self._websocket = None

    async def _subscribe_to_ws_stats(self, session_id):

        if self._websocket and not self._websocket.closed and self._session.session_id:
            subs = ",".join([f'{{"name":"{sub}"}}' for sub in self._subscriptions])
            payload = f'{{"SUBSCRIBE":[{subs}],"UNSUBSCRIBE":[],"SESSION_ID":"{self._session.session_id}"}}'
            payload = f"{len(payload)}\n{payload}"

            await self._websocket.send(payload)

    async def collect_edgeos_metrics(self):

        ws_uri = f'wss://{self._server}/ws/stats'
        while True:
            try:
                async with websockets.connect(ws_uri, ssl=ssl_unverified()) as self._websocket:
                    await self._session.notitify_subscribers()
                    async for message in self._websocket:
                        try:
                            if j_msg := json.loads(message[message.find('{'):]):
                                if self._callback:
                                    self._callback(j_msg)
                                print(f"{datetime.now()}:0 OK")
                        except Exception:
                            pass
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"{datetime.now()}:4 Connection was closed {e}")
            except Exception as e:
                print(f"{datetime.now()}:1 {e}")


def ssl_unverified() -> ssl.SSLContext:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = False

    return ssl_context
