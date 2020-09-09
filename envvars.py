import os

# Import and initialize environment variable values
API_PORT = os.environ['API_PORT'] if 'API_PORT' in os.environ else 8080
API_BASEPATH = os.environ['API_BASEPATH'] if 'API_BASEPATH' in os.environ else '/api/v1'
API_DOMAIN = os.environ['API_DOMAIN'] if 'API_DOMAIN' in os.environ else 'localhost'
API_PROTOCOL = os.environ['API_PROTOCOL'] if 'API_PROTOCOL' in os.environ else 'http'