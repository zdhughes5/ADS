from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.artist as art
import pyqtgraph as pg
import numpy as np

class SimplePlotCavas(FigureCanvas):
	def __init__(self):
		self.fig = Figure()
		self.ax = self.fig.add_subplot(111)
		FigureCanvas.__init__(self, self.fig)
		FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

class TwinAxisCanvas(FigureCanvas):
	def __init__(self):
		self.fig = Figure()
		self.ax1 = self.fig.add_subplot(111)
		self.ax2 = self.ax1.twinx()
		FigureCanvas.__init__(self, self.fig)
		FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)
		
class TripleAxisCanvas(FigureCanvas):
	def __init__(self):
		self.fig = Figure()
		self.ax1 = self.fig.add_subplot(311)
		self.ax2 = self.fig.add_subplot(312, sharex = self.ax1, sharey = self.ax1)
		self.ax3 = self.fig.add_subplot(313, sharex = self.ax1, sharey = self.ax1)
		self.ax1.set_ylim(-0.2,1.5)
		self.fig.subplots_adjust(hspace=0)
		art.setp(self.ax1.get_xticklabels(), visible=False)
		art.setp(self.ax2.get_xticklabels(), visible=False)
		FigureCanvas.__init__(self, self.fig)
		FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)
		
class ThirtyAxisCanvas(FigureCanvas):
	def __init__(self):
		self.fig = Figure(figsize=(8, 100), dpi=100)
		self.ax0 = self.fig.add_subplot(30, 1, 1)
		self.ax1 = self.fig.add_subplot(30, 1, 2, sharex = self.ax0, sharey = self.ax0)
		self.ax2 = self.fig.add_subplot(30, 1, 2, sharex = self.ax0, sharey = self.ax0)
		self.ax3 = self.fig.add_subplot(30, 1, 3, sharex = self.ax0, sharey = self.ax0)
		self.ax4 = self.fig.add_subplot(30, 1, 4, sharex = self.ax0, sharey = self.ax0)
		self.ax5 = self.fig.add_subplot(30, 1, 5, sharex = self.ax0, sharey = self.ax0)
		self.ax6 = self.fig.add_subplot(30, 1, 6, sharex = self.ax0, sharey = self.ax0)
		self.ax7 = self.fig.add_subplot(30, 1, 7, sharex = self.ax0, sharey = self.ax0)
		self.ax8 = self.fig.add_subplot(30, 1, 8, sharex = self.ax0, sharey = self.ax0)
		self.ax9 = self.fig.add_subplot(30, 1, 9, sharex = self.ax0, sharey = self.ax0)
		self.ax10 = self.fig.add_subplot(30, 1, 10, sharex = self.ax0, sharey = self.ax0)
		self.ax11 = self.fig.add_subplot(30, 1, 11, sharex = self.ax0, sharey = self.ax0)
		self.ax12 = self.fig.add_subplot(30, 1, 12, sharex = self.ax0, sharey = self.ax0)
		self.ax13 = self.fig.add_subplot(30, 1, 13, sharex = self.ax0, sharey = self.ax0)
		self.ax14 = self.fig.add_subplot(30, 1, 14, sharex = self.ax0, sharey = self.ax0)
		self.ax15 = self.fig.add_subplot(30, 1, 15, sharex = self.ax0, sharey = self.ax0)
		self.ax16 = self.fig.add_subplot(30, 1, 16, sharex = self.ax0, sharey = self.ax0)
		self.ax17 = self.fig.add_subplot(30, 1, 17, sharex = self.ax0, sharey = self.ax0)
		self.ax18 = self.fig.add_subplot(30, 1, 18, sharex = self.ax0, sharey = self.ax0)
		self.ax19 = self.fig.add_subplot(30, 1, 19, sharex = self.ax0, sharey = self.ax0)
		self.ax20 = self.fig.add_subplot(30, 1, 20, sharex = self.ax0, sharey = self.ax0)
		self.ax21 = self.fig.add_subplot(30, 1, 21, sharex = self.ax0, sharey = self.ax0)
		self.ax22 = self.fig.add_subplot(30, 1, 22, sharex = self.ax0, sharey = self.ax0)
		self.ax23 = self.fig.add_subplot(30, 1, 23, sharex = self.ax0, sharey = self.ax0)
		self.ax24 = self.fig.add_subplot(30, 1, 24, sharex = self.ax0, sharey = self.ax0)
		self.ax25 = self.fig.add_subplot(30, 1, 25, sharex = self.ax0, sharey = self.ax0)
		self.ax26 = self.fig.add_subplot(30, 1, 26, sharex = self.ax0, sharey = self.ax0)
		self.ax27 = self.fig.add_subplot(30, 1, 27, sharex = self.ax0, sharey = self.ax0)
		self.ax28 = self.fig.add_subplot(30, 1, 28, sharex = self.ax0, sharey = self.ax0)
		self.ax29 = self.fig.add_subplot(30, 1, 29, sharex = self.ax0, sharey = self.ax0)
		self.ax1.set_ylim(-0.2, 130)
		self.fig.subplots_adjust(hspace=0)
		art.setp(self.ax1.get_xticklabels(), visible=False)
		art.setp(self.ax2.get_xticklabels(), visible=False)		
		FigureCanvas.__init__(self, self.fig)
		FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)	
	
