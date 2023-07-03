import csv
import json
import os
import random
import uuid

from flask import Flask, redirect, render_template, request

import librosa as rosa

import numpy as np

from pydub import AudioSegment

import tensorflow as tf
from tensorflow.python.ops import gen_audio_ops


TITLE = 'Badanie skuteczności modelu sieci'
KEYWORD = '"komputer"'
GENDERS = ['male', 'female']
AGE_RANGES = ['below_18', '18_30', '31_50', 'above_50']
DISTANCES = ['50cm', '1m', '3m', '5m']
EXPERIMENT_IDS = ['50cm', '1m', '3m', '5m', 'noise']

SAMPLES_PER_NOISE_TYPE = 10
RECORDINGS_PER_EXPERIMENT = 5

SAMPLE_RATE = 16000
FRAME_LENGTH = 320
FRAME_STEP = 160
POOLING_SIZE = [1, 6]

EXPERIMENTS = []

noise_experiment = {
    'id': 'noise',
    'title': 'Badanie poziomu szumu',
    'status': 'Nieprzeprowadzone',
    'description': 'Pozbądź się wszystkich źródeł dźwięku z otoczenia. To badanie potrwa 3 sekundy i będzie zawierało tylko jedno nagranie. Zachowaj ciszę w trakcie tego nagrania.',
    'recordings': 1
}
EXPERIMENTS.append(noise_experiment)

for distance in DISTANCES:
    experiment = {
        'id': f'{distance}',
        'title': f'Badanie z odległości {distance}',
        'status': 'Nieprzeprowadzone',
        'description': f'Stań w odległości {distance} od mikrofonu, a następnie głośno i wyraźnie wypowiedz słowo {KEYWORD}. To badanie zawiera pięć następujących po sobie nagrań.',
        'recordings': RECORDINGS_PER_EXPERIMENT
    }
    EXPERIMENTS.append(experiment)

app = Flask(__name__)

# todo: update model
interpreter = tf.lite.Interpreter(model_path='./data/model.tflite')
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# todo: change detection threshold
DETECTION_THRESHOLD = 0.5


def get_participant_dir(participant_id):
    return os.path.join("./data/", str(participant_id))


def validate_test_form(gender, age_range):
    if gender not in GENDERS:
        raise ValueError("Invalid gender")
    if age_range not in AGE_RANGES:
        raise ValueError("Age range must be in correct range")


def validate_upload_form(participant_id, experiment_id):
    _ = uuid.UUID(participant_id, version=4)
    if experiment_id not in EXPERIMENT_IDS:
        raise ValueError("Invalid experiment_id")
    if not os.path.exists(get_participant_dir(participant_id)):
        raise ValueError("Participant id does not exists")


def validate_reusults_request(participant_id):
    if not os.path.exists(get_participant_dir(participant_id)):
        raise ValueError("Participant id does not exists")


def init_participant(gender, age_range):
    participant_id = uuid.uuid4()
    participant_dir = get_participant_dir(participant_id)
    participant_data = {
        'gender': gender,
        'age': age_range
    }
    os.mkdir(participant_dir)
    with open(os.path.join(participant_dir, "participant.json"), "w") as file:
        json.dump(participant_data, file)

    return participant_id


def add_noise(audio, noise, scale=0.1):
    start = random.randint(0, len(noise) - len(audio) - 1)
    noise = noise[start:start + len(audio)]
    audio_with_noise = audio + scale * noise
    return audio_with_noise


def find_word_in_audio(audio, sample_rate=SAMPLE_RATE, word_duration=1):
    window_size = sample_rate * word_duration
    amplitudes = [np.mean(np.abs(audio[i:i+window_size])) for i in range(0, len(audio)-window_size, window_size)]
    max_position = np.argmax(amplitudes) * window_size
    return audio[max_position:max_position + window_size]


def normalize_audio(audio):
    audio = audio - np.mean(audio)
    audio = audio / np.max(np.abs(audio))
    return audio


