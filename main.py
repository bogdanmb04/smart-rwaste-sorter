import threading
import time
from io import BytesIO
from typing import Optional, Tuple

import cv2
import numpy as np
import requests
from PIL import Image
from detectron2.data import MetadataCatalog
from detectron2.data.datasets import register_coco_instances
from detectron2.utils.visualizer import Visualizer
from flask import Flask, Response, stream_with_context, request, jsonify

CAMERA_URL = "http://192.168.15.12/"
SNAPSHOT_URL = None

from model import get_saved_model, get_class_labels

register_coco_instances("trashnet_test", {'thing_classes': get_class_labels()}, "images/test/_annotations.coco.json", "images/test")
TEST_METADATA = MetadataCatalog.get("trashnet_test")

class FrameGrabber(threading.Thread):

    def __init__(self, url: str, snapshot_url: Optional[str] = None):
        super().__init__(daemon=True)
        self.url = url
        self.snapshot_url = snapshot_url or url
        self._frame: Optional[bytes] = None
        self._frame_id = 0
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._stop = threading.Event()
        self.session = requests.Session()

    def stop(self):
        self._stop.set()

    def set_frame(self, jpeg_bytes: bytes):
        with self._cond:
            self._frame = jpeg_bytes
            self._frame_id += 1
            self._cond.notify_all()

    def get_frame(self) -> Tuple[Optional[bytes], int]:
        with self._lock:
            return self._frame, self._frame_id

    def wait_for_next(self, last_id: int, timeout: float = 5.0) -> Tuple[Optional[bytes], int]:

        with self._cond:
            if self._frame_id == last_id:
                self._cond.wait(timeout=timeout)
            return self._frame, self._frame_id

    def run(self):
        while not self._stop.is_set():
            try:
                r = self.session.get(self.url, stream=True, timeout=8)
                content_type = r.headers.get("Content-Type", "")
                if "multipart" in content_type.lower() or "mjpeg" in content_type.lower():
                    buffer = b""
                    for chunk in r.iter_content(chunk_size=1024):
                        if self._stop.is_set():
                            break
                        if not chunk:
                            continue
                        buffer += chunk
                        start = buffer.find(b"\xff\xd8")
                        end = buffer.find(b"\xff\xd9")
                        if start != -1 and end != -1 and end > start:
                            jpg = buffer[start:end+2]
                            buffer = buffer[end+2:]
                            self.set_frame(jpg)
                    r.close()
                else:
                    # Not a multipart stream: fall back to polling snapshot endpoint
                    r.close()
                    self._poll_snapshots()
            except Exception:
                # On any error, fallback to polling the snapshot URL for resilience
                try:
                    self._poll_snapshots()
                except Exception:
                    time.sleep(1)

    def _poll_snapshots(self):
        # Try snapshot endpoint repeatedly (useful for cameras that provide single-image snapshots)
        while not self._stop.is_set():
            try:
                r = self.session.get(self.snapshot_url, timeout=6)
                if r.status_code == 200:
                    ct = r.headers.get("Content-Type", "")
                    # accept jpeg content or raw jpeg bytes
                    if "jpeg" in ct.lower() or r.content.startswith(b"\xff\xd8"):
                        self.set_frame(r.content)
                r.close()
            except Exception:
                # stop polling and return to top-level to attempt MJPEG
                break
            # small sleep; tune as needed (0.1-0.5s)
            time.sleep(0.15)


# ----------------- Flask app -----------------
app = Flask(__name__)
model = get_saved_model()

grabber = FrameGrabber(CAMERA_URL, snapshot_url=SNAPSHOT_URL)
grabber.start()


def mjpeg_generator():
    """Generator yielding multipart MJPEG frames pulled from the single background grabber."""
    last_id = -1
    try:
        while True:
            frame, fid = grabber.wait_for_next(last_id, timeout=5.0)
            if frame is None:
                # nothing yet; yield a heartbeat-ish empty chunk to keep client happy if desired
                continue
            last_id = fid
            # build multipart chunk
            headers = (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
            )
            yield headers + frame + b"\r\n"
    except GeneratorExit:
        return


