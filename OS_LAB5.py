from threading import Thread, Event
import time
import itertools
from string import ascii_letters
from queue import Queue
from pynput import keyboard

MIN_LEN = 3
MAX_LEN = 26
QUANTUM = 450000  # nanosecond
TICK = QUANTUM * 15
WORDS = ("AzFh", "AfaA", "oodN")

ready_queue = Queue(maxsize=3)
wait_queue = Queue(maxsize=1)

#описание потока
class BruteThread(Thread):
    def __init__(self, name, word):
        Thread.__init__(self)
        self.name = name
        self.word = word
        self.__is_ready = False
        self.__count = 0
        self.__pause_event = Event()

    def _simple_brute(self):
        for repeat in range(MIN_LEN, MAX_LEN):
            for i in itertools.product(ascii_letters, repeat=repeat):
                self.__count += 1
                #print(''.join(i))
                self.__pause_event.wait()
                if ''.join(i) == self.word:
                    return True
        return None

#запуск и выполнение потока
    def run(self):
        self.__is_ready = True
        if self.__is_ready:
            print(f"Работа с потоком '{self.name}' запущена!")
        if self._simple_brute() is not None:
            print(f"Работа с потоком '{self.name}' успешно завершена! Слово: {self.word} Итераций: {self.__count}")
        else:
            print(f"Поток '{self.name}' завершился неудачно! Слово: {self.word} Итераций: {self.__count}")
        self.__is_ready = False

#приостановить поток
    def pause(self):
        if self.__pause_event.is_set():
            self.__pause_event.clear()

#возобновить поток
    def resume(self):
        if not self.__pause_event.is_set():
            self.__pause_event.set()

#проверяет выполняется ли поток
    def is_ready(self):
        return self.__is_ready

#проверяет остановлен ли поток
    def unready(self):
        self.__is_ready = not self.__is_ready

#планировщик
class Helper:
    def __init__(self):
        self.__active_thread = None

    def set_active_thread(self, thread):
        self.__active_thread = thread

    def get_active_thread(self):
        return self.__active_thread

    def wait_timer_or_event(self):
        start = time.time_ns()
        while self.__active_thread.is_ready():
            if time.time_ns() - start >= TICK:
                ready_queue.put(self.__active_thread)
                break
        return


threads = [BruteThread("первый", WORDS[0]), BruteThread("второй", WORDS[1]), BruteThread("третий", WORDS[2])]

Planner = Helper()

#отработка горячей клавиши
def on_hotkey():
    if wait_queue.qsize() >= 1:
        active_thread = wait_queue.get()
        active_thread.unready()
        ready_queue.put(active_thread)
        print("Клавиша активирована, поток отправлен на готовность ", active_thread.name)
    else:
        if Planner.get_active_thread() is not None:
            active_thread = Planner.get_active_thread()
            active_thread.pause()
            active_thread.unready()
            wait_queue.put(active_thread)
            print("Клавиша активирована, поток ожидает ", active_thread)
    return


def for_canonical(f):
    return lambda k: f(listener.canonical(k))


hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('k'),
    on_activate=on_hotkey)

listener = keyboard.Listener(
    on_press=for_canonical(hotkey.press),
    on_release=for_canonical(hotkey.release))

listener.start()

# Порождение
[item.start() for item in threads]

# Заполнение очереди готовыми потоками
for thread in threads:
    if thread.is_ready():
        ready_queue.put(thread)

# Основная логика программы
while ready_queue.qsize() or wait_queue.qsize():
    active_thread = ready_queue.get()
    active_thread.resume()
    Planner.set_active_thread(active_thread)
    Planner.wait_timer_or_event()
    active_thread.pause()
    Planner.set_active_thread(None)
listener.stop()
for thread in threads:
    thread.join()

