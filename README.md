# IoTSecFuzz
{: .gitlab-purple}

#### Invuls CTF Team Project - Copyright 2018

### Written by: Ilya Shaposhnikov (@drakylar), Sergey Bliznyuk (@bronzebee) and Sofia Marakhovich (@Soff).
{: .gitlab-purple}


### Twitter: [@iotsecfuzz](https://twitter.com/iotsecfuzz/)

### Email: iotsecfuzz@gmail.com


#### What is IoTSecFuzz?

**IoTSecFuzz(ISF)** was created with the aim of combining the maximum number of utilities for comprehensive testing of IoT device security at all levels of implementation. It has a convenient console in order to use it as a stand-alone application, as well as the ability to import it as a library.

   The key aspects of the tool has become a flexible modular system with the ability to add your own modules and combine them.

### Structure

The framework has the ability to operate with the tested device at three levels:

- hardware (debugging interfaces)
- firmware (reverse engineering of the device’s OS)
- communication (NRF24, Bluetooth, Wifi, ip-networking).

### Installation



#### Framework installation

Make sure you have Python 3.7 or later installed.
Upgrade _setuptools_ to the latest version as ISF requires PEP 420 support:
```bash
pip3 install --upgrade setuptools
```

Now you can install the framework from Gitlab:

```bash
git clone https://gitlab.com/invuls/iot-projects/iotsecfuzz.git

cd iotsecfuzz

python3 setup.py install
```

#### Module installation

##### ISFPM

The framework comes with tiny bundled package manager named ISFPM.
It is capable of resolving module dependencies and makes installation process much easier.


```bash
root@kali:/$ isfpm install -h
usage: isfpm install [-h] [--no-deps] [--home HOME] module [module ...]

positional arguments:
  module       either module qualified name, path to local directory or path
               to local tarball

optional arguments:
  -h, --help   show this help message and exit
  --no-deps    skip dependency resolution stage
  --home HOME  framework home directory
```

To install the module by its name, e.g. module _hardware/uboot_, use:
```bash
isfpm install hardware/uboot
```

All of the standard modules are installed automatially after framework setup has finished.

### Features

- Open Source
- A familiar and native management system like in a Metasplit
- Ability to add modules yourself(python3) 

#### Main modules list
The following modules are available in the framework (10.08.2019):

