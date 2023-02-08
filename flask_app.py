import traceback

from flask import Flask, request, jsonify, render_template
import tempfile
import math
import parselmouth

from pydub import AudioSegment
from scipy.signal import savgol_filter

app = Flask(__name__)


@app.route("/", methods=['GET'])  # 请求方式为get
def login():
    return render_template('upload.html')


@app.route('/pitch_track', methods=['POST'])
def pitch_track(smooth=False):
    smooth = request.args['smooth']

    try:
        # Save the file that was sent, and read it into a parselmouth.Sound
        # windows要设置delete为False,否则无法正确生成临时文件
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(request.files['audio'].read())
            tmp_name = convert_audio_for_model(tmp.name)
            sound = parselmouth.Sound(tmp_name)

        # Calculate the pitch track with Parselmouth
        pitch_track = sound.to_pitch().selected_array['frequency']

        pitches = list(pitch_track)
        # 数据平滑处理
        if smooth == '1':
            pitches = list(savgol_filter(pitches, 99, 1, mode='nearest'))
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
        # 音高标记
        A4 = 440
        C0 = A4 * pow(2, -4.75)
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
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
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return str(e)


EXPECTED_SAMPLE_RATE = 16000


# Function that converts the user-created audio to the format that the model
# expects: bitrate 16kHz and only one channel (mono).
def convert_audio_for_model(user_file, output_file='converted_audio_file.wav'):
    audio = AudioSegment.from_file(user_file)
    audio = audio.set_frame_rate(EXPECTED_SAMPLE_RATE).set_channels(1)
    audio.export(output_file, format="wav")
    return output_file
