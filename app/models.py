from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Actor(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_name = db.Column(db.String(120), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    manufacturer = db.Column(db.Boolean, unique=False)

    medicines = db.relationship('Medicine', backref='manufacturer', lazy='dynamic')
    adresses = db.relationship('Adress', backref='actor', lazy='dynamic')

    def __repr__(self):
        return '<Actor {}>'.format(self.actor_name)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Medicine(db.Model):
    medicine_id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(140), index=True, unique=True)
    GTIN = db.Column(db.String(14), unique=True)

    manufacturer_id = db.Column(db.Integer, db.ForeignKey('actor.id'))

    batchs = db.relationship('Batch', backref='medicine', lazy='dynamic')

    def __repr__(self):
        return '<Medicine {}>'.format(self.medicine_name)

class Batch(db.Model):
    batch_id = db.Column(db.Integer, primary_key=True, index=True)
    parent_batch_id = db.Column(db.Integer)
    exp_date = db.Column(db.String(8))
    quantity = db.Column(db.Integer)

    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.medicine_id'))

    def __repr__(self):
        return '<Batch {}>'.format(self.batch_id)

class Adress(db.Model):
    adress_id = db.Column(db.Integer, primary_key=True)
    street = db.Column(db.String(256))
    city = db.Column(db.String(128))
    state = db.Column(db.String(128))
    zip_code = db.Column(db.String(16), index=True)
    country = db.Column(db.String(128))

    id =  db.Column(db.Integer, db.ForeignKey('actor.id'))

    def __repr__(self):
        return '<Adress {}>'.format(self.street)

@login.user_loader
def load_actor(id):
    return Actor.query.get(int(id))
