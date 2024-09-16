from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, IntegerField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length
from models import Admin
from flask_wtf import CSRFProtect

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        admin = Admin.query.filter_by(username=username.data).first()
        if admin:
            raise ValidationError('Username is already taken. Please choose a different one.')
        
class BookForm(FlaskForm):
    picture = FileField('Picture')  # Allow image upload
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    isbn = IntegerField('Isbn', validators=[DataRequired()])
    genre = StringField('Genre', validators=[DataRequired()])
    description = TextAreaField('Description')
    publication_year = IntegerField('Publication Year', validators=[DataRequired()])
    available_quantity = IntegerField('Available Quantity', validators=[DataRequired()])
    total_quantity = IntegerField('Total Quantity', validators=[DataRequired()])
    shelf = StringField('Shelf', validators=[DataRequired()])
    submit = SubmitField('Add Book')

class EditBookForm(FlaskForm):
    picture = FileField('Update Picture')  # Allow image upload
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    isbn = IntegerField('Isbn', validators=[DataRequired()])
    genre = StringField('Genre', validators=[DataRequired()])
    description = TextAreaField('Description')
    publication_year = IntegerField('Publication Year', validators=[DataRequired()])
    available_quantity = IntegerField('Available Quantity', validators=[DataRequired()])
    total_quantity = IntegerField('Total Quantity', validators=[DataRequired()])
    shelf = StringField('Shelf', validators=[DataRequired()])
    submit = SubmitField('Update Book')

class MRegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class MLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EbookUploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    file = FileField('E-book', validators=[DataRequired()])
    submit = SubmitField('Upload')