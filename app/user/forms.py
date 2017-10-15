# -*- coding:utf-8 -*-
# __author__ = 'Shanks'

from flask_wtf import FlaskForm
from wtforms import StringField, FileField, TextAreaField, SubmitField, SelectField
from wtforms.validators import Regexp, ValidationError
from werkzeug.utils import secure_filename

class EditProfileForm(FlaskForm):
    user_image = FileField('上传头像')
    nickname = StringField('昵称')
    school = StringField('学校')
    campus = StringField('校区')
    faculty = StringField('院系')
    gender = SelectField('性别', choices=[(0, '男'), (1, '女')])
    about_me = TextAreaField('介绍下自己..')
    submit = SubmitField('提交')

    def validate_user_image(self, field):
        image_rep = ('.jpg', '.png', 'bmp', 'jpg','png','tiff','gif','pcx','tga','exif','fpx','svg')
        filename = secure_filename(field.data.filename)
        if field.data:
            if not filename.endswith(image_rep):
                raise ValidationError("Don't support this image format!")




