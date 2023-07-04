# Wake word "komputer" reasearch
This repository houses the code and related resources for a project focused on testing the accuracy of a neural network (NN) in detecting the wake word "komputer". This project formed the basis for a thesis study and comprises several distinct experiments.

The main function of the project is to collect 3-second voice samples from study participants, run a neural network model to verify the accuracy of the wake word detection, and subsequently save the results into a CSV file.

## Experiments

The project includes the following experiments:

1. **Background Noise Test:** Gathering background noise sample in testing environment.

2. **Distance-Based Accuracy Tests:** These tests evaluate the NN's accuracy at varying distances from the audio source. Five samples were collected for each distance. The distances tested were:
    - 0.5 cm
    - 1 m
    - 3 m
    - 5 m

## Getting Started

To clone and run this project, you'll need [Git](https://git-scm.com) and [Python3](https://www.python.org/downloads/) (which comes with [pip](https://pip.pypa.io/en/stable/installing/)) installed on your computer. From your command line:

```bash
$ git clone [https://github.com/chwalap/wake-word-research](https://github.com/chwalap/wake-word-research)
$ cd wake-word-research
$ python -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

## Usage

After installing the project, you can start the server with:

```bash
$ python app.py
```

Once the server is running, open a web browser and navigate to `localhost:8080` to access the website and begin testing.

## Generating Research Results

This project includes a Jupyter notebook that can be used to generate the research results. The notebook processes the collected data and produces a series of histograms and calculates mean accuracies based on gender, age range, and distance.

```bash
$ jupyter notebook
```

Once the Jupyter server is running, navigate to the project directory in the Jupyter interface in your web browser, and open the notebook file (`Results.ipynb`). 

In this notebook, you can run all cells to generate the charts and the mean accuracy calculations.

If you encounter any issues, please check that you have all necessary Python libraries installed (see the `requirements.txt` file) and that your data files are correctly located and accessible to the Jupyter notebook.

## License

Distributed under the GNU Affero General Public License v3.0. See `LICENSE` for more information.
