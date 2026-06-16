Paint Robot Documentation
==========================

Welcome to the Paint Robot documentation. This project provides a comprehensive Python package
for controlling and optimizing paint robot operations.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   api/paintbot

Getting Started
---------------

To get started with the Paint Robot package:

1. **Installation**: Install the package using ``pip install -e .``
2. **Research**: Use the main notebook (``main.ipynb``) for experimentation
3. **Development**: Extend the ``paintbot`` package with new features

Core Modules
------------

The ``paintbot`` package includes:

- **Robot**: Main class for hardware control and movement
- **Painter**: Paint application and color management
- **Calibration**: Robot calibration utilities

Quick Example
-------------

.. code-block:: python

    from paintbot import Robot, Painter

    # Initialize robot and painter
    robot = Robot("PaintBot")
    painter = Painter(color=(255, 0, 0), flow_rate=75.0)

    # Move to position and paint
    robot.move_to(10, 20, 5)
    painter.start_painting()
    # ... perform painting operations ...
    painter.stop_painting()
    robot.home()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
