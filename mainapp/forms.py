import flask_wtf
import flask
import wtforms
import wtforms.fields.html5



class SearchForm(flask_wtf.FlaskForm):
    imie = wtforms.StringField('Name')
    nazwisko = wtforms.StringField('Surname')
    keywords = wtforms.StringField('Interests')
    publikacja = wtforms.StringField('Publication')
    afilacja = wtforms.StringField('Institution/University')
    od = wtforms.fields.SelectField('Publication year (From to)')
    do = wtforms.fields.SelectField('to')
    choices = [('3', 'Google Scholar'), ('2', 'ORCiD'), ('1', 'DBLP')]
    engines = wtforms.fields.SelectMultipleField(choices=choices, default=['1', '2', '3'])

    # TODO
    # Multichoice for resources
