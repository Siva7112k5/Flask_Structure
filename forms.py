from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, RadioField, BooleanField  # Add BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')  # ← ADD THIS LINE
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Register')

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
    images = RadioField('images')  # You may need to adjust this based on your needs
    
    submit = SubmitField('Submit Review')