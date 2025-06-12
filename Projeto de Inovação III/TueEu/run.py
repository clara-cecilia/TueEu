from app import criar_app 
from flask import Flask 
from config import Config

app = Flask(__name__) 
app.config.from_object(Config)
app = criar_app()



if __name__ == '__main__':
    app.run(debug=True)