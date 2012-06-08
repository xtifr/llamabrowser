from distutils.core import setup

setup(name='llamabrowser',
      version='0.1',
      description="Live Music Archive browser",
      author="Chris Waters",
      author_email="xtifr.w@gmail.com",
      url="https://github.com/xtifr/llamabrowser",
      packages=['lma'],
      py_modules=['wxui'],
      scripts=['llama'],
      )
