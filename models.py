
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(80), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120))
    birth_date = db.Column(db.Date)
    id_number = db.Column(db.String(20))
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_driver = db.Column(db.Boolean, default=False)
    contracts = db.relationship('Contract', backref='driver', lazy=True)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    id_number = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    contracts = db.relationship('Contract', backref='customer', lazy=True)

class Money(db.Model):
    __tablename__ = 'money'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'))
    total_amount = db.Column(db.Float, nullable=False)
    deposit = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Contract(db.Model):
    __tablename__ = 'contracts'
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(20), unique=True, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    driver_username = db.Column(db.String(80), db.ForeignKey('users.username'), nullable=False)
    pickup_location = db.Column(db.String(200), nullable=False)
    dropoff_location = db.Column(db.String(200), nullable=False)
    contract_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    money = db.relationship('Money', backref='contract', uselist=False)
