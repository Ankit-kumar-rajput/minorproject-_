
from sqlalchemy.orm import query
from Whatsapp import db 
from datetime import datetime


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    file=db.Column(db.Text)
    file_extension=db.Column(db.Text)
    file_name=db.Column(db.Text)
    contact= db.relationship('Content', backref='author', lazy=True)
    attachment= db.relationship('Attachment', backref='Attachment', lazy=True)

class Content(db.Model):
    sno=db.Column(db.Integer,primary_key=True)
    file_id=db.Column(db.Integer,db.ForeignKey('history.id'),nullable=False)
    name=db.Column(db.Text)
    number=db.Column(db.BigInteger())
    
    message=db.Column(db.Text)
    
    status=db.Column(db.Text , default='Null')
    photo_status=db.Column(db.Text,default='Null')
    document_status=db.Column(db.Text,default='Null')

class Attachment(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    file_id=db.Column(db.Integer,db.ForeignKey('history.id'),nullable=False)
    photo_name=db.Column(db.Text,default='Null')    
    document_name=db.Column(db.Text,default='Null')
    
    
 

    

    
     