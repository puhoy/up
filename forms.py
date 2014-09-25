from flask.ext.wtf import Form
from wtforms import TextField, validators, StringField
from wtforms.validators import Required

class CommentForm(Form):
    username = StringField('username', [validators.Length(max=40)], default='Anonymous')
    text = TextField('text', validators = [Required()])