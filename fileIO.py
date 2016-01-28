# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        fileIO.py for python 3.x
# Purpose:     fuctions to save/load python objects to/from disk
#
# Author:      Claudio Piccinini
#
# Created:     31-05-2013, revised 24/06/2014
# -------------------------------------------------------------------------------

# import sys
# set module path for pydoc documentation
# sys.path.append(r'')

import pickle


def save_object(f, ob):
    """Save an object on disk

    :param f: file path
    :param ob: object to save
    :return: None
    """

    out = None
    try:
        out = open(f, 'wb')
        pickle.dump(ob, out)
    except Exception as e:
        raise e
    finally:
        if out is not None:
            out.close()


def load_object(f):
    """Load an object from disk
    :param f: file path
    :return: None
    """
    a = None
    b = None
    try:
        a = open(f,'rb')
        b = pickle.load(a)
        a.close()
    except Exception as e:
        raise e
    finally:
        if a is not None:
            a.close()
        if b is not None:
            return b