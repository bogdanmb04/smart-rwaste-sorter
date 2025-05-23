import numpy as np
import requests
from detectron2.data import MetadataCatalog
from detectron2.data.datasets import register_coco_instances
from detectron2.utils.visualizer import Visualizer
from flask import Flask, request
from PIL import Image
from model import get_saved_model, get_class_labels
import cv2
from io import BytesIO

app = Flask(__name__)
model = get_saved_model()
register_coco_instances("trashnet_test", {'thing_classes': get_class_labels()}, "images/test/_annotations.coco.json", "images/test")
test_metadata = MetadataCatalog.get("trashnet_test")

@app.route('/')
def home():
    return 'Welcome!'


def get_image() -> np.ndarray:
    # go to camera web server and grab image
    esp_url: str = "http://192.168.139.12/cam-hi.jpg"
    resp = requests.get(esp_url, timeout=10)
    resp.raise_for_status()
    image = Image.open(BytesIO(resp.content))
    img_arr = np.asarray(image)
    return img_arr


@app.route("/class", methods=['GET'])
def classify_image():
    img: np.ndarray  = get_image()
    out = model(img)
    # only here for quick testing, not meant to actually be displayed!
    # v = Visualizer(img[:,:,::-1], metadata=test_metadata)
    # v = v.draw_instance_predictions(out["instances"].to("cpu"))
    # cv2.imshow("image", v.get_image())
    labels = get_class_labels()
    if len(out['instances'].pred_classes) != 0:
        class_idx = out['instances'].pred_classes[0]
        return labels[class_idx]
    else:
        return labels[0]


def main():
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
