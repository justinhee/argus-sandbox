import yaml


def load_config(text: str):
    return yaml.load(text, Loader=yaml.Loader)
