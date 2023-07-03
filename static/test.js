let audioChunks = [];
let recordings = [];

let introduction = "Przed przeprowadzeniem każdego badania zostanie odczytana krótka instrukcja. W czasie nagrywania okienko badania będzie podświetlone na fioletowo (wtedy możesz mówić). W przerwach między nagraniami okienko będzie pomarańczowe. Po zakończonym badaniu zmieni ono kolor na zielone."
let mobileLockScreen = "Korzystasz z telefonu, więc pamiętaj żeby w trakcie badania nie dopuścić do zablokowania ekranu."
let numerals = ['Pierwsze', 'Drugie', 'Trzecie', 'Czwarte', 'Piąte'];

let COLOR_BLUE = 'rgb(115, 85, 207, 0.5)';
let COLOR_ORANGE = 'rgb(207, 148, 76, 0.5)';
let COLOR_GREEN = 'rgb(76, 207, 96, 0.5)';

function readTextPL(text) {
  return new Promise((resolve) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pl-PL';
    utterance.rate = 0.9;
    utterance.onend = () => {
      resolve();
    };
    window.speechSynthesis.speak(utterance);
  });
}

function isMobileDevice() {
  return (typeof window.orientation !== "undefined") || (navigator.userAgent.indexOf('IEMobile') !== -1);
};

function uploadRecordings(experiment_id) {
  const participant_id = document.querySelector('#participant-id').innerText;

  let formData = new FormData();
  formData.append('participant_id', participant_id);
  formData.append('experiment_id', experiment_id);

  recordings.forEach((recording, index) => {
    formData.append('recordings', recording, `recording-${index}.wav`);
  });

  fetch('/upload_recordings', {
    method: 'POST',
    body: formData
  });
}

async function conductExperimentsAutomatically() {
  if (isMobileDevice()) {
    await readTextPL(mobileLockScreen);
  }
  await readTextPL(introduction);

  const experimentBoxes = document.querySelectorAll('.box');

  for (const experimentBox of experimentBoxes) {
    const title = experimentBox.querySelector('.box-title').innerText;
    const description = experimentBox.querySelector('.box-description').innerText;
    experimentBox.style.backgroundColor = COLOR_ORANGE;
    experimentBox.scrollIntoView({ behavior: "smooth" });

    await readTextPL(title + '. ' + description + '. Badanie rozpocznie się za 3 sekundy.');
    await new Promise((resolve) => setTimeout(resolve, 3000));

    await conductExperiment(experimentBox);

    await readTextPL(title + ' zakończone.');
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  setTimeout(showThankYouScreen, 1000);
}

function updateExperimentBox(experimentBox, chunks, max_recordings) {
  const audioBlob = new Blob(chunks, { type: 'audio/wav' });
  const audioUrl = URL.createObjectURL(audioBlob);
  const audioPlayer = document.createElement('audio');
  audioPlayer.controls = true;
  audioPlayer.src = audioUrl;

  const recordingList = experimentBox.querySelector('.recording-list');
  recordingList.appendChild(audioPlayer);

  const counterElem = experimentBox.querySelector('.recording-counter');
  const currentCount = parseInt(counterElem.innerText.match(/\d+/)[0]);
  const newCount = currentCount + 1;
  counterElem.innerText = `Liczba nagrań: ${newCount} / ${max_recordings}`;

  recordings.push(audioBlob);
}

async function conductExperiment(experimentBox) {
  let stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1 } });

  experimentBox.querySelector('.sample-status').innerText = 'Status: W trakcie';

  const experiment_id = experimentBox.querySelector('.experiment-id').innerText;
  const max_recordings = parseInt(experimentBox.querySelector('.recording-counter').getAttribute("data-max-recordings"));

  recordings = [];

  for (i = 0; i < max_recordings; i++) {
    experimentBox.style.backgroundColor = COLOR_ORANGE;

    await readTextPL(numerals[i] + ' nagranie rozpocznie się za sekundę.');
    await new Promise((resolve) => setTimeout(resolve, 1000));

    experimentBox.style.backgroundColor = COLOR_BLUE;

    const waitForRecordingCompletion = new Promise((resolve) => {
      const listener = () => {
        experimentBox.removeEventListener('recordingCompleted', listener);
        resolve();
      }
      experimentBox.addEventListener('recordingCompleted', listener);
    });

    let mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };
    mediaRecorder.onstop = () => {
      updateExperimentBox(experimentBox, audioChunks, max_recordings);

      audioChunks = [];

      experimentBox.dispatchEvent(new CustomEvent('recordingCompleted'));
    };
    mediaRecorder.start();

    setTimeout(async () => {
      mediaRecorder.stop();
      experimentBox.style.backgroundColor = COLOR_ORANGE;
    }, 3100);

    await waitForRecordingCompletion;
  }

  uploadRecordings(experiment_id);
  experimentBox.querySelector('.sample-status').innerText = 'Status: Przeprowadzone';
  experimentBox.style.backgroundColor = COLOR_GREEN;
}

function showThankYouScreen() {
  const participant_id = document.querySelector('#participant-id').innerText;
  const splashScreen = document.createElement('div');
  splashScreen.className = 'splash-screen';
  splashScreen.innerHTML = 'Dziękujemy za udział w badaniu! Poczekaj na przekierowanie na stronę startową!';

  document.body.appendChild(splashScreen);

  window.location.href = '/results?id=' + participant_id;
}

document.addEventListener('DOMContentLoaded', () => {
  const autoTestButton = document.querySelector('#conduct-experiment');
  autoTestButton.addEventListener('click', () => {
    autoTestButton.disabled = true;
    conductExperimentsAutomatically();
  });
});
