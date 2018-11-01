# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 11:59:54 2016

@author: zdhughes

This runs fermi tools outside the fermi enviornment. Call with subprocess.call('. /path/to/fermi-init.sh && python /path/to/anaconda2fermi.py tool parameters usePython color, shell=True)
tool is gt_app.tool and parameters is a json.dumps converted dict of the parameters to set.
"""

import subprocess
import sys
import gt_apps
from io_functions import colors
import json

def setPythonApp(tool, parameters):
	
	app = eval('gt_apps.'+tool)
	
	for parameter in parameters:
		if parameter in app.params:
			app[parameter] = parameters[parameter]
			
	return app

def setCliApp(tool, parameters):
	
	strings = [x.strip() + '=' + parameters[x].strip() for x in parameters]
	args = ' '.join(strings)
	return args

	
if 	__name__ == '__main__':
	 	
	garbage, tool, parameters, usePython, color = sys.argv

	parameters = json.loads(parameters)
	parameters = {str(key):str(value) for key, value in parameters.items()}
	
	try:
		c = colors()
		if color.lower() == 'true':
			c.enableColors()
	except:
		pass

	if usePython.lower() == 'true':
		
		app = setPythonApp(tool, parameters)
		print('Calling: \n\n'+c.purple(app.command())+'\n\n')
		print('Running '+tool+'...')
		app.run()
		print('\n')	
		
	elif usePython.lower() == 'false':
		
		args = setCliApp(tool, parameters)	
		print('Calling: \n\n'+c.purple(tool + ' ' + args)+'\n\n')
		print('Running '+tool+'...')
		subprocess.call(tool + ' ' + args, shell = True)
		print('\n')	
	
	else:
		print(c.red('Something went wrong.'))
