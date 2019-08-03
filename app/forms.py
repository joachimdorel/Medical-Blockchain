from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import Actor

class LoginForm(FlaskForm):
    actor_name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    # Actor
    actor_name = StringField('Name',  validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[])
    manufacturer = BooleanField('Manufacturer')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])

    # Adress
    street = StringField('Street', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State')
    zip_code = StringField('ZIP Code', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])

    submit = SubmitField('Register')

    def validate_name(self, name):
        actor = Actor.query.filter_by(actor_name=actor_name.data).first()
        if actor is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        actor = Actor.query.filter_by(email=email.data).first()
        if actor is not None:
            raise ValidationError('Please use a different email address.')

class MedicineForm(FlaskForm):
    medicine_name = StringField('Name', validators=[DataRequired()])
    gtin = StringField('GTIN', validators=[DataRequired()])
    submit = SubmitField('Add new medicine')

class BatchForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired()])
