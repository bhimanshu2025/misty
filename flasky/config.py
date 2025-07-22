import os

class Config:
    print("loading config")
    ENVIRONMENT = os.environ.get('ENVIRONMENT') or "DEV"
    VERSION = "v1.0"
    BUILD = "v1.0"
    
