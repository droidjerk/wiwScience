import flask_wtf
import wtforms


class SearchForm(flask_wtf.Form):
    imie = wtforms.StringField('imie')
    nazwisko = wtforms.StringField('nazwisko')
    keywords = wtforms.StringField('keywords')
    publikacja = wtforms.StringField('publikacja')
    afilacja = wtforms.StringField('afilacja')
    od = wtforms.DateField('start', format="%Y")
    do = wtforms.DateField('koniec', format="%Y")
