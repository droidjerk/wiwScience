from mainapp import app
import config

app.secret_key = config.SECRET
app.run()
