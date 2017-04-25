import flask_wtf
import wtforms
import wtforms.fields.html5


class SearchForm(flask_wtf.FlaskForm):
    imie = wtforms.StringField('Name')
    nazwisko = wtforms.StringField('Surname')
    keywords = wtforms.StringField('Interests')
    publikacja = wtforms.StringField('Publication')
    afilacja = wtforms.StringField('Institution/University')
    #od = wtforms.fields.html5.DateField('Publication dates (from)', format="%Y")
    od = wtforms.fields.SelectField('Publication year (From)', coerce=int)
    do = wtforms.fields.SelectField('Publication year (To)', coerce=int)
    datesearch = wtforms.fields.BooleanField(label="Deactivate publication date filtering", default=True)
    # TODO
    # Multichoice for resources
