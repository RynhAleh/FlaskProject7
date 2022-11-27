from flask import Flask
import gettext
gettext.install('messages', './translations', unicode=True)

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
