from setuptools import setup
import os
from glob import glob

package_name = 'opt_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')) ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dianoandre',
    maintainer_email='tua_email@example.com',
    description='Descrizione del pacchetto',
    license='License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)
