import setuptools


setuptools.setup(
    name='base16_shell_preview',
    version='0.3.0',
    description='Browse and preview Base16 Shell themes in your terminal.',
    long_description=open('README.rst').read(),
    author='Andrew Rabert',
    author_email='arabert@nullsum.net',
    url='https://github.com/nvllsvm/base16-shell-preview',
    license='MIT',
    packages=['base16_shell_preview'],
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ),
    entry_points={
        'console_scripts': ['base16-shell-preview=base16_shell_preview:main']
    }
)