class SimplePlotWidget(QtWidgets.QWidget):
	def __init__(self, parent = None):
		QtWidgets.QWidget.__init__(self, parent)
		self.canvas = SimplePlotCavas()
		self.vbl = QtWidgets.QVBoxLayout()
		self.vbl.addWidget(self.canvas)
		self.setLayout(self.vbl)
		
class SimplePlotWidgetNTB(QtWidgets.QWidget):
	def __init__(self, parent = None):
		QtWidgets.QWidget.__init__(self, parent)
		self.canvas = SimplePlotCavas()
		self.vbl = QtWidgets.QVBoxLayout()
		self.ntb = NavigationToolbar(self.canvas, self)
		self.vbl.addWidget(self.canvas)
		self.vbl.addWidget(self.ntb)
		self.setLayout(self.vbl)

class TraceWidget(QtWidgets.QWidget):
	def __init__(self, parent = None):
		QtWidgets.QWidget.__init__(self, parent)
		self.canvas = TwinAxisCanvas()
		self.vbl = QtWidgets.QVBoxLayout()
		self.ntb = NavigationToolbar(self.canvas, self)
		self.vbl.addWidget(self.canvas)
		self.vbl.addWidget(self.ntb)
		self.setLayout(self.vbl)
		
class FADCWidget(QtWidgets.QWidget):
	def __init__(self, parent = None):
		QtWidgets.QWidget.__init__(self, parent)
		self.canvas = ThirtyAxisCanvas()
		self.vbl = QtWidgets.QVBoxLayout()
		self.ntb = NavigationToolbar(self.canvas, self)
		self.vbl.addWidget(self.canvas)
		self.vbl.addWidget(self.ntb)
		self.setLayout(self.vbl)
		
class pgCanvas(pg.GraphicsLayoutWidget):
	def __init__(self, parent = None):
		pg.GraphicsLayoutWidget.__init__(self)

		self.plotChannel = []
		self.dataChannel = []
		self.finallyMaybe = []
		data = np.random.normal(size=(100))

		for i in range(30):
			self.plotChannel.append(self.addPlot(row=i, col=1))
			self.plotChannel[i].showGrid(x = True, y = True, alpha = 0.3)
			if i > 0:
				self.plotChannel[i].setXLink(self.plotChannel[0])
			if i < 29:
				self.plotChannel[i].getAxis('bottom').setStyle(showValues=False)
				self.plotChannel[i].getAxis('bottom').showLabel(False)
			self.plotChannel[i].setYRange(-1, 100)
			self.plotChannel[i].setLabel('left', text='Channel '+str(i)+' [ADC]')
			self.plotChannel[i].setMouseEnabled(x=False, y=False)
			self.dataChannel.append(self.plotChannel[-1].plot(data))
			#print(self.plotChannel[-1])
			#print(self.dataChannel[-1])
			
	def clearAll(self):
		for i in self.plotChannel:
			i.clear()

		
#class pgWidget(QtWidgets.QGraphicsView):
#	def __init__(self, parent = None):
#		QtWidgets.QGraphicsView.__init__(self, parent)
#		self.canvas = pgCanvas()
		
		
		
		
		
		
		
		
		
		
		
		