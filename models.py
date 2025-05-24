from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Date, Time, Boolean, ForeignKey

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(String(80), primary_key=True)
    email = db.Column(String(120), unique=True, nullable=False)
    password = db.Column(String(120), nullable=False)
    full_name = db.Column(String(120))
    birth_date = db.Column(Date)
    id_number = db.Column(String(20))
    phone = db.Column(String(15))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    is_driver = db.Column(Boolean, default=False)
    contracts = db.relationship('Contract', backref='driver', lazy=True)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(120), nullable=False)
    id_number = db.Column(String(20), unique=True, nullable=False)
    phone = db.Column(String(15), nullable=False)
    contracts = db.relationship('Contract', backref='customer', lazy=True)

class Money(db.Model):
    __tablename__ = 'money'
    id = db.Column(Integer, primary_key=True)
    contract_id = db.Column(Integer, ForeignKey('contracts.id'))
    total_amount = db.Column(Float, nullable=False)
    deposit = db.Column(Float, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
class Contract(db.Model):
    __tablename__ = 'contracts'
    id = db.Column(Integer, primary_key=True)
    contract_number = db.Column(String(20), unique=True, nullable=True)
    customer_id = db.Column(Integer, ForeignKey('customers.id'), nullable=False)
    driver_username = db.Column(String(80), ForeignKey('users.username'), nullable=False)
    pickup_location = db.Column(String(200), nullable=False)
    dropoff_location = db.Column(String(200), nullable=False)
    contract_date = db.Column(Date, nullable=False)
    pickup_time = db.Column(Time, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    money = db.relationship('Money', backref='contract', uselist=False)
