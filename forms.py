from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(message="Name is required"),
        Length(min=2, max=50)
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email")
    ])
    phone = StringField('Phone', validators=[
        DataRequired(message="Phone number is required"),
        Length(min=7, max=20)
    ])
    description  = TextAreaField('Message', validators=[
        DataRequired(message="Message is required"),
        Length(min=10, message="Message should be at least 10 characters")
    ])
    submit = SubmitField('Send Message')


    