def cut_audio_length(audio, length=SAMPLE_RATE):
    audio_len = len(audio)
    if audio_len < length:
        audio = np.append(audio, np.zeros(length - audio_len))
    audio = audio[:length]
    return audio


def cure_audio(audio):
    audio = cut_audio_length(audio)
    audio = normalize_audio(audio)
    return tf.cast(audio, tf.float32)


def get_spectrogram(file_path):
    audio, _ = rosa.load(file_path, sr=SAMPLE_RATE, mono=True)
    audio = find_word_in_audio(audio)
    audio = cure_audio(audio)
    spec = gen_audio_ops.audio_spectrogram(tf.expand_dims(audio, -1),
                                           window_size=FRAME_LENGTH,
                                           stride=FRAME_STEP,
                                           magnitude_squared=True).numpy()

    spec = tf.expand_dims(spec, -1)
    spec = tf.nn.pool(input=spec,
                      window_shape=POOLING_SIZE,
                      strides=POOLING_SIZE,
                      pooling_type='AVG',
                      padding='SAME')
    spec = np.squeeze(spec, axis=0)
    spec = np.log10(spec + 1e-6)
    return spec


def get_background_noise_level(file_path):
    audio = AudioSegment.from_wav(file_path)
    return audio.dBFS


@app.route('/')
def home():
    return render_template('index.html', title=TITLE)


@app.route('/test', methods=['POST'])
def test():
    gender = request.form['gender']
    age_range = request.form['age_range']

    try:
        validate_test_form(gender, age_range)
    except ValueError:
        return redirect('/')

    participant_id = init_participant(gender, age_range)

    return render_template('test.html',
                           title=TITLE,
                           participant_id=participant_id,
                           experiments=EXPERIMENTS)


@app.route('/upload_recordings', methods=['POST'])
def upload_recordings():
    participant_id = request.form['participant_id']
    experiment_id = request.form['experiment_id']

    try:
        validate_upload_form(participant_id, experiment_id)
    except ValueError:
        return redirect('/')

    participant_dir = get_participant_dir(participant_id)

    recordings = request.files.getlist('recordings')
    for i, recording in enumerate(recordings):
        file_name = f"{experiment_id}_{i}.wav"
        audio = AudioSegment.from_file(recording.stream)
        audio = audio.set_sample_width(2)
        audio = audio.set_frame_rate(SAMPLE_RATE)
        audio = audio.set_channels(1)
        audio.export(os.path.join(participant_dir, file_name), format="wav")

    return 'Recordings uploaded successfully', 200


@app.route('/results', methods=['GET'])
def results():
    try:
        participant_id = request.args.get('id')
        validate_reusults_request(participant_id)
    except ValueError:
        return redirect('/')

    participant_dir = get_participant_dir(participant_id)

    with open(os.path.join(participant_dir, 'participant.json'), 'r') as file:
        participant_info = json.load(file)

    noise_level = get_background_noise_level(os.path.join(participant_dir, 'noise_0.wav'))

    data = []

    for file in os.listdir(participant_dir):
        if file == 'noise_0.wav':
            continue
        elif file.endswith(".wav"):
            distance = file.split('_')[0]
            file_path = os.path.join(participant_dir, file)
            spec = get_spectrogram(file_path)
            spec = tf.expand_dims(spec, 0)
            interpreter.set_tensor(input_details[0]['index'], spec)
            interpreter.invoke()
            output_data = interpreter.get_tensor(output_details[0]['index'])
            detection = np.squeeze((output_data >= DETECTION_THRESHOLD).astype(int))

            data.append({
                "ID": participant_id,
                "Płeć": participant_info["gender"],
                "Wiek": participant_info["age"],
                "Odległość": distance,
                "Szum tła (dB)": noise_level,
                "Wynik": detection
            })

    keys = data[0].keys()
    csv_filename = os.path.join(participant_dir, 'results.csv')
    with open(csv_filename, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
