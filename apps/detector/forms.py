from ast import Sub

from flask_wtf.form import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Email, Length


class SearchBookForm(FlaskForm):
    title = StringField(
        "タイトル",
        validators=[
            DataRequired("タイトルを指定してください。"),
        ],
    )
    authors = StringField(
        "著者",
    )
    submit = SubmitField("検索")


class RegistrateForm(FlaskForm):
    submit = SubmitField("登録")


class SearchLibraryForm(FlaskForm):
    pref = StringField(
        "都道府県",
        validators=[
            DataRequired("都道府県を指定してください。"),
        ],
    )
    city = StringField(
        "市区町村",
        validators=[
            DataRequired("市区町村を指定してください。"),
        ],
    )
    submit = SubmitField("検索")


class StocktakeForm(FlaskForm):
    submit = SubmitField("蔵書検索")


class DeleteForm(FlaskForm):
    submit = SubmitField("削除")
