import os


class GatewayEnvironment:
    def __init__(self, name, base_url, secret):
        self.name = name
        self.base_url = base_url
        self.secret = secret


TEST = GatewayEnvironment("test", "https://dev.oreka.vn/", "oreka-tracking-sim-local")
LOCAL = GatewayEnvironment("local", "http://localhost:8888", "oreka-tracking-sim-local")

ENVIRONMENTS = {environment.name: environment for environment in (TEST, LOCAL)}
DEFAULT_ENVIRONMENT = TEST


def current_environment():
    return ENVIRONMENTS.get(os.environ.get("OREKA_SIM_ENV", ""), DEFAULT_ENVIRONMENT)
