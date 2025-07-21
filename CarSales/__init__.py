from flask import Flask

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY="your-secret-key",  
    SQLALCHEMY_TRACK_MODIFICATIONS=False,  
)

from CarSales import logins
from CarSales import routes
