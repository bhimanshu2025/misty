
from flask import Flask
import logging
from flasky.config import Config
from flask_swagger_ui import get_swaggerui_blueprint

def create_app(config_class=Config):
    app = Flask(__name__)
    with app.app_context():
        app.config.from_object(Config)
        root = logging.getLogger()
        app.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s:[%(levelname)s]:[%(name)s] : [%(threadName)s] : %(message)s")
        file_handler = logging.FileHandler('/tmp/misty.log')
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        SWAGGER_URL = '/swagger'  # URL for exposing Swagger UI (without trailing '/')
        API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)
        # Call factory function to create our blueprint
        swaggerui_blueprint = get_swaggerui_blueprint(
            SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
            API_URL,
            config={  # Swagger UI config overrides
                'app_name': "misty"
            },
            # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
            #    'clientId': "your-client-id",
            #    'clientSecret': "your-client-secret-if-required",
            #    'realm': "your-realms",
            #    'appName': "your-app-name",
            #    'scopeSeparator': " ",
            #    'additionalQueryStringParams': {'test': "hello"}
            # }
        )
        app.register_blueprint(swaggerui_blueprint)
        from flasky.main.routes import main
        app.register_blueprint(main)
        return app 