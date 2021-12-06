from datetime import datetime
from subprocess import Popen
from time import sleep

import sys


PYTHON_PATH = sys.executable

WORKERS = [
    'parser.py',
    'main.py'
]


def main():

    for file_name in WORKERS:
        Popen([PYTHON_PATH, file_name])

        print(f'------> file: {file_name} is running...')
        sleep(5)

    print('------> All files are running!')
    print(f'Start time: {datetime.now()}')


if __name__ == '__main__':
    main()
