from mainapp import app
import config

app.secret_key = config.SECRET
app.config['SECRET_KEY'] = config.SECRET

if __name__ == "__main__":
    app.run()
