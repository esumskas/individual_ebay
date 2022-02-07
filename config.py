import yaml


def load_config():
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg


def load_credentials():
    with open("credentials.yml", 'r') as ymlfile:
        credentials = yaml.safe_load(ymlfile)
    return credentials
