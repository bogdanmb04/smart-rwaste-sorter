from random import randint
from flask import Flask, request
from PIL import Image
from model import get_saved_model, get_class_labels

app = Flask(__name__)
model = get_saved_model()


@app.route('/')
def home():
    return 'Welcome!'


@app.route('/random')
def get_random():
    return str(randint(1, 3))


@app.route('/hello')
def hello():
    return 'Hello Arduino!'


def get_image():
    # go to camera web server and grab image
    ...


@app.route("/class", methods=['POST'])
def classify_image() -> int:
    return 0



def main():
    app.run(debug=True, host='localhost', port=5000)

if __name__ == '__main__':
    main()
