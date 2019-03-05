from flask_wtf import FlaskForm

# Filefield -> which allowed different type of file field
# FileAllowed -> which is used for  validation purpose for input data
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo

class ChangePassword(FlaskForm):
    change_password = PasswordField('Password', validators = [DataRequired(), Length(min= 8, max= 20)])
    submit = SubmitField('Submit')