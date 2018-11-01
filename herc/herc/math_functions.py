#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  2 16:50:29 2018

@author: zdhughes

https://stackoverflow.com/questions/30677241/how-to-limit-cross-correlation-window-width-in-numpy
"""

import numpy as np
from numpy.lib.stride_tricks import as_strided
import matplotlib.pyplot as plt


def _check_arg(x, xname):
    x = np.asarray(x)
    if x.ndim != 1:
        raise ValueError('%s must be one-dimensional.' % xname)
    return x

def _autocorrelation(x, maxlag):
    """
    Autocorrelation with a maximum number of lags.

    `x` must be a one-dimensional numpy array.

    This computes the same result as
        numpy.correlate(x, x, mode='full')[len(x)-1:len(x)+maxlag]

    The return value has length maxlag + 1.
    """
    x = _check_arg(x, 'x')
    p = np.pad(x.conj(), maxlag, mode='constant')
    T = as_strided(p[maxlag:], shape=(maxlag+1, len(x) + maxlag),
                   strides=(-p.strides[0], p.strides[0]))
    return T.dot(p[maxlag:].conj())


def _crosscorrelation(x, y, maxlag):
    """
    Cross correlation with a maximum number of lags.

    `x` and `y` must be one-dimensional numpy arrays with the same length.

    This computes the same result as
        numpy.correlate(x, y, mode='full')[len(a)-maxlag-1:len(a)+maxlag]

    The return vaue has length 2*maxlag + 1.
    """
    x = _check_arg(x, 'x')
    y = _check_arg(y, 'y')
    py = np.pad(y.conj(), 2*maxlag, mode='constant')
    T = as_strided(py[2*maxlag:], shape=(2*maxlag+1, len(y) + 2*maxlag),
                   strides=(-py.strides[0], py.strides[0]))
    px = np.pad(x, maxlag, mode='constant')
    return T.dot(px)

def autocorrelation(x, maxlag):
	
	result = _autocorrelation(x, maxlag)
	lags = np.arange(maxlag+1)
	markerline, stemlines, baseline = plt.stem(lags, result, '-.')
	plt.show()
	
def crosscorrelation(x, y, maxlag):
	
	result = _crosscorrelation(x, y, maxlag)
	lags = np.arange(-maxlag, maxlag+1)
	markerline, stemlines, baseline = plt.stem(lags, result, '-.')
	plt.show()
	
	return result
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	