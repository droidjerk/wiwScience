from mainapp import app
import config

app.secret_key = config.SECRET
app.config['SECRET_KEY'] = config.SECRET
app.run()
