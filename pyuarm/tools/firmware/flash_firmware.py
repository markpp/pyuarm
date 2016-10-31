from __future__ import print_function
from __future__ import division

__version__ = '1.0.5'
__author__  = 'Alex Tan'
'''
This Tool is for uArm firmware flashing. Also support download firmware online
'''

import sys
from serial.tools import list_ports
import os
import io
import platform
import subprocess
import json

if sys.version > '3':
    PY3 = True
else:
    PY3 = False

if PY3:
    import urllib.request
else:
    import urllib2

default_config = {
    "filename": "firmware.hex",
    "hardware_id": "USB VID:PID=0403:6001",
    "download_url": "http://download.ufactory.cc/firmware.hex",
    "download_flag": False
}

if getattr(sys, 'frozen', False):
    FROZEN_APP = True
elif __file__:
    FROZEN_APP = False




def resourcePath(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), "pyuarm" , "tools", relative_path)


def exit_fun():
    try:
        input("\nPress Enter to Exit...")
    except Exception:
        pass


def uarm_ports(hardware_id=default_config["hardware_id"]):
    uarm_ports = []
    for i in list_ports.comports():
        if i.hwid[0:len(hardware_id)] == hardware_id:
            uarm_ports.append(i[0])
    return uarm_ports


def get_uarm_port_cli():
    ports = uarm_ports()
    if len(ports) > 1:
        i = 1
        for port in ports:
            print(("[{}] - {}".format(i, port)))
            i += 1
        port_index = input("Please Choose the uArm Port: ")
        uarm_port = ports[int(port_index) - 1]
        return uarm_port
    elif len(ports) == 1:
        return ports[0]
    elif len(ports) == 0:
        print("No uArm ports is found.")
        return None


