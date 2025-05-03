from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from typing import List

def get_saved_model() -> DefaultPredictor:
    cfg = get_cfg()
    cfg.merge_from_file("./output/configuration.yaml")
    cfg.MODEL.WEIGHTS = "output/model_final.pth"
    cfg.MODEL.DEVICE = "cuda"
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    return DefaultPredictor(cfg)

def get_class_labels() -> List[str]:
    return ['idk', 'cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash'] #not queueing up the stupid instances just to get the class labels
#legit just copy/pasted them from the notebook
#nobody will know except whoever is reading this
#why are you reading this?