1. [avrloader](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/hardware/avrloader) - secondary module for arduino auto code compilation/upload.
2. [ble_tool](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/radio/bluetooth/ble_tool) (instable) - module for BLE-communication.
3. [cfe](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/hardware/cfe) - communication with CFE bootloader using UART
4. [extractor](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/hardware/extractor) - forensics tool for memory dump with firmware (based by binwalk and cpu_rec API)
5. [goldfinder](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/software/goldfinder) - firmwalker analog (find interesting information in unpacked firmware filesystem)
6. [logic_analyzer](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/hardware/logic_analyzer) - uses avrloader for programming arduino for using it as a logic analyzer and exporting results (for example, creating graph in auto-mode)
7. [mqttmaaker](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/radio/tcpip/mqttaker) - module for MQTT-communication
8. [realtek](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/hardware/realtek) - communication with Realtek bootloader using UART
9. [ubertooth](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/radio/bluetooth/ubertooth) - uses pyubertooth library for communication in Ubertooth
10. [ttltalker](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/hardware/ttltalker) - secondary module for UART communication.
11. [uboot](https://gitlab.com/invuls/iot-projects/iotsecfuzz-modules/hardware/uboot) - communication with U-Boot bootloader using UART



#### Console UI

Welcome!
![](https://i.imgur.com/t8Ejwey.png)

Commands:
![](https://i.imgur.com/8pa1Hm6.png)

Example CLI usage (with ttltalker module):
![](https://i.imgur.com/8EtGrGd.gif)


Dumping firmware from U-Boot UART CLI:

![](https://cdn.discordapp.com/attachments/140787642647183360/508664495883681792/image1.jpg)
![](https://media.discordapp.net/attachments/140787642647183360/508664821906931713/image0.jpg?width=1462&height=1097)


[![asciicast](https://asciinema.org/a/262659.svg)](https://asciinema.org/a/262659)


Dumping firmware from CFE UART CLI:
[![asciicast](https://asciinema.org/a/262619.svg)](https://asciinema.org/a/262619)





#### API
Cерега

#### Module creation


##### Dependencies

Install python3-venv:
```bash
apt-get install python3-venv
```

##### Command info

```bash
isfpm init -h
usage: isfpm init [-h] [--no-venv] [--pycharm] [--no-git]

optional arguments:
  -h, --help  show this help message and exit
  --no-venv   skip virtual environment creation and use current Python
              interpreter
  --pycharm   initialize environment for JetBrains PyCharm
  --no-git    skip Git repository creation
```

##### First step

Create an empty folder and start module initialization.

```bash
root@kali:/tmp# mkdir test_module
root@kali:/tmp# cd test_module/
root@kali:/tmp/test_module# isfpm init 
[*] This utility will walk you through creating environment for your ISF module.
[*] It will set up the necessary file structure and the manifest.json file.
[?] Enter module name (test_module): test_module1                   
[?] Enter module version (1.0.0): 0.1.0                             
[?] Enter module category (hardware): firmware                     
[?] Enter module description: Test module firmware   
[?] Enter module authors name (root): Invuls                     
[?] Enter module license (MIT): MIT                                 
[*] Resulting manifest.json file:
{
  "manifest-version": 1,
  "name": "test_module1",
  "version": "0.1.0",
  "category": "firmware",
  "description": "Test module firmware",
  "authors": [
    "Invuls"
  ],
  "license": "MIT",
  "input": {},
  "dependencies": {}
}
[?] Is this OK? (Yes): Yes

[*] Writing manifest.json file
[*] Creating directories
[*] Generating run scripts
[*] Creating virtual environment
[*] Upgrading setuptools
[*] Installing requirements
[*] Creating git repository
[*] Adding files
[*] Environment setup finished successfully!
root@kali:/tmp#
```

##### Module filesystem
```bash
root@kali:/tmp/test_module# tree
.
├── isf
│   └── firmware
│       └── test_module1
│           ├── __init__.py
│           └── resources
│               ├── __init__.py
│               └── manifest.json
├── out
├── requirements.txt
├── scripts
│   ├── debug.py
│   └── start.py
├── setup.py
└── venv

7 directories, 7 files
root@kali:/tmp/test_module# 
```

/usf/firmware/test_module1/resources/manifest.json:
(need some editions -check comments)
```python
{
  "manifest-version": 1,
  "name": "test_module1",
  "version": "0.1.0",                    #module version
  "category": "firmware",
  "description": "Test module firmware",
  "type":"container",                    #container - module class with submodules == functions
  "container-class": "TestClass",        #name of container class
  "authors": [
    "Invuls"
  ],
  "license": "MIT",
  "input": {
      "glob_param1": {
              "description": "Global param for submodules",
              "type": "string",                             #boolean, int etc
              "required": false,
              "default-value": "def_value"
            }
  },
  "submodules":{
    "test_submodule": {
          "description": "Test submodule-function test_submodule(...)",
          "run-policy": "foreground-only",
          "input": {
            "submodule_param1": {
              "description": "Param only for submodule",
              "type": "string",
              "required": true
            }
          }
        }
  },
  "dependencies": {}
}

```

/usf/firmware/test_module1/\_\_init\_\_.py:
```python
from isf.core import logger

class TestClass:

	glob_param1 = ''
	def __init__(self, glob_param1='def_value'):
		self.glob_param1 = glob_param1

	def __del__(self):
		del self.glob_param1

	def test_submodule(self, submodule_param1):
		logger.info('Global param: {}'.format(self.glob_param1))
		logger.warning('Local parama: {}'.format(submodule_param1))
```

##### Run example

[![asciicast](https://asciinema.org/a/263291.svg)](https://asciinema.org/a/263291)


#### Issues module fix

Every module has its own repository, where everyone can create issues (if there will be any bugs) or create requests for features. 

### TODO

#### New modules

- Fast top-password protocol bruteforce
- Automatic JTAGenum to python API tool.
- ModBus communication module
- JTAGulator API
- Arduino SPI/I2C flash dump
- Bruteforce
- ARP attacks module

#### Core tasks
- GUI
- Official site
- Modules workshop
- CVE category
- Public Relations for modules creation/optimisation.

### License
This project is licensed under the MIT License.