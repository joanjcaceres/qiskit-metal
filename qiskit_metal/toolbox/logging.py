# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Created 2019

File contains some config definitions. Mostly internal.

@author: Zlatko K. Minev
"""

import logging

def setup_logger(logger_name,
                 log_format,
                 log_datefmt,
                 level_stream=logging.INFO,
                 level_base=logging.DEBUG):
    '''
    Setup the logger to work with jupyter and command line.

    `level_stream` and `level_base`:
    You can set a different logging level for each logging handler, however you have
    to set the logger's level to the "lowest".

    Integrates logging with the warnings module.

    To see the logging levels you can use:
    ```
        print(logger)
        print(logger.zkm_c_handler)
        print(gui._log_handler)
    ```
    '''
    # Logging levels: https://stackoverflow.com/questions/11111064/how-to-set-different-levels-for-different-python-log-handlers

    logger = logging.getLogger(logger_name)  # singleton

    if not len(logger.handlers):

        # Used to integrate logging with the warnings module.
        # Warnings issued by the warnings module will be redirected to the logging system.
        # Specifically, a warning will be formatted using warnings.formatwarning() and the resulting
        # string logged to a logger named 'py.warnings' with a severity of WARNING.
        logging.captureWarnings(True)

        # Sends logging output to streams such as sys.stdout, sys.stderr or any file-like object
        c_handler = logging.StreamHandler()

        # Jupyter notebooks already has a stream handler on the default log.
        # Do not propage upstream to the root logger.
        # https://stackoverflow.com/questions/31403679/python-logging-module-duplicated-console-output-ipython-notebook-qtconsole
        logger.propagate = False

        # Format. Unlike the root logger, a custom logger can't be configured using basicConfig().
        c_format = logging.Formatter(log_format, datefmt=log_datefmt)
        c_handler.setFormatter(c_format)

        # Add Hanlder with format and set level
        logger.addHandler(c_handler)
        logger.setLevel(level_base)
        c_handler.setLevel(level_stream)

        logger.zkm_c_handler = c_handler
        logger.zkm_c_format = c_format

    return logger