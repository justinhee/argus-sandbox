import base64
import pickle


def load_session(cookie: str):
    return pickle.loads(base64.b64decode(cookie))
