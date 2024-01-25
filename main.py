import numpy as np
import soundcard as sc
from scipy.io import wavfile
import mss,cv2,time,threading,os,datetime

rec_len = int(input('Введите время записи (в секундах) : '))
with mss.mss() as sct:
    monitor = sct.monitors[1]
    width = monitor['width']
    height = monitor['height']

print(f'\nОпределено разрешение монитора {width} x {height}\n')
mics = sc.all_microphones(include_loopback=True)
default_mic = mics[0]
print(f'\nУстройство записи звука - {default_mic}\n')
print('\nДо начала записи - 20 секунд, скройте это окно и откройте видео которое нужно записать. Запись начнётся после звукового сигнала\n')
time.sleep(20)
sc.default_speaker().play(0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, int(44100 * 0.5), endpoint=False)), samplerate=44100)

def get_audio():
    default_speaker = sc.default_speaker()
    with default_mic.recorder(samplerate=44100) as mic, default_speaker.player(samplerate=44100) as sp:
        data = mic.record(numframes=44100 * rec_len)
    filename = "recorded_audio.wav"
    scaled = np.int16(data/np.max(np.abs(data)) * 32767)
    wavfile.write(filename, 44100, scaled)

def get_video():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
        out = cv2.VideoWriter('screen_capture.mp4', fourcc, 30.0, (width, height))
        start_time = time.time()
        while int(time.time() - start_time) < rec_len:
            print('\033[F\033[K', end='')
            print(f'Записано секунд - {int(time.time() - start_time)}')
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
        out.release()
    sc.default_speaker().play(0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, int(44100 * 0.5), endpoint=False)), samplerate=44100)
    print('\nЗапись завершена, начинаю объединение звука и видео\n')
    time.sleep(5)
    name = f'{str(datetime.datetime.now().time()).replace(':','_')[:8]}.mp4'
    os.system(f'ffmpeg -i screen_capture.mp4 -i recorded_audio.wav -c:a aac -strict experimental -vf scale={width}:{height} {name}')
    print('\n\n\n\nОбъединение завершено, удаляю временные файлы.')
    os.remove('screen_capture.mp4')
    os.remove("recorded_audio.wav")
    input(f"Программа завершила свою работу, запись сохранена в {name} для выхода нажмите ENTER")
    exit()
if __name__ == "__main__":
    audio_thread = threading.Thread(target=get_audio)
    video_thread = threading.Thread(target=get_video)

    audio_thread.start()
    video_thread.start()

