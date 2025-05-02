from random import randint

from flask import Flask

app = Flask(__name__)


@app.route('/')
def home():
    return 'Welcome!'


@app.route('/random')
def get_random():
    return str(randint(1, 3))


@app.route('/hello')
def hello():
    return 'Hello Arduino!'


def main():
    app.run(debug=True, host='192.168.74.175', port=8000)


if __name__ == '__main__':
    main()
