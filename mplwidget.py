from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.artist as art

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
		self.canvas = TripleAxisCanvas()
		self.vbl = QtWidgets.QVBoxLayout()
		self.ntb = NavigationToolbar(self.canvas, self)
		self.vbl.addWidget(self.canvas)
		self.vbl.addWidget(self.ntb)
		self.setLayout(self.vbl)
		

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		