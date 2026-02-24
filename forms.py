from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import re

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Register')

# ADD THIS NEW FORM
class ReviewForm(FlaskForm):
    rating = RadioField('Rating', choices=[
        ('5', '★★★★★ Excellent'),
        ('4', '★★★★☆ Good'),
        ('3', '★★★☆☆ Average'),
        ('2', '★★☆☆☆ Poor'),
        ('1', '★☆☆☆☆ Terrible')
    ], coerce=int, validators=[DataRequired()])
    
    comment = TextAreaField('Your Review', validators=[
        DataRequired(),
        Length(min=10, max=500, message='Review must be between 10 and 500 characters')
    ])
    
    submit = SubmitField('Submit Review')


from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, RadioField, MultipleFileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

class ReviewForm(FlaskForm):
    rating = RadioField('Rating', choices=[
        ('5', '★★★★★ Excellent'),
        ('4', '★★★★☆ Good'),
        ('3', '★★★☆☆ Average'),
        ('2', '★★☆☆☆ Poor'),
        ('1', '★☆☆☆☆ Terrible')
    ], coerce=int, validators=[DataRequired()])
    
    comment = TextAreaField('Your Review', validators=[
        DataRequired(),
        Length(min=10, max=500, message='Review must be between 10 and 500 characters')
    ])
    
    # NEW: Multiple image upload field
    images = MultipleFileField('Add Photos (Optional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!'),
        FileSize(max_size=5 * 1024 * 1024, message='Each image must be less than 5MB')
    ])
    
    submit = SubmitField('Submit Review')    