@app.route("/video_feed")
def video_feed():
    return Response(stream_with_context(mjpeg_generator()), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/snapshot")
def snapshot():
    """Return the latest JPEG frame from the camera (raw, no processing)."""
    frame, fid = grabber.get_frame()
    if frame is None:
        return ("No frame yet", 503)
    return Response(frame, mimetype='image/jpeg', headers={"Content-Length": str(len(frame))})


def jpeg_bytes_to_rgb_numpy(jpeg_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Failed to decode JPEG bytes")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb

@app.route("/class", methods=['GET'])
def class_route():
    frame, fid = grabber.get_frame()
    if frame is None:
        return ("No frame yet", 503)
    rgb = jpeg_bytes_to_rgb_numpy(frame)

    outputs = model(rgb)
    instances = outputs.get("instances", None)
    labels = get_class_labels()
    if instances is None or len(instances) == 0:
        return (jsonify({"class": None}), 204)

    # obtain scores and class indices robustly
    try:
        scores = instances.scores.cpu().numpy()
    except Exception:
        try:
            scores = np.array([1.0] * len(instances))
        except Exception:
            scores = np.array([1.0])
    try:
        classes = instances.pred_classes.cpu().numpy()
    except Exception:
        try:
            classes = np.asarray(instances.pred_classes)
        except Exception:
            classes = np.array([0])

    if scores.size == 0:
        idx = 0
    else:
        idx = int(np.argmax(scores))

    class_idx = int(classes[idx])
    class_label = labels[class_idx] if class_idx < len(labels) else str(class_idx)
    return class_label


@app.route("/position", methods=['GET'])
def position_route():
    target_label = request.args.get("label", None)

    frame, fid = grabber.get_frame()
    if frame is None:
        return ("No frame yet", 503)

    try:
        rgb = jpeg_bytes_to_rgb_numpy(frame)
    except Exception as e:
        return (f"Failed to decode frame: {e}", 500)

    outputs = model(rgb)
    instances = outputs.get("instances", None)
    labels = get_class_labels()
    if instances is None or len(instances) == 0:
        return (jsonify({}), 204)

    try:
        boxes_np = instances.pred_boxes.tensor.cpu().numpy()
    except Exception:
        try:
            boxes_np = np.asarray(instances.pred_boxes)
        except Exception:
            try:
                boxes_np = instances.pred_boxes.to("cpu").tensor.numpy()
            except Exception:
                return ("Failed to read bounding boxes", 500)

    try:
        scores = instances.scores.cpu().numpy()
    except Exception:
        scores = np.ones((boxes_np.shape[0],), dtype=float)

    try:
        classes = instances.pred_classes.cpu().numpy()
    except Exception:
        try:
            classes = np.asarray(instances.pred_classes)
        except Exception:
            classes = np.zeros((boxes_np.shape[0],), dtype=int)

    chosen_idx = None
    if target_label is not None:
        matches = [i for i, c in enumerate(classes) if (int(c) < len(labels) and labels[int(c)] == target_label)]
        if len(matches) == 0:
            return (jsonify({"error": "label not found"}), 404)
        best = max(matches, key=lambda i: float(scores[i]) if i < len(scores) else 0.0)
        chosen_idx = int(best)
    else:
        if scores.size > 0:
            chosen_idx = int(np.argmax(scores))
        else:
            chosen_idx = 0

    if chosen_idx is None or chosen_idx < 0 or chosen_idx >= boxes_np.shape[0]:
        return (jsonify({"error": "no valid detection found"}), 404)

    x1, y1, x2, y2 = [int(round(float(v))) for v in boxes_np[chosen_idx]]
    score = float(scores[chosen_idx]) if chosen_idx < len(scores) else 1.0
    label_idx = int(classes[chosen_idx]) if chosen_idx < len(classes) else 0
    label_name = labels[label_idx] if label_idx < len(labels) else str(label_idx)

    return f"{x1} {y1} {x2} {y2}"


@app.route("/")
def index():
    return ("<html><body>"
            "<img src='/video_feed'/>"
            "</body></html>")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
