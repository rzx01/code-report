import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
    GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
