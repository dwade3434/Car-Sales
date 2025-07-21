from flask import Flask

app = Flask(__name__)

# Optional: Load configuration settings (if you plan to use configuration files or environment variables)
app.config.from_mapping(
    SECRET_KEY="your-secret-key",  # Replace with a secure random key in production
    SQLALCHEMY_TRACK_MODIFICATIONS=False,  # Useful if using SQLAlchemy
)

from CarSales import logins
from CarSales import routes
