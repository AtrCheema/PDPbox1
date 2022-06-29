from setuptools import setup
import versioneer

setup(name='PDPbox',
      packages=['pdpbox'],
      package_data={'pdpbox': ['datasets/*/*']},
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='python partial dependence plot toolbox',
      author='AtrCheema',
      author_email='ather_abbas786@yahoo.com',
      url='https://github.com/AtrCheema/PDPbox1',
      license='MIT',
      classifiers = [],
      install_requires=[
          'pandas',
          'numpy',
          'scipy',
          'joblib',
          'psutil',
          'matplotlib',
          'sklearn'
      ],
      extra_require={
          "mini": ['pandas', 'numpy', 'matplotlib']
      },
      zip_safe=False
      )
