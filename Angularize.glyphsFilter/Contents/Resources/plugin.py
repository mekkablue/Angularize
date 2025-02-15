# encoding: utf-8

###########################################################################################################
#
#
# Filter with dialog Plugin
#
# Read the docs:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Filter%20with%20Dialog
#
# For help on the use of Xcode:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import Glyphs, GSPath, GSNode, GSPathSegment, GSSHARP, LINE, CURVE, OFFCURVE
from GlyphsApp.plugins import FilterWithDialog
from AppKit import NSPoint
from copy import copy


def calculateBezierSegmentLength(p0, p1, p2, p3):
	calcSegment = GSPathSegment.alloc().initWithCurvePoint1_point2_point3_point4_options_(p0, p1, p2, p3, 0)
	return calcSegment.length()


def calculateBezierPoint(t, A, B, C, D):
	"""
	Returns coordinates for t (=0.0...1.0) on curve segment.
	x1,y1 and x4,y4: coordinates of on-curve nodes
	x2,y2 and x3,y3: coordinates of BCPs
	"""
	x1, y1 = A.x, A.y
	x2, y2 = B.x, B.y
	x3, y3 = C.x, C.y
	x4, y4 = D.x, D.y
	
	x = x1*(1-t)**3 + x2*3*t*(1-t)**2 + x3*3*t**2*(1-t) + x4*t**3
	y = y1*(1-t)**3 + y2*3*t*(1-t)**2 + y3*3*t**2*(1-t) + y4*t**3

	return x, y


def divideSegment(length, A, B, C, D):
	segmentLength = calculateBezierSegmentLength(
		A.position,
		B.position,
		C.position,
		D.position,
		)
	parts = int(round(segmentLength / length))
	nodes = []
	for i in range(1, parts+1):
		t = i * (1.0 / parts)
		x, y = calculateBezierPoint(t, A, B, C, D)
		newNode = GSNode()
		newNode.position = NSPoint(x, y)
		newNode.type = LINE
		newNode.connection = GSSHARP
		nodes.append(newNode)
	return nodes


def turnCurveToLinesOnLayer(layer, length=100):
	for path in layer.paths:
		newPath = GSPath()
		for node in path.nodes:
			if node.type == LINE: # LINE, CURVE or OFFCURVE
				newNode = copy(node)
				newNode.connection = GSSHARP
				newPath.nodes.append(newNode)
			elif node.type == CURVE:
				newNodes = divideSegment(
					max(3.0, length), # sanity check: min length of 3 
					node.prevNode.prevNode.prevNode,
					node.prevNode.prevNode,
					node.prevNode,
					node,
					)
				for newNode in newNodes:
					newPath.nodes.append(newNode)
			else:
				continue
		newPath.closed = path.closed
		path.nodes = newPath.nodes


class Angularize(FilterWithDialog):

	# Definitions of IBOutlets

	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()

	# Text field in dialog
	segmentLengthField = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': 'Angularize',
		})

		# Word on Run Button (default: Apply)
		self.actionButtonLabel = Glyphs.localize({
			'en': 'Angularize',
		})

		# Load dialog from .nib (without .extension)
		self.loadNib('IBdialog', __file__)

	# On dialog show
	@objc.python_method
	def start(self):

		# Set default value
		Glyphs.registerDefault(
			'com.mekkablue.Angularize.segmentLength',
			15.0,
			)

		# Set value of text field
		self.segmentLengthField.setStringValue_(
			Glyphs.defaults['com.mekkablue.Angularize.segmentLength']
			)

		# Set focus to text field
		self.segmentLengthField.becomeFirstResponder()


	# Action triggered by UI
	@objc.IBAction
	def setSegmentLength_(self, sender):

		# Store value coming in from dialog
		Glyphs.defaults['com.mekkablue.Angularize.segmentLength'] = sender.floatValue()

		# Trigger redraw
		self.update()


	# Actual filter
	@objc.python_method
	def filter(self, layer, inEditView, customParameters):
		segmentLength = float(Glyphs.defaults['com.mekkablue.Angularize.segmentLength'])
		
		# Called on font export, get value from customParameters
		if "segmentLength" in customParameters:
			segmentLength = float(customParameters['segmentLength'])

		# Shift all nodes in x and y direction by the value
		turnCurveToLinesOnLayer(layer, length=segmentLength)


	@objc.python_method
	def generateCustomParameter(self):
		return "%s; segmentLength:%s;" % (
			self.__class__.__name__,
			Glyphs.defaults['com.mekkablue.Angularize.segmentLength'],
			)


	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
