from setuptools import setup

setup(name='IotSecFuzz',
      version='0.1',
      description='IoT security testing framework',
      author='Not_so_sm4rt_hom3 team',
      packages=['core', 'util'],
      install_requires=[
          'tabulate',
          'termcolor',
          'serial',
          'scapy'
      ],
      zip_safe=False)
