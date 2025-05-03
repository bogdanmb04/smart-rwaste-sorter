# Smart Recyclable Waste Sorting System (SRWSS)

An IoT project, destined for Smart-City usage in recycling plants - proof of concept of a camera watching a conveyor belt, able to sort the recyclable waste into different categories.

## IoT

The main scope of this project is to exemplify the power such small components are able to hold.

### Communication

The components communicate in the following order:

**ESP32-cam ==> Flask server ==> Detectron ==> Flask Server ==> Arduino**

Where:

- The ESP32-cam instantiates its own server, where it will send back an image whenever accessed
- The Flask server will continuosly queue the ESP32-cam, taking the image it returns and placing it through the model
- The Detectron takes the image and returns a corresponding output
- Based on the class with the highest confidence within the model, the server sends over a signal to the Arduino board
- The Arduino lights up an LED corresponding to the server's response

## Recycling Detectron

A detectron2 model trained in order to classify recyclable waste. Uses the [Trashnet](https://github.com/garythung/trashnet) dataset for its training images.

### Explanation
The model's build can be found within the jupyter notebook in this repository - `detectron.ipynb`. It must be built in order to be deployed.

When deployed, the model can detect waste from the following categories:
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

The server sends a message to an Arduino board in order to signal the detected class. A LED with a color corresponding to the super label of the detected class will light up!

## Requirements

Install detectron2 according to its [documentation](https://detectron2.readthedocs.io/en/latest/tutorials/install.html). Remember to install [PyTorch and torchvision](https://pytorch.org/) from the same place as well, in order to avoid conflicts.
If you're using `conda` environment, look up the specific steps in order to install the CUDA toolkit specific for your current CUDA installation.

## Specs - used for training the model

| Component | Type                    |
|-----------|-------------------------|
| Memory    | 32GB DDR5               |
| CPU       | Intel Core i7-14650HX   |
| GPU       | NVIDIA GeForce RTX 4060 |

**Any other details regarding the model's architecture can be found within the notebook in the project (including augmentations made on the dataset's images).**