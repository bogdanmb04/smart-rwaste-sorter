# RecyclingDetectron

A detectron2 model trained in order to classify recyclable waste. Uses the [Trashnet](https://github.com/garythung/trashnet) dataset in order to train.

## Explanation
The model's build can be found within the jupyter notebook in this repository - `detectron.ipynb`. It must be built in order to be deployed.

The model itself can be deployed via the flask server within `main.py`. It is used to gather data from an [ESP-32 cam](https://i0.wp.com/randomnerdtutorials.com/wp-content/uploads/2019/03/ESP32-CAM-camera.jpg?w=750&quality=100&strip=all&ssl=1) and trigger a signal based on the detected classes:
1. Paper
2. Cardboard
3. Metal
4. Glass
5. Plastic
6. Trash

To simplify the real-life aspect of sorting recyclable trash (and because this is only a proof-of-concept project), the following table groups up the class labels together:

| Super label | Small labels list |
|-------------|-------------------|
| Blue        | Paper, Cardboard  |
| Yellow      | Plastic, Metal    |
| Green       | Glass             |
| Red         | Trash             |

The server sends a message to an Arduino board in order to signal the detected class.

## Requirements

Install detectron2 according to its [documentation](https://detectron2.readthedocs.io/en/latest/tutorials/install.html). Remember to install [PyTorch and torchvision](https://pytorch.org/) from the same place as well, in order to avoid conflicts.
If you're using `conda` environment, look up the specific steps in order to install the CUDA toolkit specific for your current CUDA installation.
