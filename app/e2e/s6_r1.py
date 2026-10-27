import base64
import json


def load_session(cookie: str):
    return json.loads(base64.b64decode(cookie))
