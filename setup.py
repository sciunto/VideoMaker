#!/usr/bin/env python

from distutils.core import setup
import info

setup(
    name         = 'VideoMaker',
    version      = info.VERSION,
    url          = info.URL,
    author       = "Francois Boulogne",
    license      = info.LICENSE,
    author_email = info.EMAIL,
    description  = info.SHORT_DESCRIPTION,
    scripts     = ['videomaker.py'],
)
