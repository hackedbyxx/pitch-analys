import json
import os
import re
import sys
import time
import traceback

import requests
from flask import Flask, request, jsonify, render_template
import tempfile
import math
import parselmouth

# from pydub import AudioSegment
#from scipy.signal import savgol_filter

# 音高标记
from pydub import AudioSegment

A4 = 440
C0 = A4 * pow(2, -4.75)
note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

app = Flask(__name__, template_folder="../templates", static_folder="../static")

session = requests.Session()
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/85.0.4183.102 Safari/537.36 "
}


@app.route("/", methods=['GET'])  # 请求方式为get
def upload():
    return render_template('upload.html')


@app.route('/pitch_track', methods=['POST'])
def pitch_track(smooth=False, vocal=0):
    smooth = request.args['smooth']
    vocal = request.args['vocal']
    try:
        # Save the file that was sent, and read it into a parselmouth.Sound
        # windows要设置delete为False,否则无法正确生成临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(request.files['audio'].read())
            # tmp_name = convert_audio_for_model(tmp.name)
            file_name = tmp.name
            print(file_name)
            if vocal == '1':
                file_name = separate_vocal(file_name)
            print(file_name)
            return jsonify(get_pitch_result(file_name))
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"info": "转换数据失败：" + str(e)}, ensure_ascii=False)


# 获取音高数据
def get_pitch_result(sound_file_name, smooth="0"):
    # Calculate the pitch track with Parselmouth
    try:
        sound = parselmouth.Sound(sound_file_name)
    except Exception as e:
        convert_audio_for_model(sound_file_name, sound_file_name)
        sound = parselmouth.Sound(sound_file_name)
    pitch = sound.to_pitch()
    # pitch = pitch.smooth(0)
    pitch_track = pitch.selected_array['frequency']

    pitches = list(pitch_track)
    # 数据平滑处理
    if smooth == "1":
        None
        # pitches = list(savgol_filter(pitches, 99, 1, mode='nearest'))
    '''
    # 每0.5s计算平均音高 算法待优化
    pitches = []
    times = []
    all_pitch = 0.0
    offset = 50
    for i, pitch in enumerate(pitch_track):
        all_pitch += pitch
        if i % offset == 0 and i != 0:
            avg_pitch = all_pitch/offset
            times.append(round(i/100, 1))
            pitches.append(avg_pitch)
            all_pitch = 0.0
    '''

    notes = []
    times = []
    for i, freq in enumerate(pitches):
        times.append(i / 100)
        # if freq < 329:
        #     notes.append(None)
        #     continue
        if freq == 0.0:
            notes.append(None)
            continue
        h = round(12 * math.log2(freq / C0))
        octave = h // 12
        n = h % 12
        minute = int(i / 60 / 100)
        second = round(i / 100 % 60, 1)
        note = note_names[n] + str(octave) + '-' + str(minute) + 'm' + str(second) + 's'
        notes.append(note)
    # Convert the NumPy array into a list, then encode as JSON to send back
    result = {
        'times': times,
        'pitches': pitches,
        'notes': notes
    }
    return result


@app.route('/kge_pitch_track', methods=['POST'])
def kge_pitch_track(vocal=False):
    vocal = request.args['vocal']
    try:
        url = request.form['url']

        result = session.get(url=url, headers=headers, timeout=10)
        pattern = re.compile('"playurl":"(.*?)",', re.S)
        cover_pattern = re.compile('"fb_cover":"(.*?)",', re.S)
        name_pattern = re.compile('"song_name":"(.*?)",', re.S)
        if result.status_code == 200:
            res = result.text
            url = re.findall(pattern, res)[0]
            print(url)
            cover = re.findall(cover_pattern, res)[0]
            song_name = re.findall(name_pattern, res)[0]
            info = {
                "cover": cover,
                "url": url,
            }
            rsp = requests.head(url)
            # get the file size
            size = rsp.headers['Content-Length']
            # convert Byte to MB
            print("%.2f MB" % (int(size) / 1024 / 1024))
            p = 0
            rp = requests.get(url, stream=True)
            with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as tmp:
                for i in rp.iter_content(chunk_size=1024):
                    p += len(i)
                    tmp.write(i)
                    done = 50 * p / int(size)
                    sys.stdout.write("\r[%s%s] %.2f%%" % ('█' * int(done), '' * int(50 - done), done + done))
                sys.stdout.flush()
                file_name = tmp.name
                if vocal == '1':
                    file_name = separate_vocal(file_name)
                pitch_result = get_pitch_result(file_name)
                pitch_result['song_name'] = song_name
                pitch_result['audio_url'] = url
                return json.dumps(pitch_result)
        else:
            return json.dumps({"info": "暂无相关数据，请检查相关数据："}, ensure_ascii=False)
    except Exception as e:
        traceback.print_exc()
        return json.dumps({"info": "暂无相关数据，请检查相关数据：" + str(e)}, ensure_ascii=False)


