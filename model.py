import torch
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from typing import List

def get_saved_model() -> DefaultPredictor:
    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    cfg = get_cfg()
    cfg.merge_from_file("./output/configuration.yaml")
    cfg.MODEL.WEIGHTS = "output/model_final.pth"
    cfg.MODEL.DEVICE = device.type
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    return DefaultPredictor(cfg)

def get_class_labels() -> List[str]:
    return ['idk', 'cardboard', 'glass', 'metal', 'paper', 'plastic']
