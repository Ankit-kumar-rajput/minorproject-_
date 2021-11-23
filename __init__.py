from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, migrate


app=Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/whatsapp'
app.debug=False
db=SQLAlchemy(app)
migrate=Migrate(app,db)
        

from Whatsapp.main import main as main_blueprint
app.register_blueprint(main_blueprint)