'''
import tensorflow as tf
import tensorflow_hub as hub
from scipy.io import wavfile
@app.route('/pitch_track_spice', methods=['POST'])
def pitch_track_spice():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(request.files['audio'].read())
        converted_audio_file = convert_audio_for_model(tmp.name)
        sample_rate, audio_samples = wavfile.read(converted_audio_file, 'rb')

    model = hub.load("https://tfhub.dev/google/spice/2")

    # We now feed the audio to the SPICE tf.hub model to obtain pitch and uncertainty outputs as tensors.
    model_output = model.signatures["serving_default"](tf.constant(audio_samples, tf.float32))

    pitch_outputs = model_output["pitch"]
    uncertainty_outputs = model_output["uncertainty"]

    # 'Uncertainty' basically means the inverse of confidence.
    confidence_outputs = 1.0 - uncertainty_outputs

    # 我们移除所有具有低置信度（置信度<0.9）的音高估计值，并绘制剩余估计值，使结果更易于理解。
    confidence_outputs = list(confidence_outputs)
    pitch_outputs = [float(x) for x in pitch_outputs]

    indices = range(len(pitch_outputs))
    confident_pitch_outputs = [(i, p)
                               for i, p, c in zip(indices, pitch_outputs, confidence_outputs) if c >= 0.95]
    confident_pitch_outputs_x, confident_pitch_outputs_y = zip(*confident_pitch_outputs)

    confident_pitch_values_hz = [output2hz(p) for p in confident_pitch_outputs_y]

    # 在输出中添加零来表示没有歌声的部分
    pitch_outputs_and_rests = [
        output2hz(p) if c >= 0.9 else 0
        for i, p, c in zip(indices, pitch_outputs, confidence_outputs)
    ]
    times = []
    notes = []
    print(confident_pitch_outputs_x[len(confident_pitch_outputs_x)-1])
    for i, freq in enumerate(confident_pitch_values_hz):
        # if freq < 329:
        #     notes.append(None)
        #     continue
        times.append(confident_pitch_outputs_x[i] / 100)
        if freq == 0.0:
            notes.append(None)
            continue
        h = round(12 * math.log2(freq / C0))
        octave = h // 12
        n = h % 12
        x = confident_pitch_outputs_x[i]
        minute = int(x / 60 / 100)
        second = round(x / 100 % 60, 1)
        note = note_names[n] + str(octave) + '-' + str(minute) + 'm' + str(second) + 's'
        notes.append(note)
    # Convert the NumPy array into a list, then encode as JSON to send back
    result = {
        'times': times,
        'pitches': confident_pitch_values_hz,
        'notes': notes
    }
    return jsonify(result)
'''

EXPECTED_SAMPLE_RATE = 16000


# Function that converts the user-created audio to the format that the model
# expects: bitrate 16kHz and only one channel (mono).

def convert_audio_for_model(user_file, output_file='converted_audio_file.wav'):
    audio = AudioSegment.from_file(user_file)
    audio = audio.set_frame_rate(EXPECTED_SAMPLE_RATE).set_channels(1)
    audio.export(output_file, format="wav")
    return output_file

def separate_vocal(file_input):
    from spleeter.separator import Separator
    folder = 'output'
    separator = Separator('spleeter:2stems')
    separator.separate_to_file(file_input, folder, synchronous=False)
    time.sleep(5)
    dirStr, ext = os.path.splitext(file_input)
    file_name = dirStr.split("\\")[-1]
    path = folder + '/' + file_name + '/vocals.wav'
    path = os.path.abspath(path)
    while not os.path.exists(path):
        None
    return path

if __name__ == '__main__':
    app.run(debug=True)