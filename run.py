from datetime import datetime
from subprocess import Popen
from time import sleep

import sys
import os


PYTHON_PATH = sys.executable

WORKERS = [
    'telegram_parser.py',
    'main.py'
]


def main():
    session_files = os.listdir('sessions')

    for i in session_files:
        if i.endswith('session-journal'):
            os.remove(f'sessions/{i}')

    if not 'user_v1.session' in session_files or not 'user_v2.session' in session_files:
        print('Error: Session files not found!')
        countdown = list(range(1, 6))
        countdown.reverse()

        for i in countdown:
            print(f'Exit in {i}')
            sleep(1)
        sys.exit()


    for file_name in WORKERS:
        Popen([PYTHON_PATH, file_name])

        print(f'------> file: {file_name} is running...')
        sleep(5)

    print('------> All files are running!')
    print(f'Start time: {datetime.now()}')


if __name__ == '__main__':
    main()