def download(url, filepath):
    try:
        if PY3:
            u = urllib.request.urlopen(url)
            fileTotalbytes = u.length
        else:
            u = urllib2.urlopen(url)
            fileTotalbytes = int(u.info().getheaders("Content-Length")[0])
        print ("writing to {}, file size: {} bytes ".format(filepath, str(fileTotalbytes)))

        data_blocks = []
        total=0

        while True:
            block = u.read(1024)
            data_blocks.append(block)
            total += len(block)
            hash = ((60*total)//fileTotalbytes)
            per =total / fileTotalbytes
            if PY3:
                print("[{}{}] {:.0%}".format('#' * hash, ' ' * (60-hash), per), end="\r")
            else:
                print("[{}{}] {:.0%}".format('#' * hash, ' ' * (60 - hash), per), end="\r")
            if not len(block):
                print ("\nCompleted!")
                break

        data=b''.join(data_blocks) #had to add b because I was joining bytes not strings
        u.close()


        with open(filepath, "wb") as f:
                f.write(data)
    except Exception as e:
        print ("Error: " + str(e))


def flash(port, firmware_path):
    if port:
        global avrdude_bin, avrdude_conf, error_description, cmd
        if platform.system() == 'Darwin':
            if FROZEN_APP:
                avrdude_bin = os.path.join(resourcePath('avrdude'), 'bin', 'avrdude')
                avrdude_conf = os.path.join(resourcePath('avrdude'), 'avrdude.conf')
            else:
                avrdude_bin = os.path.join(resourcePath('avrdude'), 'mac', 'bin', 'avrdude')
                avrdude_conf = os.path.join(resourcePath('avrdude'), 'mac', 'avrdude.conf')

            error_description = "built-in avrdude is not working, Trying to install avrdude..."

        elif platform.system() == 'Windows':
            if FROZEN_APP:
                avrdude_bin = os.path.join(resourcePath('avrdude'), 'avrdude.exe')
                avrdude_conf = os.path.join(resourcePath('avrdude'), 'avrdude.conf')
            else:
                avrdude_bin = os.path.join(resourcePath('avrdude'), 'win', 'avrdude.exe')
                avrdude_conf = os.path.join(resourcePath('avrdude'), 'win', 'avrdude.conf')
            # cmd = [avrdude_path, '-C' + avrdude_conf, '-v', '-patmega328p', '-carduino', port_conf, '-b115200', '-D',
            #        '-Uflash:w:{0}:i'.format(self.firmware_path)]
            error_description = "built-in avrdude is not working, Trying to download winavr..."

        elif platform.system() == 'Linux':
            if FROZEN_APP:
                if platform.architecture()[0] == '64bit':
                    avrdude_bin = os.path.join(resourcePath('avrdude'), 'avrdude-x64')
                else:
                    avrdude_bin = os.path.join(resourcePath('avrdude'), 'avrdude')
                avrdude_conf = os.path.join(resourcePath('avrdude'), 'avrdude.conf')
            else:
                if platform.architecture()[0] == '64bit':
                    avrdude_bin = os.path.join(resourcePath('avrdude'), 'linux', 'avrdude-x64')
                else:
                    avrdude_bin = os.path.join(resourcePath('avrdude'), 'linux', 'avrdude')
                avrdude_conf = os.path.join(resourcePath('avrdude'), 'linux', 'avrdude.conf')
            error_description = "built-in avrdude is not working, Trying to install avrdude..."

        cmd = [avrdude_bin, '-C' + avrdude_conf, '-v', '-patmega328p', '-carduino', '-P' + port, '-b115200', '-D',
               '-Uflash:w:{0}:i'.format(firmware_path)]

        print((' '.join(cmd)))
        try:
            subprocess.call(cmd)
        except OSError as e:
            print(("Error occurred: error code {0}, error msg: {1}".format(str(e.errno), e.strerror)))
            # if e.errno == 2:
            #     if platform.system() == 'Darwin':
            #         try:
            #             print("Installing avrdude...")
            #             subprocess.call(['brew', 'install', 'avrdude'])
            #             subprocess.call(cmd)
            #         except OSError as e:
            #             print(("Error occurred: error code {0}, error msg: {1}".format(str(e.errno), e.strerror)))
            #             if e.errno == 2:
            #                 print("-------------------------------------------------------")
            #                 print("You didn't install homebrew, please visit http://bew.sh")
            #                 print("-------------------------------------------------------")
            #     if platform.system() == 'Linux':
            #         print("------------------------------------------------------------------------------")
            #         print("You didn't install avrdude.\n "
            #               "please try `sudo apt-get install avrdude` or other package management command ")
            #         print("------------------------------------------------------------------------------")


class FlashFirmware:

    def __init__(self):
        if FROZEN_APP:
            self.application_path = os.path.dirname(__file__)
        else:
            self.application_path = os.path.dirname(sys.executable)

        if PY3:
            config_path = os.path.join(self.application_path, 'config.json')
        else:
            config_path = os.path.join(self.application_path, 'config.json').decode("utf8").encode("latin-1")
        if not os.path.exists(config_path):
            print ("config.json not found, use default setting: " + str(default_config))
            print ("\n")
            config = default_config
        else:
            print("Loading config file:" + str(config_path))
            with io.open(config_path, "r", encoding="utf-8") as data_file:
                config = json.load(data_file)

        if PY3:
            self.firmware_path = os.path.join(self.application_path, config['filename'])
        else:
            self.firmware_path = os.path.join(self.application_path, config['filename'].decode("utf8").encode("latin-1"))
        self.hardware_id = config['hardware_id']
        self.firmware_url = config['download_url']
        self.download_flag = config['download_flag']

    def flash_firmware(self):
        flash(port=get_uarm_port_cli(), firmware_path=self.firmware_path)

    def download_firmware(self):
        print ("Downloading firmware.hex...")
        download(self.firmware_url, self.firmware_path)


def main(args):
    if args.port:
        port_name = args.port
    else:
        port_name = get_uarm_port_cli()
    if args.path:
        firmware_path = args.path
    else:
        firmware_path = os.path.join(os.getcwd(), default_config['filename'])

    if args.download:
        download(default_config['download_url'], firmware_path)

    flash(port_name, firmware_path)

if __name__ == '__main__':
    try:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", help="specify port number")
        parser.add_argument("--path", help="firmware path")
        parser.add_argument("-d", "--download",
                        help="download firmware from {}".format(default_config['download_url']),
                        action="store_true")
        args = parser.parse_args()
        main(args)
    except SystemExit:
        exit_fun()


