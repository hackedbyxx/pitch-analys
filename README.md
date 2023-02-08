### 前提背景
之前在B站看到一个分析歌手在各大晚会的歌唱表演是否为假唱，通过分析声音的频率还有连续稳定性来判断，觉得很有意思来研究一下。

### 准备工作
首先找到了tensorflow的Spice声音分析模型，查看了下[官方文档](https://tensorflow.google.cn/hub/tutorials/spice?hl=zh-cn)照着示例用了一下，步骤比较繁琐且不易懂，其使用的plotly python生成数据图性能较差生成较慢。

于是找到了另一个开源库 [Parselmouth](https://parselmouth.readthedocs.io/en/stable/)，
Parselmouth是Praat软件的 Python 库，Parselmouth 直接访问 Praat 的 C/C++ 代码（这意味着算法及其输出与 Praat 中的完全相同）并提供对程序数据的高效访问，但也提供了一个看起来与任何其他 Python 库没有区别的界面，
使用起来效率更高且相对简单易懂。

### 基础数据处理
获取频率
```python
sound = parselmouth.Sound(tmp_name)
# 获取频率数组
pitch_track = sound.to_pitch().selected_array['frequency']
```
计算音高，首先了解了下音高的定义及对应频率算法，参考[音高、音名与对应频率](https://www.jianshu.com/p/0fc2163cfc50)
```python
pitches = list(pitch_track)
A4 = 440 #以A4为基准频率
C0 = A4 * pow(2, -4.75) #计算最低C0音高后面作为对比
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
```
获取到对应时间点的频率及计算出来的音高，数据处理完毕

### 前端展示
相对复杂一些

使用plotly js进行数据展示，性能较好且考虑到跨平台使用了Flask开放对应接口使用
音频图展示比较容易但是动画相对复杂一些，plotly自带的动画插入帧可以实现基本的波形动画，但是无法获取每一帧的事件，没有办法进行回调处理。
于是曲线救国使用setInterval定时绘制标头及计算滚动rangeslider
```javascript
//计算range范围
var xrange = 20; //当前屏展示的时间范围
var startX = x/100;
startX = startX>xrange/5*2?startX-xrange/5*2:0;
Plotly.update("plot", {}, {xaxis:{range:[startX, startX+xrange]}});
```
setInterval会有一些延迟，目前还没有找到好的解决方案

### 使用地址及效果展示

**https://taotail.pythonanywhere.com/**
![图片](https://findxx.cn/2023/02/07/pitch-analys/%E8%83%8C%E5%8F%9B.png)
