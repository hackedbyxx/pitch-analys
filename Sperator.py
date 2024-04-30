import os

from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter
from multiprocessing import freeze_support

# python -m spleeter separate -p spleeter:2stems -o output "1672507817.mp3"
path = folder + '/' + file_name + '/vocals.wav'
print(os.path.abspath(path))

if __name__ == '__main__':
    freeze_support()
    separator = Separator('spleeter:2stems')
    input_ = r'C:\Users\SN78083\Music\搁浅.m4a'
    # audio_loader = AudioAdapter.default()
    # sample_rate = 44100
    # waveform, _ = audio_loader.load(input_, sample_rate=sample_rate)

    # Perform the separation :
    # prediction = separator.separate(waveform)
    separator.separate_to_file(input_, 'output', synchronous=False)