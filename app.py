import os
from CarSales import app 

if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', '127.0.0.1') 
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(host=HOST, port=PORT, debug=True)