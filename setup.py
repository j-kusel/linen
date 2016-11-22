from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='linen',
    version='1.3',
    description='Fabric wrapper for automated Django/Apache/MySQL deployments',
    long_description=readme(),
    classifiers = [
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Programming Language :: SQL',
        'Framework :: Django :: 1.10',
    ],
    url='http://github.com/ultraturtle0/linen',
    author='Jordan Kusel',
    author_email='jordankusel@my.unt.edu',
    license='GNU GPLv3+',
    packages=['linen','linen.templates'],
    install_requires=[
        'fabric3',
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    entry_points = {
        'console_scripts': ['linen=linen.LinenCore:main'],
    },
    zip_safe=False)
