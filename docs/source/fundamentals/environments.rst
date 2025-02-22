.. _environments:

Environments
============
.. tip::
    👉 Would you rather watch a short video tutorial? Check it our here: `installing additional
    packages <https://app.tella.tv/story/cknr8owf4000308kzalsk11a5>`_.

The scripts and Notebooks that are pointed to by pipeline steps are executed within their own
environment when doing a pipeline run. When editing Notebooks, the respective kernel runs within an
environment as well! On step creation (or when editing the step) you can choose the environment it
should use.

Essentially, Orchest's environments define the execution environment in which the scripts and
kernels are executed. Therefore, if you want to use additional packages within scripts, then they
need to be installed in their respective environment.

Lastly, environments are part of a single project and included when versioning. This ensures that
you can get started immediately when importing an existing project without having to recreate the
same environment.

Choosing a programming language
-------------------------------

An environment is always specifically used for one programming language. This avoids bloating
the container image of the environment to include dependencies for multiple languages.


Orchest has built in support for environments with the languages:

* Python
* R
* JavaScript
* Julia

Each environment supports ``Bash`` scripts. This can also be used to invoke any other language indirectly.
Like Java, Scala, Go or C++ based steps.

Important paths inside environments
-----------------------------------
Whenever code is executed in an environment a number of paths are mounted to the container that you
can access from within your code. These paths are:

``/data``
    This directory should be used to write large artifacts and/or data to. Writing it to other
    locations might lose your data (since the environments are stateless) or bloat your project
    directory (which will slow down :ref:`job <jobs>` creation).

``/project-dir``
    This directory contains all files from your :ref:`project <projects>` and is the working
    directory when building the environment. This means that you can do:

    .. code-block:: bash

       #!/bin/bash
       pip install -r requirements.txt

Building an environment
-----------------------
1. Go to *Environments* in the left menu pane.
2. Create a new *Environment*.
3. Choose an *Environment name*.
4. Choose a base image. This image will be extended through your setup bash script.
5. To keep environment image sizes to a minimal, each environment is tied to a specific programming
   language. Choose one of the supported languages for your environment.
6. Go to the *BUILD* tab to install additional packages by adding their installation steps to the *Environment set-up
   script*. This is where you enter your installation commands, e.g. :code:`pip install tensorflow`
   or :code:`sudo apt-get install gcc`.
7. Finally, press the *Build* button at the bottom.

.. note::
   💡 When updating an existing environment, the new environment will automatically be used inside
   the visual editor (and for your :ref:`interactive pipeline runs <interactive pipeline run>`).

.. _install packages:

Installing additional packages
------------------------------
.. warning::
   🚨 Do not install packages by running :code:`!pip install <package-name>` inside your
   Jupyter Notebook. This causes the package to be installed every time you run the pipeline
   step. It is not saved in the environment as containers are stateless!

Installing additional packages is as easy as building a new version of your environment that
includes the packages you need, simply follow the steps in the previous section. An example
*Environment set-up script*:

.. code-block:: bash

   #!/bin/bash

   # Get system level dependencies for one of your packages
   sudo apt-get install -y default-libmysqlclient-dev

   # Install any dependency using mamba or conda
   mamba install -y spacy -c conda-forge

   # Or, alternatively, install Python dependencies using pip
   pip install black

.. note::
   💡 `mamba <https://mamba.readthedocs.io/>`_ is a drop-in replacement to conda
   that is more user friendly and faster. Installing packages with conda is also supported,
   but conda might need a long time to solve the environment.

.. note::
   💡 ``pip``, ``mamba`` and ``conda`` caches are persisted across builds for quicker iterations.
   Said cache can be ignored or removed using the respective flags (e.g. ``pip install --no-cache``)
   or commands.

Creating a custom environment image
-----------------------------------
Bringing your own fully custom environment image is not recommended as Orchest requires a certain
structure of the image to work correctly. Due to the dependency on the Jupyter Docker stacks and the
ability of the environments to work for pipeline runs and to host active Jupyter kernels, we
recommend using our provided base images for the :ref:`environments <environments>` instead and
using the *set-up script* to customize the environments according to your needs.

Using a different Python version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
It might be the case that your code requires another Python version than we are offering. Luckily
with environments it is easy to set up the Python version you require.

To do this, create the new conda environment in your setup script with your desired Python version
and store the relevant environment variables in ``/home/jovyan/.orchestrc``,
which will be sourced on startup.
For example, to configure an environment with Python 3.10 using mamba, add these commands:

.. code-block:: bash

   #!/bin/bash
   # Install Python 3.10 and get minimum set of dependencies
   mamba create -y -n py310 python=3.10 future
   mamba install -y -n py310 ipykernel jupyter_client ipython_genutils pycryptodomex future "pyarrow<8.0.0"
   mamba run -n py310 pip install orchest

   # Jupyter environment variable that specifies
   # a path to search for kernels data files
   # See https://jupyter-core.readthedocs.io/en/latest/paths.html
   echo "export JUPYTER_PATH=/opt/conda/envs/py310/share/jupyter" >> /home/jovyan/.orchestrc

   # Orchest related environment variable that can be set to specify
   # the conda environment to use to start Jupyter kernels
   echo "export CONDA_ENV=py310" >> /home/jovyan/.orchestrc
