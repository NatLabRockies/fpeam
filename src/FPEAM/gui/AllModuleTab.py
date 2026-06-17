import logging
import os
import sys
import tempfile
import threading
import time

import numpy as np
import seaborn as sns
from AttributeValueStorage import AttributeValueStorage
from FPEAM import (IO, FPEAM)
from MovesConfig import movesConfigCreation
from NonroadConfig import nonroadConfigCreation
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtGui import QDoubleValidator, QPixmap
from PyQt5.QtWidgets import QComboBox, QPushButton, QFileDialog, QPlainTextEdit, \
    QScrollArea, QProgressBar, QDockWidget
from PyQt5.QtWidgets import QGridLayout, QLabel, QLineEdit, QSpinBox, QCheckBox
from emissionFactorsConfig import emissionFactorsConfigCreation
from fugitiveDustConfig import fugitiveDustConfigCreation
from matplotlib import pyplot as plt
from run_config import runConfigCreation

WIDTH = 890
HEIGHT = 650


# Provides resize event to mainWindow
class Window(QtWidgets.QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(Window, self).__init__(parent=parent)
        self.resized.connect(self.resizeDependentUiObjects)
        scrollArea = []

    def setSizeDependency(self, scrollAreaList):
        self.scrollAreaList = scrollAreaList

    def resizeEvent(self, event):
        self.resized.emit()
        return super(Window, self).resizeEvent(event)

    def resizeDependentUiObjects(self):
        for scrollArea in self.scrollAreaList:
            scrollArea.resize(self.width(), self.height() - 222)


class AlltabsModule(QtWidgets.QWidget):

    # Function to adjust all tab's position ( Currently disabled.
    # It can be changed by modifying the default values of leftSpaces and rightSpaces)
    def getSpacedNames(self, name, leftSpaces=0, rightSpaces=0):
        halfNameLen = int(len(name) / 2)
        return "".join([" "] * (leftSpaces - halfNameLen)) + name + "".join([" "] * (rightSpaces - halfNameLen))

    # Set Height and Width to a label as width=170 and height=40
    def createLabelBig(self, text, width=170, height=40):
        label = QLabel()
        label.setText(text)
        label.setFixedWidth(width)
        label.setFixedHeight(height)
        label.setAlignment(QtCore.Qt.AlignCenter)
        return label

    # Set Height and Width to a label as width=165 and height=30
    def createLabelSmall(self, text, width=165, height=30):
        label = QLabel()
        label.setText(text)
        label.setFixedWidth(width)
        label.setFixedHeight(height)
        label.setAlignment(QtCore.Qt.AlignCenter)
        return label

    # Set Height and Width to a label as width=165 and height=30
    def createButton(self, text, width=120, height=30):
        button = QPushButton()
        button.setText(text)
        button.setFixedWidth(width)
        button.setFixedHeight(height)
        return button

    def createHeadingLink(self, url, text):
        _link = "<a style='text-decoration:none;' href=\"{address}\"> <font face=Roboto color=#028ACC> {display}</font> </a>"
        return _link.format(address=url, display=text)

    def createLink(self, url, text):
        _link = "<a href=\"{address}\"> <font face=Roboto font size='4' color=#028ACC> {display}</font></a>"
        return _link.format(address=url, display=text)

    # Function to set UI for HOME Page
    def setupUIHomePage(self):
        # Home Page tab created
        tabHome = QtWidgets.QWidget()
        tabHome.setWindowTitle("HOME")
        # Home Page tab added
        self.centralwidget.addTab(tabHome, self.getSpacedNames("Home"))

        # Home Page code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(5, 1)

        # Add Scrollbar to HOME Page
        self.scrollAreaFPEAM = QScrollArea(tabHome)
        self.scrollAreaFPEAM.setWidgetResizable(True)
        self.scrollAreaFPEAM.resize(WIDTH, HEIGHT)
        self.scrollAreaFPEAM.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaFPEAM.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.innerWidgetFPEAM = QtWidgets.QWidget()
        self.innerWidgetFPEAM.resize(WIDTH, HEIGHT)
        self.scrollAreaFPEAM.setWidget(self.innerWidgetFPEAM)
        self.innerWidgetFPEAM.setLayout(self.windowLayout)

        # Add Vertical Space at the top
        emptyLabelTop = QLabel()
        emptyLabelTop.setFixedHeight(30)
        self.windowLayout.addWidget(emptyLabelTop, 0, 0, 1, 5)

        # add README link to top left of tab
        self.homeHelpLink = QLabel()
        self.homeHelpLink.setText(self.createLink("https://github.com/NREL/fpeam/tree/master#home",
                                                  "Readme"))
        self.homeHelpLink.setOpenExternalLinks(True)
        self.homeHelpLink.setFixedHeight(30)
        self.windowLayout.addWidget(self.homeHelpLink, 1, 0, 1, 1)

        # Create UI element Scenario Name HOME Page
        self.labelScenaName = self.createLabelSmall(text="Scenario Name")
        self.labelScenaName.setToolTip("Enter the Scenario Name")
        self.labelScenaName.setObjectName("allLabels")
        self.lineEditScenaName = QLineEdit(self)
        self.lineEditScenaName.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditScenaName.setFixedHeight(30)
        regex = QtCore.QRegExp("[0-9,a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditScenaName.setValidator(validator)
        self.windowLayout.addWidget(self.labelScenaName, 2, 0)
        self.windowLayout.addWidget(self.lineEditScenaName, 2, 1, 1, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        self.windowLayout.addWidget(emptyLabelE, 3, 0, 1, 5)

        # UI element - Project Path - HOME Page
        self.labelProjPath = self.createLabelSmall(text="Project Path")
        self.labelProjPath.setObjectName("allLabels")
        self.labelProjPath.setToolTip("Folder path where output files will be stored")
        self.browseBtn = self.createButton(text="Browse")
        self.browseBtn.clicked.connect(self.getfiles)
        self.lineEditProjectPath = QLineEdit(self)
        self.lineEditProjectPath.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditProjectPath.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelProjPath, 4, 0)
        self.windowLayout.addWidget(self.browseBtn, 4, 1)
        self.windowLayout.addWidget(self.lineEditProjectPath, 4, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        self.windowLayout.addWidget(emptyLabelE, 5, 0, 1, 5)

        # Created UI element Module Selection - HOME Page
        self.labelModules = self.createLabelSmall(text="Select Modules")
        self.labelModules.setObjectName("allLabels")
        self.labelModules.setToolTip("Select modules to run")
        self.checkBoxMoves = QCheckBox("MOVES")
        self.checkBoxMoves.setFixedWidth(120)
        self.checkBoxMoves.setFixedHeight(30)
        self.checkBoxMoves.setChecked(True)
        self.checkBoxMoves.stateChanged.connect(self.onStateChangedMoves)
        self.checkBoxNonroad = QCheckBox("NONROAD")
        self.checkBoxNonroad.setFixedWidth(120)
        self.checkBoxNonroad.setFixedHeight(30)
        self.checkBoxNonroad.setChecked(True)
        self.checkBoxNonroad.stateChanged.connect(self.onStateChangedNonroad)
        self.checkBoxEmissionFactors = QCheckBox("Emission Factors")
        self.checkBoxEmissionFactors.setFixedWidth(120)
        self.checkBoxEmissionFactors.setFixedHeight(30)
        self.checkBoxEmissionFactors.setChecked(True)
        self.checkBoxEmissionFactors.stateChanged.connect(self.onStateChangedEmissionFactors)
        self.checkBoxFugitiveDust = QCheckBox("Fugitive Dust")
        self.checkBoxFugitiveDust.setFixedWidth(120)
        self.checkBoxFugitiveDust.setFixedHeight(30)
        self.checkBoxFugitiveDust.setChecked(True)
        self.checkBoxFugitiveDust.stateChanged.connect(self.onStateChangedFugitiveDust)
        self.windowLayout.addWidget(self.labelModules, 6, 0, 1, 6)
        self.windowLayout.addWidget(self.checkBoxMoves, 6, 1)
        self.windowLayout.addWidget(self.checkBoxNonroad, 6, 2)
        self.windowLayout.addWidget(self.checkBoxEmissionFactors, 6, 3)
        self.windowLayout.addWidget(self.checkBoxFugitiveDust, 6, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(20)
        self.windowLayout.addWidget(emptyLabelE, 7, 0, 1, 5)

        # Created UI element Reset Button - HOME Page
        self.resetBtn = QPushButton("Reset", self)
        self.resetBtn.setFixedHeight(40)
        self.resetBtn.setFixedWidth(152)
        self.resetBtn.setObjectName("resetRunBtn")
        self.resetBtn.clicked.connect(self.resetFields)
        self.windowLayout.addWidget(self.resetBtn, 8, 3)

        # Created UI element Run Button - HOME Page
        self.runBtn = QPushButton("Run", self)
        self.runBtn.setFixedWidth(152)
        self.runBtn.setFixedHeight(40)
        self.runBtn.setObjectName("resetRunBtn")
        self.runBtn.setStyleSheet("border-color: #028ACC; color : #ffffff; background-color : #028ACC;")
        self.runBtn.clicked.connect(self.runTheSelectedModules)
        self.windowLayout.addWidget(self.runBtn, 8, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(20)
        self.windowLayout.addWidget(emptyLabelE, 9, 0, 1, 5)

        # Custom Data Filepaths Label - HOME Page
        self.customDataFilepathsLabel = QLabel()
        self.customDataFilepathsLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#custom-data-filepaths",
                                                                     "Custom Data Filepaths"))
        self.customDataFilepathsLabel.setOpenExternalLinks(True)
        self.customDataFilepathsLabel.setFixedHeight(30)
        self.customDataFilepathsLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.customDataFilepathsLabel, 10, 0, 1, 6)

        # Custom Datafiles below Line - HOME PAge
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('line.png')
        pixmap1 = pixmapLine1.scaledToHeight(15)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 11, 0, 1, 6)

        # Expand/Collapse code
        # Custom Data Filepaths FPEAM - HOME Page
        self.labelCustomDatafileFPEAMExpand = QPushButton()
        self.labelCustomDatafileFPEAMExpand.setFixedHeight(30)
        self.labelCustomDatafileFPEAMExpand.setFixedWidth(30)
        self.labelCustomDatafileFPEAMExpand.setObjectName("expandCollapseIcon")
        self.labelCustomDatafileFPEAMExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelCustomDatafileFPEAMExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelCustomDatafileFPEAMExpand, 10, 5)

        self.customDatafileFPEAMexpandWidget = QtWidgets.QWidget()
        self.customDatafileFPEAMexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.customDatafileFPEAMGridLayout = QtWidgets.QGridLayout()
        self.customDatafileFPEAMexpandWidget.setLayout(self.customDatafileFPEAMGridLayout)
        self.customDatafileFPEAMexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileFPEAMexpandWidget, 12, 0, 1, 5)

        def labelCustomDatafileFPEAMOnClickEvent():
            if self.customDatafileFPEAMexpandWidget.isVisible():
                self.labelCustomDatafileFPEAMExpand.setIcon(QtGui.QIcon('plus.png'))
                self.labelCustomDatafileFPEAMExpand.setIconSize(QtCore.QSize(28, 28))
                self.customDatafileFPEAMexpandWidget.setVisible(False)
            else:
                self.labelCustomDatafileFPEAMExpand.setIcon(QtGui.QIcon('minus.png'))
                self.labelCustomDatafileFPEAMExpand.setIconSize(QtCore.QSize(28, 28))
                self.customDatafileFPEAMexpandWidget.setVisible(True)

        self.labelCustomDatafileFPEAMExpand.clicked.connect(labelCustomDatafileFPEAMOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFPEAMGridLayout.addWidget(emptyLabelE, 0, 0, 1, 5)

        # UI element - Equipment - HOME
        self.labelEq = self.createLabelSmall(text="Equipment Use")
        self.labelEq.setObjectName("allLabels")
        self.labelEq.setStyleSheet(" border: 1px solid #000000; ")
        self.labelEq.setToolTip("Select equipment input dataset")
        self.browseBtnEq = self.createButton(text="Browse")
        self.browseBtnEq.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnEq.clicked.connect(self.getfilesEq)
        self.lineEditEq = QLineEdit(self)
        self.lineEditEq.setText("data/equipment/bts16_equipment.csv")
        self.lineEditEq.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditEq.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditEq.setFixedHeight(30)
        self.customDatafileFPEAMGridLayout.addWidget(self.labelEq, 1, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnEq, 1, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditEq, 1, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFPEAMGridLayout.addWidget(emptyLabelE, 2, 0, 1, 5)

        # UI element - Production - HOME
        self.labelProd = self.createLabelSmall(text="Feedstock Production")
        self.labelProd.setObjectName("allLabels")
        self.labelProd.setStyleSheet(" border: 1px solid #000000; ")
        self.labelProd.setToolTip("Select production input dataset")
        self.browseBtnProd = self.createButton(text="Browse")
        self.browseBtnProd.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnProd.clicked.connect(self.getfilesProd)
        self.lineEditProd = QLineEdit(self)
        self.lineEditProd.setText("data/production/production_2017_bc1060.csv")
        self.lineEditProd.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditProd.setFixedHeight(30)
        self.lineEditProd.setStyleSheet(" border: 1px solid #000000; ")
        self.customDatafileFPEAMGridLayout.addWidget(self.labelProd, 3, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnProd, 3, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditProd, 3, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFPEAMGridLayout.addWidget(emptyLabelE, 4, 0, 1, 5)

        # Feedstock Loss Factors - HOME
        self.labelFedLossFact = self.createLabelSmall(text="Feedstock Loss Factors")
        self.labelFedLossFact.setObjectName("allLabels")
        self.labelFedLossFact.setStyleSheet(" border: 1px solid #000000; ")
        self.labelFedLossFact.setToolTip("Select feedstock loss factors dataset")
        self.browseBtnFLoss = self.createButton(text="Browse")
        self.browseBtnFLoss.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnFLoss.clicked.connect(self.getfilesFLoss)
        self.lineEditFedLossFact = QLineEdit(self)
        self.lineEditFedLossFact.setText("data/inputs/feedstock_loss_factors.csv")
        self.lineEditFedLossFact.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditFedLossFact.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditFedLossFact.setFixedHeight(30)
        self.customDatafileFPEAMGridLayout.addWidget(self.labelFedLossFact, 5, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnFLoss, 5, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditFedLossFact, 5, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFPEAMGridLayout.addWidget(emptyLabelE, 6, 0, 1, 5)

        # Transportation graph - HOME
        self.labelTransGraph = self.createLabelSmall(text="Transportation Graph")
        self.labelTransGraph.setObjectName("allLabels")
        self.labelTransGraph.setStyleSheet(" border: 1px solid #000000; ")
        self.labelTransGraph.setToolTip("Select transportation graph dataset")
        self.browseBtnTransGr = self.createButton(text="Browse")
        self.browseBtnTransGr.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnTransGr.clicked.connect(self.getfilesTransGr)
        self.lineEditTransGraph = QLineEdit(self)
        self.lineEditTransGraph.setText("data/inputs/transportation_graph.csv")
        self.lineEditTransGraph.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditTransGraph.setFixedHeight(30)
        self.lineEditTransGraph.setStyleSheet(" border: 1px solid #000000; ")
        self.customDatafileFPEAMGridLayout.addWidget(self.labelTransGraph, 7, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnTransGr, 7, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditTransGraph, 7, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFPEAMGridLayout.addWidget(emptyLabelE, 8, 0, 1, 5)

        # Node locations - HOME
        self.labelNodeLocs = self.createLabelSmall(text="Node Locations")
        self.labelNodeLocs.setObjectName("allLabels")
        self.labelNodeLocs.setStyleSheet(" border: 1px solid #000000; ")
        self.labelNodeLocs.setToolTip("Select node locations dataset")
        self.browseBtnNodeLocs = self.createButton(text="Browse")
        self.browseBtnNodeLocs.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnNodeLocs.clicked.connect(self.getfilesNodeLocs)
        self.lineEditNodeLocs = QLineEdit(self)
        self.lineEditNodeLocs.setText("data/inputs/node_locations.csv")
        self.lineEditNodeLocs.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditNodeLocs.setFixedHeight(30)
        self.lineEditNodeLocs.setStyleSheet(" border: 1px solid #000000; ")
        self.customDatafileFPEAMGridLayout.addWidget(self.labelNodeLocs, 9, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnNodeLocs, 9, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditNodeLocs, 9, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFPEAMGridLayout.addWidget(emptyLabelE, 10, 0, 1, 5)

        # Truck Capacity - HOME
        self.labelTruckCapacity = self.createLabelSmall(text="Truck Capacity")
        self.labelTruckCapacity.setObjectName("allLabels")
        self.labelTruckCapacity.setStyleSheet(" border: 1px solid #000000; ")
        self.labelTruckCapacity.setToolTip("Select truck capacity dataset")
        self.browseBtnTruckCapa = self.createButton(text="Browse")
        self.browseBtnTruckCapa.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnTruckCapa.clicked.connect(self.getfilesTruckCapa)
        self.lineEditTruckCapa = QLineEdit(self)
        self.lineEditTruckCapa.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditTruckCapa.setText("data/inputs/truck_capacity.csv")
        self.lineEditTruckCapa.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditTruckCapa.setFixedHeight(30)
        self.customDatafileFPEAMGridLayout.addWidget(self.labelTruckCapacity, 11, 0)
        self.customDatafileFPEAMGridLayout.addWidget(self.browseBtnTruckCapa, 11, 1)
        self.customDatafileFPEAMGridLayout.addWidget(self.lineEditTruckCapa, 11, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFPEAMGridLayout.addWidget(emptyLabelE, 12, 0, 1, 5)

        # Advanced Options Label - HOME
        self.advOptionsLabel = QLabel()
        self.advOptionsLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#advanced-options",
                                                            "Advanced Options"))
        self.advOptionsLabel.setOpenExternalLinks(True)
        self.advOptionsLabel.setFixedHeight(30)
        self.advOptionsLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.advOptionsLabel, 18, 0, 1, 6)

        # Advanced Options below Line
        self.labelAdvOptionsLine = QLabel()
        pixmapLine2 = QPixmap('line.png')
        pixmap2 = pixmapLine2.scaledToHeight(15)
        self.labelAdvOptionsLine.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelAdvOptionsLine, 19, 0, 1, 6)

        # Expand/Collapse code
        # Advanced Options FPEAM - HOME
        self.labelAdvOptionsFPEAMExpand = QPushButton()
        self.labelAdvOptionsFPEAMExpand.setStyleSheet("QPushButton { text-align : right}")
        self.labelAdvOptionsFPEAMExpand.setFixedHeight(30)
        self.labelAdvOptionsFPEAMExpand.setFixedWidth(30)
        self.labelAdvOptionsFPEAMExpand.setObjectName("expandCollapseIcon")
        self.labelAdvOptionsFPEAMExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelAdvOptionsFPEAMExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelAdvOptionsFPEAMExpand, 18, 5)

        self.advOptionsFPEAMexpandWidget = QtWidgets.QWidget()
        self.advOptionsFPEAMexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;outline-style: solid; outline-color:black;border-radius: 5px;")
        self.advOptionsFPEAMGridLayout = QtWidgets.QGridLayout()
        self.advOptionsFPEAMexpandWidget.setLayout(self.advOptionsFPEAMGridLayout)
        self.advOptionsFPEAMexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.advOptionsFPEAMexpandWidget, 20, 0, 1, 5)

        def labelAdvOptionsFPEAMOnClickEvent():
            if self.advOptionsFPEAMexpandWidget.isVisible():
                self.labelAdvOptionsFPEAMExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelAdvOptionsFPEAMExpand.setIcon(QtGui.QIcon('plus.png'))
                self.advOptionsFPEAMexpandWidget.setVisible(False)
            else:
                self.labelAdvOptionsFPEAMExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelAdvOptionsFPEAMExpand.setIcon(QtGui.QIcon('minus.png'))
                self.advOptionsFPEAMexpandWidget.setVisible(True)

        self.labelAdvOptionsFPEAMExpand.clicked.connect(labelAdvOptionsFPEAMOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(15)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsFPEAMGridLayout.addWidget(emptyLabelE, 0, 0, 1, 5)

        # Ui Element - Logging Verbosity Level - HOME
        self.labelLoggVerboLevel = self.createLabelSmall(text="Logging Level")
        self.labelLoggVerboLevel.setObjectName("allLabels")
        self.labelLoggVerboLevel.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxVerbosityLevel = QComboBox(self)
        self.comboBoxVerbosityLevel.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxVerbosityLevel.setFixedWidth(165)
        self.comboBoxVerbosityLevel.setFixedHeight(30)
        self.comboBoxVerbosityLevel.addItem("INFO")
        self.comboBoxVerbosityLevel.addItem("ERROR")
        self.comboBoxVerbosityLevel.addItem("WARNING")
        self.comboBoxVerbosityLevel.addItem("UNSET")
        self.comboBoxVerbosityLevel.addItem("CRITICAL")
        self.comboBoxVerbosityLevel.addItem("DEBUG")
        self.index = self.comboBoxVerbosityLevel.findText("DEBUG")
        self.comboBoxVerbosityLevel.setCurrentIndex(self.index)
        self.comboBoxVerbosityLevel.setEditable(True)
        self.leditVerboLevel = self.comboBoxVerbosityLevel.lineEdit()
        self.leditVerboLevel.setAlignment(QtCore.Qt.AlignCenter)
        self.leditVerboLevel = self.comboBoxVerbosityLevel.lineEdit()
        self.leditVerboLevel.setReadOnly(True)
        self.advOptionsFPEAMGridLayout.addWidget(self.labelLoggVerboLevel, 1, 0)
        self.advOptionsFPEAMGridLayout.addWidget(self.comboBoxVerbosityLevel, 2, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.emptyPlainText3.setStyleSheet("border-color: white;")
        self.emptyPlainText3.setFixedWidth(55)
        self.emptyPlainText3.setFixedHeight(30)
        self.advOptionsFPEAMGridLayout.addWidget(self.emptyPlainText3, 1, 1)

        # UI element  -  Router Engine - HOME
        self.labelRE = self.createLabelSmall(text="Use Router Engine")
        self.labelRE.setObjectName("allLabels")
        self.labelRE.setStyleSheet(" border: 1px solid #000000; ")
        self.labelRE.setToolTip("Determine route lengths by road distance")
        self.comboBoxRE = QComboBox(self)
        self.comboBoxRE.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxRE.setFixedWidth(165)
        self.comboBoxRE.setFixedHeight(30)
        self.comboBoxRE.addItem("Yes")
        self.comboBoxRE.addItem("No")
        self.comboBoxRE.setCurrentText("Yes")
        self.index = self.comboBoxRE.findText("Yes")
        self.comboBoxRE.setCurrentIndex(self.index)
        self.comboBoxRE.setEditable(True)
        self.leditRE = self.comboBoxRE.lineEdit()
        self.leditRE.setAlignment(QtCore.Qt.AlignCenter)
        self.leditRE = self.comboBoxRE.lineEdit()
        self.leditRE.setReadOnly(True)
        self.advOptionsFPEAMGridLayout.addWidget(self.labelRE, 1, 2)
        self.advOptionsFPEAMGridLayout.addWidget(self.comboBoxRE, 2, 2)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.advOptionsFPEAMGridLayout.addWidget(self.emptyPlainText2, 1, 3)

        # UI element -  Backfill Flag - HOME
        self.labelBF = self.createLabelSmall(text="Backfill Missing Data")
        self.labelBF.setObjectName("allLabels")
        self.labelBF.setStyleSheet(" border: 1px solid #000000; ")
        self.labelBF.setToolTip("Replace mandatory missing data with zeros")
        self.comboBoxBF = QComboBox(self)
        self.comboBoxBF.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxBF.setFixedWidth(165)
        self.comboBoxBF.setFixedHeight(30)
        self.comboBoxBF.addItem("Yes")
        self.comboBoxBF.addItem("No")
        self.comboBoxBF.setCurrentText("Yes")
        self.index = self.comboBoxBF.findText("Yes")
        self.comboBoxBF.setCurrentIndex(self.index)
        self.comboBoxBF.setEditable(True)
        self.leditBE = self.comboBoxBF.lineEdit()
        self.leditBE.setAlignment(QtCore.Qt.AlignCenter)
        self.leditBF = self.comboBoxBF.lineEdit()
        self.leditBF.setReadOnly(True)
        self.advOptionsFPEAMGridLayout.addWidget(self.labelBF, 1, 4)
        self.advOptionsFPEAMGridLayout.addWidget(self.comboBoxBF, 2, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsFPEAMGridLayout.addWidget(emptyLabelE, 3, 0, 1, 5)

        # Created UI element Forestry Feedstock Names
        self.labelForestryNamesNon = self.createLabelBig(text="Forestry Feedstock" + "\n" + " Names")
        self.labelForestryNamesNon.setObjectName("allLabels")
        self.labelForestryNamesNon.setStyleSheet(" border: 1px solid #000000; ")
        self.labelForestryNamesNon.setToolTip("List of forestry feedstocks in production dataset")
        self.lineEditForestryNamesNon = QLineEdit(self)
        self.lineEditForestryNamesNon.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditForestryNamesNon.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditForestryNamesNon.setFixedHeight(40)
        self.regex = QtCore.QRegExp("[a-z-A-Z_,]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditForestryNamesNon.setValidator(validator)
        self.lineEditForestryNamesNon.setText("'forest whole tree', 'forest residues'")
        self.advOptionsFPEAMGridLayout.addWidget(self.labelForestryNamesNon, 4, 0)
        self.advOptionsFPEAMGridLayout.addWidget(self.lineEditForestryNamesNon, 4, 1, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsFPEAMGridLayout.addWidget(emptyLabelE, 5, 0, 1, 5)

        # Created UI element VMT per Truck
        self.labelVMTperTruck = self.createLabelBig(text="VMT Per Truck")
        self.labelVMTperTruck.setStyleSheet(" border: 1px solid #000000; ")
        self.labelVMTperTruck.setObjectName("allLabels")
        self.labelVMTperTruck.setToolTip("Default vehicle miles traveled (VMT) per truck. Only used if the router engine is turned off.")
        self.lineEditVMTperTruck = QLineEdit(self)
        self.lineEditVMTperTruck.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditVMTperTruck.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditVMTperTruck.setFixedWidth(75)
        self.lineEditVMTperTruck.setFixedHeight(40)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditVMTperTruck.setValidator(self.onlyFlaot)
        self.lineEditVMTperTruck.setText("20")
        self.advOptionsFPEAMGridLayout.addWidget(self.labelVMTperTruck, 6, 0)
        self.advOptionsFPEAMGridLayout.addWidget(self.lineEditVMTperTruck, 6, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsFPEAMGridLayout.addWidget(emptyLabelE, 7, 0, 1, 5)

        # Add space to adjust position of the elements
        # Add Empty PlainText
        self.emptyPlainText10 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText10, 21, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 22, 0)

        # Add Empty PlainText
        self.emptyPlainText14 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText14, 23, 0)

        # Add Empty PlainText
        self.emptyPlainText7 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText7, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText11 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText11, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText13 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText13, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText8 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText8, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText9 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText9, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText12 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText12, 30, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 31, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 32, 0)

    # Checkbox - MOVES Module - Checked
    def onStateChangedMoves(self, state1):
        if state1 == self.checkBoxMoves.isChecked():
            self.centralwidget.setTabEnabled(1, False)

        else:
            self.centralwidget.setTabEnabled(1, True)

    # Checkbox - NONROAD Module- Checked
    def onStateChangedNonroad(self, state2):

        if state2 == self.checkBoxNonroad.isChecked():
            self.centralwidget.setTabEnabled(2, False)
        else:
            self.centralwidget.setTabEnabled(2, True)

    # Checkbox - Emission Factors Module- Checked
    def onStateChangedEmissionFactors(self, state3):

        if state3 == self.checkBoxEmissionFactors.isChecked():
            self.centralwidget.setTabEnabled(3, False)
        else:
            self.centralwidget.setTabEnabled(3, True)

    # Checkbox - Fugitive Dust Module- Checked
    def onStateChangedFugitiveDust(self, state4):
        if state4 == self.checkBoxFugitiveDust.isChecked():
            self.centralwidget.setTabEnabled(4, False)
        else:
            self.centralwidget.setTabEnabled(4, True)

    # Get Project Path
    def getfiles(self):
        fileName = QFileDialog.getExistingDirectory(self, "Browse")
        if fileName != "":
            selectedFileName = str(fileName).split(',')
            self.lineEditProjectPath.setText(selectedFileName[0])

    # Equipment
    def getfilesEq(self):
        fileNameEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameEq[0] != "":
            selectedFileNameEq = fileNameEq[0].split("FPEAM/")
            self.lineEditEq.setText(selectedFileNameEq[1])

    # Production
    def getfilesProd(self):
        fileNameProd = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameProd[0] != "":
            selectedFileNameProd = fileNameProd[0].split("FPEAM/")
            self.lineEditProd.setText(selectedFileNameProd[1])

    # Feedstock Loss Factors
    def getfilesFLoss(self):
        fileNameFLoss = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameFLoss[0] != "":
            selectedFileNameFLoss = fileNameFLoss[0].split("FPEAM/")
            self.lineEditFedLossFact.setText(selectedFileNameFLoss[1])

    # Transportation graph
    def getfilesTransGr(self):
        fileNameTransGr = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTransGr[0] != "":
            selectedFileNameTransGr = fileNameTransGr[0].split("FPEAM/")
            self.lineEditTransGraph.setText(selectedFileNameTransGr[1])

    # Node locations
    def getfilesNodeLocs(self):
        fileNameNodeLocs = QFileDialog.getOpenFileName(self, 'Browse', "",
                                                      "CSV files (*.csv)")
        if fileNameNodeLocs[0] != "":
            selectedFileNameNodeLocs = fileNameNodeLocs[0].split("FPEAM/")
            self.lineEditNodeLocs.setText(selectedFileNameNodeLocs[1])

        ###########################################################################################################################################################################

    def setupUIMoves(self):

        # MOVES code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSpacing(15)
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        # MOVES tab created
        self.tabMoves = QtWidgets.QWidget()
        # Moves tab added
        self.centralwidget.addTab(self.tabMoves, self.getSpacedNames("MOVES"))

        # Add Scrollbar to MOVES tab
        self.scrollAreaMOVES = QScrollArea(self.tabMoves)
        self.scrollAreaMOVES.setWidgetResizable(True)
        self.scrollAreaMOVES.resize(WIDTH, HEIGHT)
        self.scrollAreaMOVES.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaMOVES.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.innerWidgetMOVES = QtWidgets.QWidget()
        self.innerWidgetMOVES.resize(WIDTH, HEIGHT)
        self.scrollAreaMOVES.setWidget(self.innerWidgetMOVES)
        self.innerWidgetMOVES.setLayout(self.windowLayout)

        # Add Vertical space at the top @todo
        emptyLabelTop = QLabel()
        emptyLabelTop.setFixedHeight(30)
        self.windowLayout.addWidget(emptyLabelTop, 0, 0, 1, 5)

        # add link to readme in upper-left-hand corner of tab
        self.moveshelplink = QLabel()
        self.moveshelplink.setText(self.createLink("https://github.com/NREL/fpeam/tree/master#moves",
                                                   "Readme"))
        self.moveshelplink.setOpenExternalLinks(True)
        self.moveshelplink.setFixedHeight(30)
        self.windowLayout.addWidget(self.moveshelplink, 1, 0, 1, 4)

        # Created UI element Aggregation Level - MOVES
        self.labelAggLevel = self.createLabelBig(text="Aggregation Level")
        self.labelAggLevel.setObjectName("allLabels")
        self.comboBoxAggLevel = QComboBox(self)
        self.comboBoxAggLevel.setObjectName("AggLevelCombo")
        self.comboBoxAggLevel.setFixedWidth(116)
        self.comboBoxAggLevel.setFixedHeight(40)
        self.comboBoxAggLevel.addItem("By State")
        self.comboBoxAggLevel.addItem("By County")
        self.comboBoxAggLevel.addItem("By State-Feedstock")
        self.comboBoxAggLevel.setCurrentText("By State")
        self.index = self.comboBoxAggLevel.findText("By State")
        self.comboBoxAggLevel.setCurrentIndex(self.index)
        self.comboBoxAggLevel.setEditable(True)
        self.leditAggLevel = self.comboBoxAggLevel.lineEdit()
        self.leditAggLevel.setAlignment(QtCore.Qt.AlignCenter)
        self.leditAggLevel = self.comboBoxAggLevel.lineEdit()
        self.leditAggLevel.setReadOnly(True)
        self.windowLayout.addWidget(self.labelAggLevel, 2, 0)
        self.windowLayout.addWidget(self.comboBoxAggLevel, 2, 1)

        # Created UI element Cached Result usage
        self.labelCachedResUse = self.createLabelBig(text="Use Cached Results")
        self.labelCachedResUse.setObjectName("allLabels")
        self.labelCachedResUse.setToolTip("Use existing results in MOVES output database")
        self.comboBoxCachedResUse = QComboBox(self)
        self.comboBoxCachedResUse.setFixedWidth(116)
        self.comboBoxCachedResUse.setFixedHeight(40)
        self.comboBoxCachedResUse.addItem("True")
        self.comboBoxCachedResUse.addItem("False")
        self.index = self.comboBoxCachedResUse.findText("True")
        self.comboBoxCachedResUse.setCurrentIndex(self.index)
        self.comboBoxCachedResUse.setEditable(True)
        self.leditCachedRes = self.comboBoxCachedResUse.lineEdit()
        self.leditCachedRes.setAlignment(QtCore.Qt.AlignCenter)
        self.leditCachedRes = self.comboBoxCachedResUse.lineEdit()
        self.leditCachedRes.setReadOnly(True)
        # Add Empty PlainText
        self.emptyPlainTextCachedRes = QLabel()
        self.windowLayout.addWidget(self.labelCachedResUse, 3, 0)
        self.windowLayout.addWidget(self.comboBoxCachedResUse, 3, 1)
        self.windowLayout.addWidget(self.emptyPlainTextCachedRes, 3, 2)

        # Created UI element Moves Path
        self.MovesPathLable = self.createLabelBig(text="Executable Path")
        self.MovesPathLable.setObjectName("allLabels")
        self.MovesPathLable.setToolTip("Path where Moves is installed. If it's not installed, then download from the "
                                       "link - "
                                       "<a href ='https://www.epa.gov/moves/moves-versions-limited-current-use#downloading-2014a'>MOVES</a> ")
        self.browseBtnMovesPath = self.createButton(text="Browse", width=116, height=40)
        self.browseBtnMovesPath.clicked.connect(self.getfilesMovesPath)
        self.lineEditMovesPath = QLineEdit(self)
        self.lineEditMovesPath.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditMovesPath.setFixedHeight(40)
        self.lineEditMovesPath.setText("C:\MOVES2014b")
        self.windowLayout.addWidget(self.MovesPathLable, 4, 0)
        self.windowLayout.addWidget(self.browseBtnMovesPath, 4, 1)
        self.windowLayout.addWidget(self.lineEditMovesPath, 4, 2, 1, 3)

        # Created UI element Moves Datafiles
        self.labelDatafiles = self.createLabelBig(text="MOVES Datafiles")
        self.labelDatafiles.setObjectName("allLabels")
        self.labelDatafiles.setToolTip("Select all input files created for MOVES runs")
        self.browseBtnDatafiles = self.createButton(text="Browse", width=116, height=40)
        self.browseBtnDatafiles.clicked.connect(self.getfilesDatafiles)
        self.lineEditDatafiles = QLineEdit(self)
        self.lineEditDatafiles.setText("C:\MOVESdata")
        self.lineEditDatafiles.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditDatafiles.setFixedHeight(40)
        self.windowLayout.addWidget(self.labelDatafiles, 5, 0)
        self.windowLayout.addWidget(self.browseBtnDatafiles, 5, 1)
        self.windowLayout.addWidget(self.lineEditDatafiles, 5, 2, 1, 3)

        # Created UI element Feedstock Measure Type
        self.labelFeedMeasureType = self.createLabelBig(text="Feedstock Measure" + "\n" + " Type")
        self.labelFeedMeasureType.setObjectName("allLabels")
        self.labelFeedMeasureType.setToolTip("Enter feedstock measure type identifier")
        self.lineEditFeedMeasureType = QLineEdit(self)
        self.lineEditFeedMeasureType.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureType.setFixedWidth(116)
        self.lineEditFeedMeasureType.setFixedHeight(40)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureType.setValidator(validator)
        self.lineEditFeedMeasureType.setText("production")
        self.windowLayout.addWidget(self.labelFeedMeasureType, 6, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureType, 6, 1)

        # Database Connection Parameters Label
        self.dbConnectionParaLabel = QLabel()
        self.dbConnectionParaLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#database-connection-parameters",
                                                                  "Database Connection Parameters"))
        self.dbConnectionParaLabel.setOpenExternalLinks(True)
        self.dbConnectionParaLabel.setFixedHeight(30)
        self.dbConnectionParaLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.dbConnectionParaLabel, 7, 0, 1, 4)

        # Created UI element - Database Connection Parameters below Line
        self.dbConnectionParaLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.dbConnectionParaLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dbConnectionParaLine, 8, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Database Connection Parameters MOVES
        self.labeldbConnectionsMOVESExpand = QPushButton()
        self.labeldbConnectionsMOVESExpand.setFixedHeight(30)
        self.labeldbConnectionsMOVESExpand.setFixedWidth(30)
        self.labeldbConnectionsMOVESExpand.setObjectName("expandCollapseIcon")
        self.labeldbConnectionsMOVESExpand.setIconSize(QtCore.QSize(28, 28))
        self.labeldbConnectionsMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labeldbConnectionsMOVESExpand, 7, 4)


        self.dbConnectionsMOVESexpandWidget = QtWidgets.QWidget()
        self.dbConnectionsMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.dbConnectionsMOVESGridLayout = QtWidgets.QGridLayout()
        self.dbConnectionsMOVESexpandWidget.setLayout(self.dbConnectionsMOVESGridLayout)
        self.dbConnectionsMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.dbConnectionsMOVESexpandWidget, 9, 0, 1, 4)

        def labelDbConnectionsMOVESOnClickEvent():
            if self.dbConnectionsMOVESexpandWidget.isVisible():
                self.labeldbConnectionsMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labeldbConnectionsMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
                self.dbConnectionsMOVESexpandWidget.setVisible(False)
            else:
                self.labeldbConnectionsMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labeldbConnectionsMOVESExpand.setIcon(QtGui.QIcon('minus.png'))
                self.dbConnectionsMOVESexpandWidget.setVisible(True)

        self.labeldbConnectionsMOVESExpand.clicked.connect(labelDbConnectionsMOVESOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsMOVESGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Database Host
        self.labelDbHost = self.createLabelSmall(text="Database Host")
        self.labelDbHost.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbHost.setObjectName("allLabels")
        self.labelDbHost.setToolTip("Database host")
        self.lineEditDbHost = QLineEdit(self)
        self.lineEditDbHost.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbHost.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbHost.setFixedHeight(30)
        self.lineEditDbHost.setFixedWidth(125)
        regex = QtCore.QRegExp("[1-9,a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditDbHost.setValidator(validator)
        self.lineEditDbHost.setText("localhost")
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbHost, 1, 0)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbHost, 1, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.dbConnectionsMOVESGridLayout.addWidget(self.emptyPlainText2, 1, 2)

        # Created UI element Database Username
        self.labelDbUsername = self.createLabelSmall(text="Username")
        self.labelDbUsername.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbUsername.setObjectName("allLabels")
        self.labelDbUsername.setToolTip("Database username")
        self.lineEditDbUsername = QLineEdit(self)
        self.lineEditDbUsername.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbUsername.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbUsername.setFixedHeight(30)
        self.lineEditDbUsername.setFixedWidth(125)
        self.lineEditDbUsername.setText("root")
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbUsername, 1, 3)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbUsername, 1, 4)

        ## Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsMOVESGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element Database Name
        self.labelDbName = self.createLabelSmall(text="MOVES Database")
        self.labelDbName.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbName.setObjectName("allLabels")
        self.labelDbName.setToolTip("Name of default MOVES database")
        self.lineEditDbName = QLineEdit(self)
        self.lineEditDbName.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbName.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbName.setFixedHeight(30)
        self.lineEditDbName.setFixedWidth(125)
        self.lineEditDbName.setText("movesdb20180517")
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbName, 3, 0)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbName, 3, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.dbConnectionsMOVESGridLayout.addWidget(self.emptyPlainText2, 3, 2)

        # Created UI element Database Password
        self.labelDbPwd = self.createLabelSmall(text="Password")
        self.labelDbPwd.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbPwd.setObjectName("allLabels")
        self.labelDbPwd.setToolTip("Database password")
        self.lineEditDbPwd = QLineEdit(self)
        self.lineEditDbPwd.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbPwd.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbPwd.setFixedHeight(30)
        self.lineEditDbPwd.setFixedWidth(125)
        self.lineEditDbPwd.setEchoMode(QLineEdit.Password)
        self.lineEditDbPwd.show()
        self.lineEditDbPwd.setText("root")
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelDbPwd, 3, 3)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditDbPwd, 3, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsMOVESGridLayout.addWidget(emptyLabelE, 4, 0, 1, 5)

        # Created UI element Output database
        self.labelOutDb = self.createLabelSmall(text="Output Database")
        self.labelOutDb.setStyleSheet(" border: 1px solid #000000; ")
        self.labelOutDb.setObjectName("allLabels")
        self.labelOutDb.setToolTip("Name of database where MOVES results are stored")
        self.lineEditOutDb = QLineEdit(self)
        self.lineEditOutDb.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditOutDb.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditOutDb.setFixedHeight(30)
        self.lineEditOutDb.setFixedWidth(125)
        self.lineEditOutDb.setText('moves_output_db')
        self.dbConnectionsMOVESGridLayout.addWidget(self.labelOutDb, 5, 0)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditOutDb, 5, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsMOVESGridLayout.addWidget(emptyLabelE, 6, 0, 1, 5)

        # create UI element for mysql executable
        self.MysqlBinLab = self.createLabelSmall(text="MySQL Exe")
        self.MysqlBinLab.setStyleSheet(" border: 1px solid #000000; ")
        self.MysqlBinLab.setObjectName("allLabels")
        self.MysqlBinLab.setToolTip("Select path where MySQL executable file is located")
        self.browseBtnMysqlBin = self.createButton(text="Browse", width=125, height=30)
        self.browseBtnMysqlBin.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnMysqlBin.clicked.connect(self.getfilesMysqlBin)
        self.lineEditMysqlBin = QLineEdit(self)
        self.lineEditMysqlBin.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMysqlBin.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditMysqlBin.setFixedHeight(30)
        self.lineEditMysqlBin.setText("C:\Program Files\MySQL\MySQL Server 5.7\\bin\mysql.exe")
        self.dbConnectionsMOVESGridLayout.addWidget(self.MysqlBinLab, 7, 0)
        self.dbConnectionsMOVESGridLayout.addWidget(self.browseBtnMysqlBin, 7, 1)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditMysqlBin, 7, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsMOVESGridLayout.addWidget(emptyLabelE, 8, 0, 1, 5)

        # create UI element for mysql dump executable
        self.MysqlDumpBinLab = self.createLabelSmall(text="MySQL Dump Exe")
        self.MysqlDumpBinLab.setStyleSheet(" border: 1px solid #000000; ")
        self.MysqlDumpBinLab.setObjectName("allLabels")
        self.MysqlDumpBinLab.setToolTip("Select path where MySQL dump executable file is located")
        self.browseBtnMysqlDumpBin = self.createButton(text="Browse", width=125, height=30)
        self.browseBtnMysqlDumpBin.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnMysqlDumpBin.clicked.connect(self.getfilesMysqlDumpBin)
        self.lineEditMysqlDumpBin = QLineEdit(self)
        self.lineEditMysqlDumpBin.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMysqlDumpBin.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditMysqlDumpBin.setFixedHeight(30)
        self.lineEditMysqlDumpBin.setText("C:\Program Files\MySQL\MySQL Server 5.7\\bin\mysqldump.exe")
        self.dbConnectionsMOVESGridLayout.addWidget(self.MysqlDumpBinLab, 9, 0)
        self.dbConnectionsMOVESGridLayout.addWidget(self.browseBtnMysqlDumpBin, 9, 1)
        self.dbConnectionsMOVESGridLayout.addWidget(self.lineEditMysqlDumpBin, 9, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsMOVESGridLayout.addWidget(emptyLabelE, 10, 0, 1, 5)

        # Execution Timeframe Label
        self.executionTimeLabel = QLabel()
        self.executionTimeLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#execution-timeframe",
                                                               "Execution Timeframe"))
        self.executionTimeLabel.setOpenExternalLinks(True)
        self.executionTimeLabel.setFixedHeight(30)
        self.executionTimeLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.executionTimeLabel, 11, 0, 1, 4)

        # Created UI element - Execution Timeframe below Line
        self.executionTimeLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.executionTimeLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.executionTimeLine, 12, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Execution Timeframe MOVES
        self.labelTimeframeMOVESExpand = QPushButton()
        self.labelTimeframeMOVESExpand.setFixedHeight(30)
        self.labelTimeframeMOVESExpand.setFixedWidth(30)
        self.labelTimeframeMOVESExpand.setObjectName("expandCollapseIcon")
        self.labelTimeframeMOVESExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelTimeframeMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelTimeframeMOVESExpand, 11, 4)

        self.timeframeMOVESexpandWidget = QtWidgets.QWidget()
        self.timeframeMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.timeframeMOVESGridLayout = QtWidgets.QGridLayout()
        self.timeframeMOVESexpandWidget.setLayout(self.timeframeMOVESGridLayout)
        self.timeframeMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.timeframeMOVESexpandWidget, 13, 0, 1, 4)

        def labelTimeframeMOVESOnClickEvent():
            if self.timeframeMOVESexpandWidget.isVisible():
                self.labelTimeframeMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelTimeframeMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
                self.timeframeMOVESexpandWidget.setVisible(False)
            else:
                self.labelTimeframeMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelTimeframeMOVESExpand.setIcon(QtGui.QIcon('minus.png'))
                self.timeframeMOVESexpandWidget.setVisible(True)

        self.labelTimeframeMOVESExpand.clicked.connect(labelTimeframeMOVESOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.timeframeMOVESGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Analysis Year
        self.labelAnalysisYear = self.createLabelSmall(text="Analysis Year")
        self.labelAnalysisYear.setStyleSheet(" border: 1px solid #000000; ")
        self.labelAnalysisYear.setObjectName("allLabels")
        self.labelAnalysisYear.setToolTip("Start year of equipment")
        self.comboBoxYear = QComboBox(self)
        self.comboBoxYear.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxYear.setFixedWidth(125)
        self.comboBoxYear.setFixedHeight(30)
        for i in range(2018, 1990, -1):
            self.number = i
            self.comboBoxYear.addItem(str(i))
        self.index = self.comboBoxYear.findText("2017")
        self.comboBoxYear.setCurrentIndex(self.index)
        self.comboBoxYear.setEditable(True)
        self.leditYear = self.comboBoxYear.lineEdit()
        self.leditYear.setAlignment(QtCore.Qt.AlignCenter)
        self.leditYear = self.comboBoxYear.lineEdit()
        self.leditYear.setReadOnly(True)
        self.labelYearErrorMsg = QLabel()
        self.labelYearErrorMsg.setStyleSheet(" border: 1px solid white; ")
        self.labelYearErrorMsg.setObjectName("yearErrorMsg")
        self.labelYearErrorMsg.setFixedHeight(30)
        self.labelYearErrorMsg.setText("")
        self.timeframeMOVESGridLayout.addWidget(self.labelAnalysisYear, 1, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxYear, 1, 1)
        self.timeframeMOVESGridLayout.addWidget(self.labelYearErrorMsg, 1, 2, 1, 3)
        self.comboBoxYear.currentIndexChanged.connect(self.handleItemPressed)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.timeframeMOVESGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element Timestamp - Month
        self.labelMonth = self.createLabelSmall(text="Month")
        self.labelMonth.setStyleSheet(" border: 1px solid #000000; ")
        self.labelMonth.setObjectName("allLabels")
        self.comboBoxMonth = QComboBox(self)
        self.comboBoxMonth.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxMonth.setFixedWidth(125)
        self.comboBoxMonth.setFixedHeight(30)
        for i in range(1, 13):
            self.number = i
            self.comboBoxMonth.addItem(str(i))
        self.index = self.comboBoxMonth.findText("10")
        self.comboBoxMonth.setCurrentIndex(self.index)
        self.comboBoxMonth.setEditable(True)
        self.leditMonth = self.comboBoxMonth.lineEdit()
        self.leditMonth.setAlignment(QtCore.Qt.AlignCenter)
        self.leditMonth = self.comboBoxMonth.lineEdit()
        self.leditMonth.setReadOnly(True)
        self.timeframeMOVESGridLayout.addWidget(self.labelMonth, 3, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxMonth, 3, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.timeframeMOVESGridLayout.addWidget(self.emptyPlainText2, 3, 2)

        # Created UI element Timestamp - Beginning Hour
        self.labelBegHr = self.createLabelSmall(text="Beginning Hour")
        self.labelBegHr.setStyleSheet(" border: 1px solid #000000; ")
        self.labelBegHr.setObjectName("allLabels")
        self.comboBoxBegHr = QComboBox(self)
        self.comboBoxBegHr.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxBegHr.setFixedWidth(125)
        self.comboBoxBegHr.setFixedHeight(30)
        for i in range(1, 25):
            self.number = i
            self.comboBoxBegHr.addItem(str(i))
        self.index = self.comboBoxBegHr.findText("7")
        self.comboBoxBegHr.setCurrentIndex(self.index)
        self.comboBoxBegHr.setEditable(True)
        self.leditBeghr = self.comboBoxBegHr.lineEdit()
        self.leditBeghr.setAlignment(QtCore.Qt.AlignCenter)
        self.leditBeghr = self.comboBoxBegHr.lineEdit()
        self.leditBeghr.setReadOnly(True)
        self.timeframeMOVESGridLayout.addWidget(self.labelBegHr, 4, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxBegHr, 4, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.timeframeMOVESGridLayout.addWidget(self.emptyPlainText2, 4, 2)

        # Created UI element Timestamp - Ending Hour
        self.labelEndHr = self.createLabelSmall(text="Ending Hour")
        self.labelEndHr.setStyleSheet(" border: 1px solid #000000; ")
        self.labelEndHr.setObjectName("allLabels")
        self.comboBoxEndHr = QComboBox(self)
        self.comboBoxEndHr.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxEndHr.setFixedWidth(125)
        self.comboBoxEndHr.setFixedHeight(30)
        for i in range(1, 25):
            self.number = i
            self.comboBoxEndHr.addItem(str(i))
        self.index = self.comboBoxEndHr.findText("18")
        self.comboBoxEndHr.setCurrentIndex(self.index)
        self.comboBoxEndHr.setEditable(True)
        self.leditEndhr = self.comboBoxEndHr.lineEdit()
        self.leditEndhr.setAlignment(QtCore.Qt.AlignCenter)
        self.leditEndhr = self.comboBoxEndHr.lineEdit()
        self.leditEndhr.setReadOnly(True)
        self.timeframeMOVESGridLayout.addWidget(self.labelEndHr, 4, 3)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxEndHr, 4, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.timeframeMOVESGridLayout.addWidget(emptyLabelE, 5, 0, 1, 4)

        # Created UI element Timestamp - Day Type
        self.labelDayType = self.createLabelSmall(text="Day Type")
        self.labelDayType.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDayType.setObjectName("allLabels")
        self.comboBoxDayType = QComboBox(self)
        self.comboBoxDayType.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxDayType.setFixedWidth(125)
        self.comboBoxDayType.setFixedHeight(30)
        self.comboBoxDayType.addItem("Weekday")
        self.comboBoxDayType.addItem("Weekend")
        self.index = self.comboBoxDayType.findText("Weekday")
        self.comboBoxDayType.setCurrentIndex(self.index)
        self.comboBoxDayType.setEditable(True)
        self.leditDayType = self.comboBoxDayType.lineEdit()
        self.leditDayType.setAlignment(QtCore.Qt.AlignCenter)
        self.leditDayType = self.comboBoxDayType.lineEdit()
        self.leditDayType.setReadOnly(True)
        self.timeframeMOVESGridLayout.addWidget(self.labelDayType, 6, 0)
        self.timeframeMOVESGridLayout.addWidget(self.comboBoxDayType, 6, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.timeframeMOVESGridLayout.addWidget(emptyLabelE, 7, 0, 1, 4)

        # Custom Data Filepaths Label MOVES
        self.customDataFilepathsLabelM = QLabel()
        self.customDataFilepathsLabelM.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#custom-data-filepaths-1",
                                                                      "Custom Data Filepaths"))
        self.customDataFilepathsLabelM.setOpenExternalLinks(True)
        self.customDataFilepathsLabelM.setFixedHeight(30)
        self.customDataFilepathsLabelM.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.customDataFilepathsLabelM, 17, 0, 1, 4)

        # Created UI element - Custom Dtatfiles below Line MOVES
        self.labelCustomDatafilsLineM = QLabel()
        pixmapLine2 = QPixmap('line.png')
        pixmap2 = pixmapLine2.scaledToHeight(15)
        self.labelCustomDatafilsLineM.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLineM, 18, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Data Filepaths MOVES
        self.labelCustomDatafileMOVESExpand = QPushButton()
        self.labelCustomDatafileMOVESExpand.setFixedHeight(30)
        self.labelCustomDatafileMOVESExpand.setFixedWidth(30)
        self.labelCustomDatafileMOVESExpand.setObjectName("expandCollapseIcon")
        self.labelCustomDatafileMOVESExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelCustomDatafileMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelCustomDatafileMOVESExpand, 17, 4)

        self.customDatafileMOVESexpandWidget = QtWidgets.QWidget()
        self.customDatafileMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.customDatafileMOVESGridLayout = QtWidgets.QGridLayout()
        self.customDatafileMOVESexpandWidget.setLayout(self.customDatafileMOVESGridLayout)
        self.customDatafileMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileMOVESexpandWidget, 19, 0, 1, 4)

        def labelCustomDatafileMOVESOnClickEvent():
            if self.customDatafileMOVESexpandWidget.isVisible():
                self.labelCustomDatafileMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelCustomDatafileMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
                self.customDatafileMOVESexpandWidget.setVisible(False)
            else:
                self.labelCustomDatafileMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelCustomDatafileMOVESExpand.setIcon(QtGui.QIcon('minus.png'))
                self.customDatafileMOVESexpandWidget.setVisible(True)

        self.labelCustomDatafileMOVESExpand.clicked.connect(labelCustomDatafileMOVESOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileMOVESGridLayout.addWidget(emptyLabelE, 0, 0, 1, 3)

        # Created UI element AVFT
        self.labelAVFT = self.createLabelSmall(text="AVFT")
        self.labelAVFT.setStyleSheet(" border: 1px solid #000000; ")
        self.labelAVFT.setObjectName("allLabels")
        self.labelAVFT.setToolTip("Select AVFT (fuel fraction by engine type) dataset")
        self.browseBtnAVFT = self.createButton(text="Browse")
        self.browseBtnAVFT.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnAVFT.clicked.connect(self.getfilesAVFT)
        self.lineEditAVFT = QLineEdit(self)
        self.lineEditAVFT.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditAVFT.setText("data/inputs/avft.csv")
        self.lineEditAVFT.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditAVFT.setFixedHeight(30)
        self.customDatafileMOVESGridLayout.addWidget(self.labelAVFT, 3, 0)
        self.customDatafileMOVESGridLayout.addWidget(self.browseBtnAVFT, 3, 1)
        self.customDatafileMOVESGridLayout.addWidget(self.lineEditAVFT, 3, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileMOVESGridLayout.addWidget(emptyLabelE, 4, 0, 1, 3)

        # Created UI element MOVES Region to FIPS Map
        self.labelFips = self.createLabelSmall(text="Region to FIPS Map")
        self.labelFips.setStyleSheet(" border: 1px solid #000000; ")
        self.labelFips.setObjectName("allLabels")
        self.labelFips.setToolTip("Select production region to MOVES FIPS mapping dataset")
        self.browseBtnFips = self.createButton(text="Browse")
        self.browseBtnFips.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnFips.clicked.connect(self.getfilesFips)
        self.lineEditFips = QLineEdit(self)
        self.lineEditFips.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditFips.setText("data/inputs/region_fips_map.csv")
        self.lineEditFips.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditFips.setFixedHeight(30)
        self.customDatafileMOVESGridLayout.addWidget(self.labelFips, 5, 0)
        self.customDatafileMOVESGridLayout.addWidget(self.browseBtnFips, 5, 1)
        self.customDatafileMOVESGridLayout.addWidget(self.lineEditFips, 5, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileMOVESGridLayout.addWidget(emptyLabelE, 6, 0, 1, 3)

        # Created UI element VMT Fractions
        self.labelVMTFraction = QLabel()
        self.labelVMTFraction.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#vmt-fractions",
                                                             "VMT Fractions"))
        self.labelVMTFraction.setOpenExternalLinks(True)
        self.labelVMTFraction.setToolTip("Fraction of vehicle miles traveled (VMT) by road type (must sum to 1)")
        self.labelVMTFraction.setFixedHeight(30)
        self.labelVMTFraction.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.labelVMTFraction, 22, 0, 1, 4)

        # Created UI element - VMT Fractions below Line MOVES
        self.vMTFractionLine = QLabel()
        pixmapLine3 = QPixmap('line.png')
        pixmap3 = pixmapLine3.scaledToHeight(15)
        self.vMTFractionLine.setPixmap(pixmap2)
        self.resize(pixmap3.width(), pixmap3.height())
        self.windowLayout.addWidget(self.vMTFractionLine, 23, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element VMT Fractions
        self.labelVMTFractionExpand = QPushButton()
        self.labelVMTFractionExpand.setFixedHeight(30)
        self.labelVMTFractionExpand.setFixedWidth(30)
        self.labelVMTFractionExpand.setObjectName("expandCollapseIcon")
        self.labelVMTFractionExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelVMTFractionExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelVMTFractionExpand, 22, 4)

        self.vmtexpandWidget = QtWidgets.QWidget()
        self.vmtexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.vmtGridLayout = QtWidgets.QGridLayout()
        self.vmtexpandWidget.setLayout(self.vmtGridLayout)
        self.vmtexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.vmtexpandWidget, 26, 0, 1, 4)

        def labelVMTFractionOnClickEvent():
            if self.vmtexpandWidget.isVisible():
                self.labelVMTFractionExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelVMTFractionExpand.setIcon(QtGui.QIcon('plus.png'))
                self.vmtexpandWidget.setVisible(False)
            else:
                self.labelVMTFractionExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelVMTFractionExpand.setIcon(QtGui.QIcon('minus.png'))
                self.vmtexpandWidget.setVisible(True)

        self.labelVMTFractionExpand.clicked.connect(labelVMTFractionOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.vmtGridLayout.addWidget(emptyLabelE, 0, 0, 1, 3)

        # Created UI element VMT - Rural Restricted
        self.labelRuralRes = self.createLabelSmall(text="Rural Restricted")
        self.labelRuralRes.setStyleSheet(" border: 1px solid #000000; ")
        self.labelRuralRes.setObjectName("allLabels")
        self.lineEditRuralRes = QLineEdit(self)
        self.lineEditRuralRes.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditRuralRes.setFixedWidth(116)
        self.lineEditRuralRes.setFixedHeight(30)
        self.lineEditRuralRes.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralRes.setValidator(self.onlyFlaot)
        self.lineEditRuralRes.setText("0.3")
        self.vmtGridLayout.addWidget(self.labelRuralRes, 1, 0)
        self.vmtGridLayout.addWidget(self.lineEditRuralRes, 1, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.vmtGridLayout.addWidget(self.emptyPlainText2, 1, 2)

        # Created UI element VMT - Urban Restricted
        self.labelUrbanRes = self.createLabelSmall(text="Urban Restricted")
        self.labelUrbanRes.setStyleSheet(" border: 1px solid #000000; ")
        self.labelUrbanRes.setObjectName("allLabels")
        self.lineEditUrbanRes = QLineEdit(self)
        self.lineEditUrbanRes.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditUrbanRes.setFixedWidth(116)
        self.lineEditUrbanRes.setFixedHeight(30)
        self.lineEditUrbanRes.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanRes.setValidator(self.onlyFlaot)
        self.lineEditUrbanRes.setText("0.21")
        self.vmtGridLayout.addWidget(self.labelUrbanRes, 1, 3)
        self.vmtGridLayout.addWidget(self.lineEditUrbanRes, 1, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.vmtGridLayout.addWidget(emptyLabelE, 2, 0, 1, 3)

        # Created UI element VMT - Rural Unrestricted
        self.labelRuralUnres = self.createLabelSmall(text="Rural Unrestricted")
        self.labelRuralUnres.setStyleSheet(" border: 1px solid #000000; ")
        self.labelRuralUnres.setObjectName("allLabels")
        self.lineEditRuralUnres = QLineEdit(self)
        self.lineEditRuralUnres.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditRuralUnres.setFixedWidth(116)
        self.lineEditRuralUnres.setFixedHeight(30)
        self.lineEditRuralUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditRuralUnres.setValidator(self.onlyFlaot)
        self.lineEditRuralUnres.setText("0.28")
        self.vmtGridLayout.addWidget(self.labelRuralUnres, 3, 0)
        self.vmtGridLayout.addWidget(self.lineEditRuralUnres, 3, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.vmtGridLayout.addWidget(self.emptyPlainText2, 3, 2)

        # Created UI element VMT - Urban Unrestricted
        self.labelUrbanUnres = self.createLabelSmall(text="Urban Unrestricted")
        self.labelUrbanUnres.setStyleSheet(" border: 1px solid #000000; ")
        self.labelUrbanUnres.setObjectName("allLabels")
        self.lineEditUrbanUnres = QLineEdit()
        self.lineEditUrbanUnres.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditUrbanUnres.setFixedWidth(116)
        self.lineEditUrbanUnres.setFixedHeight(30)
        self.lineEditUrbanUnres.setFixedHeight(30)
        self.lineEditUrbanUnres.setAlignment(QtCore.Qt.AlignCenter)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditUrbanUnres.setValidator(self.onlyFlaot)
        self.lineEditUrbanUnres.setText("0.21")
        self.vmtGridLayout.addWidget(self.labelUrbanUnres, 3, 3)
        self.vmtGridLayout.addWidget(self.lineEditUrbanUnres, 3, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.vmtGridLayout.addWidget(emptyLabelE, 4, 0, 1, 3)

        # Advanced Options Label MOVES
        self.advOptionsLabelM = QLabel()
        self.advOptionsLabelM.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#advanced-options-1",
                                                             "Advanced Options"))
        self.advOptionsLabelM.setOpenExternalLinks(True)
        self.advOptionsLabelM.setFixedHeight(30)
        self.advOptionsLabelM.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.advOptionsLabelM, 27, 0, 1, 4)

        # Created UI element - Advanced Optiones below Line
        self.labelAdvOptionsLineM = QLabel()
        pixmapLine2 = QPixmap('line.png')
        pixmap2 = pixmapLine2.scaledToHeight(15)
        self.labelAdvOptionsLineM.setPixmap(pixmap2)
        self.resize(pixmap2.width(), pixmap2.height())
        self.windowLayout.addWidget(self.labelAdvOptionsLineM, 28, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Advanced Options MOVES
        self.labelAdvOptionsMOVESExpand = QPushButton()
        self.labelAdvOptionsMOVESExpand.setFixedHeight(30)
        self.labelAdvOptionsMOVESExpand.setFixedWidth(30)
        self.labelAdvOptionsMOVESExpand.setObjectName("expandCollapseIcon")
        self.labelAdvOptionsMOVESExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelAdvOptionsMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelAdvOptionsMOVESExpand, 27, 4)

        self.advOptionsMOVESexpandWidget = QtWidgets.QWidget()
        self.advOptionsMOVESexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.advOptionsMOVESGridLayout = QtWidgets.QGridLayout()
        self.advOptionsMOVESexpandWidget.setLayout(self.advOptionsMOVESGridLayout)
        self.advOptionsMOVESexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.advOptionsMOVESexpandWidget, 31, 0, 1, 4)

        def labelAdvOptionsMOVESOnClickEvent():
            if self.advOptionsMOVESexpandWidget.isVisible():
                self.labelAdvOptionsMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelAdvOptionsMOVESExpand.setIcon(QtGui.QIcon('plus.png'))
                self.advOptionsMOVESexpandWidget.setVisible(False)
            else:
                self.labelAdvOptionsMOVESExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelAdvOptionsMOVESExpand.setIcon(QtGui.QIcon('minus.png'))
                self.advOptionsMOVESexpandWidget.setVisible(True)

        self.labelAdvOptionsMOVESExpand.clicked.connect(labelAdvOptionsMOVESOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsMOVESGridLayout.addWidget(emptyLabelE, 0, 0, 1, 3)

        # Created UI element No of Trucks used
        self.labelNoofTruck = self.createLabelBig(text="Number Of Trucks" + "\n" + " Used")
        self.labelNoofTruck.setStyleSheet(" border: 1px solid #000000; ")
        self.labelNoofTruck.setObjectName("allLabels")
        self.labelNoofTruck.setToolTip("Number of trucks used to transport feedstock")
        self.spinBoxNoofTruck = QSpinBox()
        self.spinBoxNoofTruck.setStyleSheet(" border: 1px solid #000000; ")
        self.spinBoxNoofTruck.setFixedWidth(116)
        self.spinBoxNoofTruck.setFixedHeight(30)
        self.spinBoxNoofTruck.setMinimum(1)
        self.spinBoxNoofTruck.setValue(1)
        self.leditNofTrucksUsed = self.spinBoxNoofTruck.lineEdit()
        self.leditNofTrucksUsed.setAlignment(QtCore.Qt.AlignCenter)
        self.leditNofTrucksUsed = self.spinBoxNoofTruck.lineEdit()
        self.leditNofTrucksUsed.setReadOnly(True)
        self.advOptionsMOVESGridLayout.addWidget(self.labelNoofTruck, 1, 0)
        self.advOptionsMOVESGridLayout.addWidget(self.spinBoxNoofTruck, 1, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsMOVESGridLayout.addWidget(emptyLabelE, 2, 0, 1, 3)

        # Created UI element HPMSV type ID
        self.labelHPMSVtypeId = self.createLabelBig(text="HPMSV ID")
        self.labelHPMSVtypeId.setStyleSheet(" border: 1px solid #000000; ")
        self.labelHPMSVtypeId.setObjectName("allLabels")
        self.labelHPMSVtypeId.setToolTip("Enter Highway Performance Monitoring System Vehicle ID. Default indicates a generic combination truck.")
        self.spinBoxHPMSVtypeId = QSpinBox()
        self.spinBoxHPMSVtypeId.setStyleSheet(" border: 1px solid #000000; ")
        self.spinBoxHPMSVtypeId.setFixedWidth(116)
        self.spinBoxHPMSVtypeId.setFixedHeight(30)
        self.spinBoxHPMSVtypeId.setMinimum(1)
        self.spinBoxHPMSVtypeId.setValue(60)
        self.leditHPMSVtypeId = self.spinBoxHPMSVtypeId.lineEdit()
        self.leditHPMSVtypeId.setAlignment(QtCore.Qt.AlignCenter)
        self.leditHPMSVtypeId = self.spinBoxHPMSVtypeId.lineEdit()
        self.leditHPMSVtypeId.setReadOnly(True)
        self.advOptionsMOVESGridLayout.addWidget(self.labelHPMSVtypeId, 3, 0)
        self.advOptionsMOVESGridLayout.addWidget(self.spinBoxHPMSVtypeId, 3, 1)

        # Add horizontal space between elements
        self.emptyPlainText3 = QLabel()
        self.emptyPlainText3.setStyleSheet("border-color: white;")
        self.emptyPlainText3.setFixedWidth(55)
        self.emptyPlainText3.setFixedHeight(30)
        self.advOptionsMOVESGridLayout.addWidget(self.emptyPlainText3, 3, 2)

        # Created UI element Source type ID
        self.labelSourceTypeId = self.createLabelBig(text="Source Type ID")
        self.labelSourceTypeId.setStyleSheet(" border: 1px solid #000000; ")
        self.labelSourceTypeId.setObjectName("allLabels")
        self.labelSourceTypeId.setToolTip("Enter source type ID. Default indicates a short-haul combination truck.")
        self.spinBoxSourceTypeId = QSpinBox()
        self.spinBoxSourceTypeId.setStyleSheet(" border: 1px solid #000000; ")
        self.spinBoxSourceTypeId.setFixedWidth(116)
        self.spinBoxSourceTypeId.setFixedHeight(30)
        self.spinBoxSourceTypeId.setMinimum(1)
        self.spinBoxSourceTypeId.setValue(61)
        self.leditSourceTypeId = self.spinBoxSourceTypeId.lineEdit()
        self.leditSourceTypeId.setAlignment(QtCore.Qt.AlignCenter)
        self.leditSourceTypeId = self.spinBoxSourceTypeId.lineEdit()
        self.leditSourceTypeId.setReadOnly(True)
        self.advOptionsMOVESGridLayout.addWidget(self.labelSourceTypeId, 3, 3)
        self.advOptionsMOVESGridLayout.addWidget(self.spinBoxSourceTypeId, 3, 4)

    # CHeck for consistent input for year
    def handleItemPressedMoves(self, index):
        if str(self.comboBoxYearNon.currentText()) != str(self.comboBoxYear.currentText()):
            self.comboBoxYear.setStyleSheet(
                """QComboBox { background-color: red; color: white }""")

    # Functions used for Moves Path

    def getfilesMovesPath(self):
        fileNameMovesPath = QFileDialog.getExistingDirectory(self, "Browse")
        if fileNameMovesPath != "":
            selectedFileNameMovesPath = str(fileNameMovesPath).split(',')
            self.lineEditMovesPath.setText(selectedFileNameMovesPath[0])

    # function used for MySQL executable
    def getfilesMysqlBin(self):
        fileNameMysqlBin = QFileDialog.getExistingDirectory(self, "Browse")
        if fileNameMysqlBin != "":
            selectedFileNameMysqlBin = str(fileNameMysqlBin).split(',')
            self.lineEditMysqlBin.setText(selectedFileNameMysqlBin[0])

    # function used for MySQL dump executable
    def getfilesMysqlDumpBin(self):
        fileNameMysqlDumpBin = QFileDialog.getExistingDirectory(self, "Browse")
        if fileNameMysqlDumpBin != "":
            selectedFileNameMysqlDumpBin = str(fileNameMysqlDumpBin).split(',')
            self.lineEditMysqlDumpBin.setText(selectedFileNameMysqlDumpBin[0])

    # Functions used for Truck Capacity

    def getfilesTruckCapa(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTruckCapa[0] != "":
            selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
            self.lineEditTruckCapa.setText(selectedFileNameTruckCapa[1])

    # Functions used for AVFT

    def getfilesAVFT(self):
        fileNameAVFT = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameAVFT[0] != "":
            selectedFileNameAVFT = fileNameAVFT[0].split("FPEAM/")
            self.lineEditAVFT.setText(selectedFileNameAVFT[1])

    # Functions used for Fips

    def getfilesFips(self):
        fileNameFips = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameFips[0] != "":
            selectedFileNameFips = fileNameFips[0].split("FPEAM/")
            self.lineEditFips.setText(selectedFileNameFips[1])

    # Functions used for Moves Datafiles

    def getfilesDatafiles(self):
        fileNameDatafile = QFileDialog.getExistingDirectory(self, "Browse")
        if fileNameDatafile != "":
            selectedFileNameDatafile = str(fileNameDatafile).split(',')
            self.lineEditDatafiles.setText(selectedFileNameDatafile[0])

    def getEnteredText(self):
        self.enteredText.setText(self.lineEditVMTperTruck)

        #########################################################################################################################

        #### Nonroad Module   #####

    def setupUINonroad(self):
        # NONROAD tab created
        self.tabNonroad = QtWidgets.QWidget()
        self.tabNonroad.resize(WIDTH, HEIGHT - 200)
        # NONROAD tab added
        self.centralwidget.addTab(self.tabNonroad, self.getSpacedNames("NONROAD"))

        # NONROAD code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSpacing(15)
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        # Add Scrollbar to NONROAD tab
        self.scrollAreaNONROAD = QScrollArea(self.tabNonroad)
        self.scrollAreaNONROAD.setWidgetResizable(True)
        self.scrollAreaNONROAD.resize(WIDTH, HEIGHT)
        self.scrollAreaNONROAD.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaNONROAD.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.innerWidgetNONROAD = QtWidgets.QWidget()
        self.innerWidgetNONROAD.resize(WIDTH, HEIGHT)
        self.scrollAreaNONROAD.setWidget(self.innerWidgetNONROAD)
        self.innerWidgetNONROAD.setLayout(self.windowLayout)

        # Add Vertical spce at the top
        emptyLabelTop = QLabel()
        emptyLabelTop.setFixedHeight(30)
        self.windowLayout.addWidget(emptyLabelTop, 0, 0, 1, 5)

        # add link to readme in upper-left-hand corner of tab
        self.nonroadhelplink = QLabel()
        self.nonroadhelplink.setText(self.createLink("https://github.com/NREL/fpeam/tree/master#nonroad",
                                                   "Readme"))
        self.nonroadhelplink.setOpenExternalLinks(True)
        self.nonroadhelplink.setFixedHeight(30)
        self.windowLayout.addWidget(self.nonroadhelplink, 1, 0, 1, 4)

        # Created UI element NONROAD Datafiles
        self.labelDatafilesNon = self.createLabelSmall(text="Data Folder")
        self.labelDatafilesNon.setObjectName("allLabels")
        self.labelDatafilesNon.setToolTip("Select path where NONROAD input and output output data files will be saved")
        self.browseBtnDatafilesNon = self.createButton(text="Browse")
        self.browseBtnDatafilesNon.clicked.connect(self.getfilesDatafilesNon)
        self.lineEditDatafilesNon = QLineEdit(self)
        self.lineEditDatafilesNon.setText("C:/Nonroad")
        self.lineEditDatafilesNon.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditDatafilesNon.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelDatafilesNon, 2, 0)
        self.windowLayout.addWidget(self.browseBtnDatafilesNon, 2, 1)
        self.windowLayout.addWidget(self.lineEditDatafilesNon, 2, 2, 1, 3)

        # Created UI element Nonroad executable path
        self.labelNonExePath = self.createLabelSmall(text="Path to EXE")
        self.labelNonExePath.setObjectName("allLabels")
        self.labelNonExePath.setToolTip("Select path where NONROAD executable is located")
        self.browseBtnNonExePath = self.createButton(text="Browse")
        self.browseBtnNonExePath.clicked.connect(self.getfilesNonExePath)
        self.lineEditNonExePath = QLineEdit(self)
        self.lineEditNonExePath.setText("C:/MOVES2014b/NONROAD/NR08a")
        self.lineEditNonExePath.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditNonExePath.setFixedHeight(30)
        self.windowLayout.addWidget(self.labelNonExePath, 3, 0)
        self.windowLayout.addWidget(self.browseBtnNonExePath, 3, 1)
        self.windowLayout.addWidget(self.lineEditNonExePath, 3, 2, 1, 3)

        # Created UI element Year - NONROAD
        self.labelYearNon = self.createLabelSmall(text="Analysis Year")
        self.labelYearNon.setObjectName("allLabels")
        self.labelYearNon.setToolTip("Start year of equipment")
        self.comboBoxYearNon = QComboBox(self)
        self.comboBoxYearNon.setFixedHeight(30)
        for i in range(2018, 1990, -1):
            self.number = i
            self.comboBoxYearNon.addItem(str(i))
        self.index = self.comboBoxYearNon.findText("2017")
        self.comboBoxYearNon.setCurrentIndex(self.index)
        self.comboBoxYearNon.setEditable(True)
        self.leditYear = self.comboBoxYearNon.lineEdit()
        self.leditYear.setAlignment(QtCore.Qt.AlignCenter)
        self.leditYear = self.comboBoxYearNon.lineEdit()
        self.leditYear.setReadOnly(True)
        self.labelYearNonErrorMsg = QLabel()
        self.labelYearNonErrorMsg.setObjectName("yearErrorMsg")
        self.labelYearNonErrorMsg.setFixedHeight(30)
        self.labelYearNonErrorMsg.setText("")
        self.labelYearNonErrorMsg.setStyleSheet("border: 1px solid white;")
        self.windowLayout.addWidget(self.labelYearNon, 4, 0)
        self.windowLayout.addWidget(self.comboBoxYearNon, 4, 1)
        self.windowLayout.addWidget(self.labelYearNonErrorMsg, 4, 2, 1, 3)
        # Check whether Moves year matches with Nonroad year
        self.comboBoxYearNon.currentIndexChanged.connect(self.handleItemPressed)

        # Database Connection Parameters Label NONROAD
        self.dbConnectionParaLabelN = QLabel()
        self.dbConnectionParaLabelN.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#database-connection-parameters-1",
                                                                   "Database Connection Parameters"))
        self.dbConnectionParaLabelN.setOpenExternalLinks(True)
        self.dbConnectionParaLabelN.setFixedHeight(30)
        self.dbConnectionParaLabelN.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.dbConnectionParaLabelN, 5, 0, 1, 4)

        # Created UI element - Advanced Optiones below Line NONROAD
        self.dbConnectionParaLineN = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.dbConnectionParaLineN.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dbConnectionParaLineN, 6, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Database Connection Parameters NONROAD
        self.labeldbConnectionsNONROADExpand = QPushButton()
        self.labeldbConnectionsNONROADExpand.setFixedHeight(30)
        self.labeldbConnectionsNONROADExpand.setFixedWidth(30)
        self.labeldbConnectionsNONROADExpand.setObjectName("expandCollapseIcon")
        self.labeldbConnectionsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
        self.labeldbConnectionsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labeldbConnectionsNONROADExpand, 5, 4)

        self.dbConnectionsNONROADexpandWidget = QtWidgets.QWidget()
        self.dbConnectionsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.dbConnectionsNONROADGridLayout = QtWidgets.QGridLayout()
        self.dbConnectionsNONROADexpandWidget.setLayout(self.dbConnectionsNONROADGridLayout)
        self.dbConnectionsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.dbConnectionsNONROADexpandWidget, 7, 0, 1, 4)

        def labelDbConnectionsNONROADOnClickEvent():
            if self.dbConnectionsNONROADexpandWidget.isVisible():
                self.labeldbConnectionsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labeldbConnectionsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
                self.dbConnectionsNONROADexpandWidget.setVisible(False)
            else:
                self.labeldbConnectionsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labeldbConnectionsNONROADExpand.setIcon(QtGui.QIcon('minus.png'))
                self.dbConnectionsNONROADexpandWidget.setVisible(True)

        self.labeldbConnectionsNONROADExpand.clicked.connect(labelDbConnectionsNONROADOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsNONROADGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Database Host
        self.labelDbHostN = self.createLabelSmall(text="Database Host")
        self.labelDbHostN.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbHostN.setObjectName("allLabels")
        self.labelDbHostN.setToolTip("Database host")
        self.lineEditDbHostN = QLineEdit(self)
        self.lineEditDbHostN.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbHostN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbHostN.setFixedHeight(30)
        self.lineEditDbHostN.setFixedWidth(125)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditDbHostN.setValidator(validator)
        self.lineEditDbHostN.setText("localhost")
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbHostN, 1, 0)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbHostN, 1, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.dbConnectionsNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 2)

        # Created UI element Database Username
        self.labelDbUsernameN = self.createLabelSmall(text="Username")
        self.labelDbUsernameN.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbUsernameN.setObjectName("allLabels")
        self.labelDbUsernameN.setToolTip("Database username")
        self.lineEditDbUsernameN = QLineEdit(self)
        self.lineEditDbUsernameN.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbUsernameN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbUsernameN.setFixedHeight(30)
        self.lineEditDbUsernameN.setFixedWidth(125)
        self.lineEditDbUsernameN.setText("root")
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbUsernameN, 1, 3)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbUsernameN, 1, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsNONROADGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element Database Name
        self.labelDbNameN = self.createLabelSmall(text="Database Name")
        self.labelDbNameN.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbNameN.setObjectName("allLabels")
        self.labelDbNameN.setToolTip("Database name")
        self.lineEditDbNameN = QLineEdit(self)
        self.lineEditDbNameN.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbNameN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbNameN.setFixedHeight(30)
        self.lineEditDbNameN.setFixedWidth(125)
        self.lineEditDbNameN.setText("movesdb20180517")
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbNameN, 3, 0)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbNameN, 3, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.dbConnectionsNONROADGridLayout.addWidget(self.emptyPlainText2, 3, 2)

        # Created UI element Database Password
        self.labelDbPwdN = self.createLabelSmall(text="Password")
        self.labelDbPwdN.setStyleSheet(" border: 1px solid #000000; ")
        self.labelDbPwdN.setObjectName("allLabels")
        self.labelDbPwdN.setToolTip("Database password")
        self.lineEditDbPwdN = QLineEdit(self)
        self.lineEditDbPwdN.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditDbPwdN.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditDbPwdN.setFixedHeight(30)
        self.lineEditDbPwdN.setFixedWidth(125)
        self.lineEditDbPwdN.setEchoMode(QLineEdit.Password)
        self.lineEditDbPwdN.show()
        self.lineEditDbPwdN.setText("root")
        self.dbConnectionsNONROADGridLayout.addWidget(self.labelDbPwdN, 3, 3)
        self.dbConnectionsNONROADGridLayout.addWidget(self.lineEditDbPwdN, 3, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dbConnectionsNONROADGridLayout.addWidget(emptyLabelE, 4, 0, 1, 4)

        # Data Label
        self.dataLabel = QLabel()
        self.dataLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#data-labels",
                                                      "Data Labels"))
        self.dataLabel.setOpenExternalLinks(True)
        self.dataLabel.setFixedHeight(30)
        self.dataLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.dataLabel, 8, 0, 1, 4)

        # Created UI element - Data Labels Line
        self.dataLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.dataLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.dataLabelLine, 9, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Database Connection Parameters NONROAD
        self.labelDataLabelsNONROADExpand = QPushButton()
        self.labelDataLabelsNONROADExpand.setFixedHeight(30)
        self.labelDataLabelsNONROADExpand.setFixedWidth(30)
        self.labelDataLabelsNONROADExpand.setObjectName("expandCollapseIcon")
        self.labelDataLabelsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelDataLabelsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelDataLabelsNONROADExpand, 8, 4)

        self.dataLabelsNONROADexpandWidget = QtWidgets.QWidget()
        self.dataLabelsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.dtaLabelsNONROADGridLayout = QtWidgets.QGridLayout()
        self.dataLabelsNONROADexpandWidget.setLayout(self.dtaLabelsNONROADGridLayout)
        self.dataLabelsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.dataLabelsNONROADexpandWidget, 10, 0, 1, 4)

        def labelDataLabelsNONROADOnClickEvent():
            if self.dataLabelsNONROADexpandWidget.isVisible():
                self.labelDataLabelsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelDataLabelsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
                self.dataLabelsNONROADexpandWidget.setVisible(False)
            else:
                self.labelDataLabelsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelDataLabelsNONROADExpand.setIcon(QtGui.QIcon('minus.png'))
                self.dataLabelsNONROADexpandWidget.setVisible(True)

        self.labelDataLabelsNONROADExpand.clicked.connect(labelDataLabelsNONROADOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dtaLabelsNONROADGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeNon = self.createLabelBig(text="Feedstock Measure" + "\n" + " Type")
        self.labelFeedMeasureTypeNon.setStyleSheet(" border: 1px solid #000000; ")
        self.labelFeedMeasureTypeNon.setObjectName("allLabels")
        self.labelFeedMeasureTypeNon.setToolTip("Enter feedstock measure type identifier")
        self.lineEditFeedMeasureTypeNon = QLineEdit()
        self.lineEditFeedMeasureTypeNon.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditFeedMeasureTypeNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureTypeNon.setFixedHeight(40)
        self.lineEditFeedMeasureTypeNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeNon.setValidator(validator)
        # Set Default text
        self.lineEditFeedMeasureTypeNon.setText("harvested")
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelFeedMeasureTypeNon, 1, 0)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditFeedMeasureTypeNon, 1, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.dtaLabelsNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 2)

        # Created UI element Time Resource Name
        self.labelTimeResNamesNon = self.createLabelBig(text="Time Resource Name")
        self.labelTimeResNamesNon.setStyleSheet(" border: 1px solid #000000; ")
        self.labelTimeResNamesNon.setObjectName("allLabels")
        self.labelTimeResNamesNon.setToolTip("Equipment table row identifier")
        self.lineEditTimeResNamesNon = QLineEdit()
        self.lineEditTimeResNamesNon.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditTimeResNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditTimeResNamesNon.setFixedHeight(40)
        self.lineEditTimeResNamesNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditTimeResNamesNon.setValidator(validator)
        self.lineEditTimeResNamesNon.setText("time")
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelTimeResNamesNon, 1, 3)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditTimeResNamesNon, 1, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dtaLabelsNONROADGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element Irrigation Feedstock Measure Type Nonroad
        self.labelFeedMeasureTypeIrrigNon = self.createLabelBig(text="Irrigation Feedstock " + "\n" + "Measure Type")
        self.labelFeedMeasureTypeIrrigNon.setStyleSheet(" border: 1px solid #000000; ")
        self.labelFeedMeasureTypeIrrigNon.setObjectName("allLabels")
        self.labelFeedMeasureTypeIrrigNon.setToolTip(
            "Production table identifier for irrigation activity calculation")
        self.lineEditFeedMeasureTypeIrrigNon = QLineEdit()
        self.lineEditFeedMeasureTypeIrrigNon.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditFeedMeasureTypeIrrigNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureTypeIrrigNon.setFixedHeight(40)
        self.lineEditFeedMeasureTypeIrrigNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedMeasureTypeIrrigNon.setValidator(validator)
        self.lineEditFeedMeasureTypeIrrigNon.setText("planted")
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelFeedMeasureTypeIrrigNon, 3, 0)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditFeedMeasureTypeIrrigNon, 3, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.dtaLabelsNONROADGridLayout.addWidget(self.emptyPlainText2, 3, 2)

        # Created UI element Irrigation Feedstock Names
        self.labelIrrigationFeedNamesNon = self.createLabelBig(text="Irrigation Feedstock" + "\n" + "Name")
        self.labelIrrigationFeedNamesNon.setStyleSheet(" border: 1px solid #000000; ")
        self.labelIrrigationFeedNamesNon.setObjectName("allLabels")
        self.labelIrrigationFeedNamesNon.setToolTip("List of irrigated feedstocks")
        self.lineEditFeedIrrigNamesNon = QLineEdit()
        self.lineEditFeedIrrigNamesNon.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditFeedIrrigNamesNon.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedIrrigNamesNon.setFixedHeight(40)
        self.lineEditFeedIrrigNamesNon.setFixedWidth(125)
        self.regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(self.regex)
        self.lineEditFeedIrrigNamesNon.setValidator(validator)
        self.lineEditFeedIrrigNamesNon.setText("corn grain")
        self.dtaLabelsNONROADGridLayout.addWidget(self.labelIrrigationFeedNamesNon, 3, 3)
        self.dtaLabelsNONROADGridLayout.addWidget(self.lineEditFeedIrrigNamesNon, 3, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.dtaLabelsNONROADGridLayout.addWidget(emptyLabelE, 4, 0, 1, 4)

        # Custom Data Filepaths Label
        self.cusromDatafileLabel = QLabel()
        self.cusromDatafileLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#custom-data-filepaths-2",
                                                                "Custom Data Filepaths"))
        self.cusromDatafileLabel.setOpenExternalLinks(True)
        self.cusromDatafileLabel.setFixedHeight(30)
        self.cusromDatafileLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.cusromDatafileLabel, 13, 0, 1, 4)

        # Custom Data Filepaths Label Line
        self.customDatafileLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.customDatafileLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.customDatafileLabelLine, 14, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Datafiles NONROAD
        self.labelcustomDatafileNONROADExpand = QPushButton()
        self.labelcustomDatafileNONROADExpand.setFixedHeight(30)
        self.labelcustomDatafileNONROADExpand.setFixedWidth(30)
        self.labelcustomDatafileNONROADExpand.setObjectName("expandCollapseIcon")
        self.labelcustomDatafileNONROADExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelcustomDatafileNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelcustomDatafileNONROADExpand, 13, 4)

        self.customDatafileNONROADexpandWidget = QtWidgets.QWidget()
        self.customDatafileNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.customDatafileNONROADGridLayout = QtWidgets.QGridLayout()
        self.customDatafileNONROADexpandWidget.setLayout(self.customDatafileNONROADGridLayout)
        self.customDatafileNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileNONROADexpandWidget, 15, 0, 1, 4)

        def labelCustomDatafileNONROADOnClickEvent():
            if self.customDatafileNONROADexpandWidget.isVisible():
                self.labelcustomDatafileNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelcustomDatafileNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
                self.customDatafileNONROADexpandWidget.setVisible(False)
            else:
                self.labelcustomDatafileNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelcustomDatafileNONROADExpand.setIcon(QtGui.QIcon('minus.png'))
                self.customDatafileNONROADexpandWidget.setVisible(True)

        self.labelcustomDatafileNONROADExpand.clicked.connect(labelCustomDatafileNONROADOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileNONROADGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Region Nonroad Irrigation
        self.labelNonIrrig = self.createLabelBig(text="Irrigation Activity")
        self.labelNonIrrig.setObjectName("allLabels")
        self.labelNonIrrig.setStyleSheet(" border: 1px solid #000000; ")
        self.labelNonIrrig.setToolTip("Select irrigation dataset")
        self.browseBtnNonIrrig = self.createButton(text="Browse", height=40)
        self.browseBtnNonIrrig.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnNonIrrig.clicked.connect(self.getfilesNonIrrig)
        self.lineEditNonIrrig = QLineEdit(self)
        self.lineEditNonIrrig.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditNonIrrig.setText("data/inputs/irrigation.csv")
        self.lineEditNonIrrig.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditNonIrrig.setFixedHeight(40)
        self.customDatafileNONROADGridLayout.addWidget(self.labelNonIrrig, 1, 0)
        self.customDatafileNONROADGridLayout.addWidget(self.browseBtnNonIrrig, 1, 1)
        self.customDatafileNONROADGridLayout.addWidget(self.lineEditNonIrrig, 1, 2, 1, 5)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileNONROADGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element NONROAD Equipment
        self.labelNonEquip = self.createLabelBig(text="Equipment Specs")
        self.labelNonEquip.setObjectName("allLabels")
        self.labelNonEquip.setStyleSheet(" border: 1px solid #000000; ")
        self.labelNonEquip.setToolTip("Select NONROAD equipment specifications dataset")
        self.browseBtnNonEquip = self.createButton(text="Browse", height=40)
        self.browseBtnNonEquip.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnNonEquip.clicked.connect(self.getfilesNonEquip)
        self.lineEditNonEquip = QLineEdit(self)
        self.lineEditNonEquip.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditNonEquip.setText("data/inputs/nonroad_equipment.csv")
        self.lineEditNonEquip.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditNonEquip.setFixedHeight(40)
        self.customDatafileNONROADGridLayout.addWidget(self.labelNonEquip, 3, 0)
        self.customDatafileNONROADGridLayout.addWidget(self.browseBtnNonEquip, 3, 1)
        self.customDatafileNONROADGridLayout.addWidget(self.lineEditNonEquip, 3, 2, 1, 5)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileNONROADGridLayout.addWidget(emptyLabelE, 4, 0, 1, 4)

        # Created UI element Region FIPs Map Nonroad
        self.labelFipsNon = self.createLabelBig(text="Region to FIPS Map")
        self.labelFipsNon.setObjectName("allLabels")
        self.labelFipsNon.setStyleSheet(" border: 1px solid #000000; ")
        self.labelFipsNon.setToolTip("Select production region to NONROAD FIPS mapping dataset")
        self.browseBtnFipsNon = self.createButton(text="Browse", height=40)
        self.browseBtnFipsNon.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnFipsNon.clicked.connect(self.getfilesFipsNon)
        self.lineEditFipsNon = QLineEdit(self)
        self.lineEditFipsNon.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditFipsNon.setText("data/inputs/region_fips_map.csv")
        self.lineEditFipsNon.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditFipsNon.setFixedHeight(40)
        self.customDatafileNONROADGridLayout.addWidget(self.labelFipsNon, 5, 0)
        self.customDatafileNONROADGridLayout.addWidget(self.browseBtnFipsNon, 5, 1)
        self.customDatafileNONROADGridLayout.addWidget(self.lineEditFipsNon, 5, 2, 1, 5)

        # Empty label
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileNONROADGridLayout.addWidget(emptyLabelE, 6, 0, 1, 4)

        # Operating Temperature Label
        self.opTempLabel = QLabel()
        self.opTempLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#operating-temperature",
                                                        "Operating Temperature"))
        self.opTempLabel.setOpenExternalLinks(True)
        self.opTempLabel.setFixedHeight(30)
        self.opTempLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.opTempLabel, 17, 0, 1, 4)

        # Operating Temperature Label Line
        self.opTempLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.opTempLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.opTempLabelLine, 18, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Operating Temperature NONROAD
        self.labelTempNONROADExpand = QPushButton()
        self.labelTempNONROADExpand.setFixedHeight(30)
        self.labelTempNONROADExpand.setFixedWidth(30)
        self.labelTempNONROADExpand.setObjectName("expandCollapseIcon")
        self.labelTempNONROADExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelTempNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelTempNONROADExpand, 17, 4)

        self.tempNONROADexpandWidget = QtWidgets.QWidget()
        self.tempNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.tempNONROADGridLayout = QtWidgets.QGridLayout()
        self.tempNONROADexpandWidget.setLayout(self.tempNONROADGridLayout)
        self.tempNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.tempNONROADexpandWidget, 19, 0, 1, 4)

        def labelTempNONROADOnClickEvent():
            if self.tempNONROADexpandWidget.isVisible():
                self.labelTempNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelTempNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
                self.tempNONROADexpandWidget.setVisible(False)
            else:
                self.labelTempNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelTempNONROADExpand.setIcon(QtGui.QIcon('minus.png'))
                self.tempNONROADexpandWidget.setVisible(True)

        self.labelTempNONROADExpand.clicked.connect(labelTempNONROADOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.tempNONROADGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Minimum Temperature
        self.labelMinTemp = self.createLabelSmall(text="Minimum Temp (" + "\N{DEGREE SIGN}" + "F)")
        self.labelMinTemp.setObjectName("allLabels")
        self.labelMinTemp.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMinTemp = QLineEdit(self)
        self.lineEditMinTemp.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMinTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditMinTemp.setFixedHeight(30)
        self.lineEditMinTemp.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMinTemp.setValidator(self.onlyFlaot)
        self.lineEditMinTemp.setText("50")
        self.tempNONROADGridLayout.addWidget(self.labelMinTemp, 1, 0)
        self.tempNONROADGridLayout.addWidget(self.lineEditMinTemp, 1, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.tempNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 2)

        # Created UI element Average Temperature
        self.labelMeanTemp = self.createLabelSmall(text="Average Temp (" + "\N{DEGREE SIGN}" + "F)")
        self.labelMeanTemp.setObjectName("allLabels")
        self.labelMeanTemp.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMeanTemp = QLineEdit(self)
        self.lineEditMeanTemp.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMeanTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditMeanTemp.setFixedHeight(30)
        self.lineEditMeanTemp.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMeanTemp.setValidator(self.onlyFlaot)
        self.lineEditMeanTemp.setText("60")
        self.tempNONROADGridLayout.addWidget(self.labelMeanTemp, 1, 3)
        self.tempNONROADGridLayout.addWidget(self.lineEditMeanTemp, 1, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.tempNONROADGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element Maximum Temperature
        self.labelMaxTemp = self.createLabelSmall(text="Maximum Temp (" + "\N{DEGREE SIGN}" + "F)")
        self.labelMaxTemp.setObjectName("allLabels")
        self.labelMaxTemp.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMaxTemp = QLineEdit()
        self.lineEditMaxTemp.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditMaxTemp.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditMaxTemp.setFixedHeight(30)
        self.lineEditMaxTemp.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 4)
        self.lineEditMaxTemp.setValidator(self.onlyFlaot)
        self.lineEditMaxTemp.setText("68.8")
        self.tempNONROADGridLayout.addWidget(self.labelMaxTemp, 3, 0)
        self.tempNONROADGridLayout.addWidget(self.lineEditMaxTemp, 3, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.tempNONROADGridLayout.addWidget(emptyLabelE, 4, 0, 1, 4)

        # Conversion Factors Label
        self.convFactorsLabel = QLabel()
        self.convFactorsLabel.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#conversion-factors",
                                                             "Conversion Factors"))
        self.convFactorsLabel.setOpenExternalLinks(True)
        self.convFactorsLabel.setFixedHeight(30)
        self.convFactorsLabel.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.convFactorsLabel, 21, 0, 1, 4)

        #  Conversion Factors Label Line
        self.convFactorsLabelLine = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.convFactorsLabelLine.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.convFactorsLabelLine, 22, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Conversion Factors NONROAD
        self.labelConvFactorsNONROADExpand = QPushButton()
        self.labelConvFactorsNONROADExpand.setFixedHeight(30)
        self.labelConvFactorsNONROADExpand.setFixedWidth(30)
        self.labelConvFactorsNONROADExpand.setObjectName("expandCollapseIcon")
        self.labelConvFactorsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelConvFactorsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelConvFactorsNONROADExpand, 21, 4)

        self.convFactorsNONROADexpandWidget = QtWidgets.QWidget()
        self.convFactorsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.convFactorsNONROADGridLayout = QtWidgets.QGridLayout()
        self.convFactorsNONROADexpandWidget.setLayout(self.convFactorsNONROADGridLayout)
        self.convFactorsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.convFactorsNONROADexpandWidget, 23, 0, 1, 4)

        def labelConvFactorsNONROADOnClickEvent():
            if self.convFactorsNONROADexpandWidget.isVisible():
                self.labelConvFactorsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelConvFactorsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
                self.convFactorsNONROADexpandWidget.setVisible(False)
            else:
                self.labelConvFactorsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelConvFactorsNONROADExpand.setIcon(QtGui.QIcon('minus.png'))
                self.convFactorsNONROADexpandWidget.setVisible(True)

        self.labelConvFactorsNONROADExpand.clicked.connect(labelConvFactorsNONROADOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.convFactorsNONROADGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Low Heating Value
        self.labelLowHeat = self.createLabelBig(text="Diesel Low Heating" + "\n" + " Value (mmBTU/gal)")
        self.labelLowHeat.setStyleSheet(" border: 1px solid #000000; ")
        self.labelLowHeat.setObjectName("allLabels")
        self.labelLowHeat.setToolTip("Lower heating value for diesel fuel")
        self.lineEditLowHeat = QLineEdit(self)
        self.lineEditLowHeat.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditLowHeat.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditLowHeat.setFixedHeight(40)
        self.lineEditLowHeat.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditLowHeat.setValidator(self.onlyFlaot)
        self.lineEditLowHeat.setText("0.12845")
        self.convFactorsNONROADGridLayout.addWidget(self.labelLowHeat, 1, 0)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditLowHeat, 1, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.convFactorsNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 2)

        # Created UI element Hydrocarbon to VOC Conversion Factor
        self.labelHydeo = self.createLabelBig(text="Hydrocarbon to VOC"+ "\n" + "Conversion Factor")
        self.labelHydeo.setObjectName("allLabels")
        self.labelHydeo.setStyleSheet(" border: 1px solid #000000; ")
        self.labelHydeo.setToolTip("Conversion between total hydrocarbons and VOCs (unitless)")
        self.lineEditHydro = QLineEdit()
        self.lineEditHydro.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditHydro.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditHydro.setFixedHeight(40)
        self.lineEditHydro.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditHydro.setValidator(self.onlyFlaot)
        self.lineEditHydro.setText("1.053")
        self.convFactorsNONROADGridLayout.addWidget(self.labelHydeo, 1, 3)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditHydro, 1, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.convFactorsNONROADGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element NH3 Emission Factor
        self.labelNH3 = self.createLabelBig(text="NH3 Emission Factor" + "\n" + "(g NH3/mmBTU diesel)")
        self.labelNH3.setObjectName("allLabels")
        self.labelNH3.setStyleSheet(" border: 1px solid #000000; ")
        self.labelNH3.setToolTip("NH3 emission factor for diesel fuel")
        self.lineEditNH3 = QLineEdit(self)
        self.lineEditNH3.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditNH3.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditNH3.setFixedHeight(40)
        self.lineEditNH3.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditNH3.setValidator(self.onlyFlaot)
        self.lineEditNH3.setText("0.68")
        self.convFactorsNONROADGridLayout.addWidget(self.labelNH3, 3, 0)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditNH3, 3, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.convFactorsNONROADGridLayout.addWidget(self.emptyPlainText2, 3, 2)

        # Created UI element PM10 to PM2.5 Conversion Factor
        self.labelPM10 = self.createLabelBig(text="PM10 to PM2.5"+ "\n" + "Conversion Factor")
        self.labelPM10.setObjectName("allLabels")
        self.labelPM10.setStyleSheet(" border: 1px solid #000000; ")
        self.labelPM10.setToolTip("Ratio of PM10 to PM2.5 (unitless)")
        self.lineEditPM10 = QLineEdit(self)
        self.lineEditPM10.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditPM10.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditPM10.setFixedHeight(40)
        self.lineEditPM10.setFixedWidth(125)
        self.onlyFlaot = QDoubleValidator(0.0, 9.0, 6)
        self.lineEditPM10.setValidator(self.onlyFlaot)
        self.lineEditPM10.setText("0.97")
        self.convFactorsNONROADGridLayout.addWidget(self.labelPM10, 3, 3)
        self.convFactorsNONROADGridLayout.addWidget(self.lineEditPM10, 3, 4)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.convFactorsNONROADGridLayout.addWidget(emptyLabelE, 4, 0, 1, 4)

        # Advanced Options Label
        self.advOptionsLabelN = QLabel()
        self.advOptionsLabelN.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#advanced-options-2",
                                                             "Advanced Options"))
        self.advOptionsLabelN.setOpenExternalLinks(True)
        self.advOptionsLabelN.setFixedHeight(30)
        self.advOptionsLabelN.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.advOptionsLabelN, 25, 0, 1, 4)

        #  Advanced Options Label Line
        self.labelAdvOptionsLineN = QLabel()
        pixmapLine1M = QPixmap('line.png')
        pixmap1M = pixmapLine1M.scaledToHeight(15)
        self.labelAdvOptionsLineN.setPixmap(pixmap1M)
        self.resize(pixmap1M.width(), pixmap1M.height())
        self.windowLayout.addWidget(self.labelAdvOptionsLineN, 26, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Advanced Options NONROAD
        self.labelAdvOptionsNONROADExpand = QPushButton()
        self.labelAdvOptionsNONROADExpand.setStyleSheet("QPushButton { text-align : right}")
        self.labelAdvOptionsNONROADExpand.setFixedHeight(30)
        self.labelAdvOptionsNONROADExpand.setFixedWidth(30)
        self.labelAdvOptionsNONROADExpand.setObjectName("expandCollapseIcon")
        self.labelAdvOptionsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelAdvOptionsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelAdvOptionsNONROADExpand, 25, 4)

        self.advOptionsNONROADexpandWidget = QtWidgets.QWidget()
        self.advOptionsNONROADexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.advOptionsNONROADGridLayout = QtWidgets.QGridLayout()
        self.advOptionsNONROADexpandWidget.setLayout(self.advOptionsNONROADGridLayout)
        self.advOptionsNONROADexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.advOptionsNONROADexpandWidget, 27, 0, 1, 4)

        def labelAdvOptionsNONROADOnClickEvent():
            if self.advOptionsNONROADexpandWidget.isVisible():
                self.labelAdvOptionsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelAdvOptionsNONROADExpand.setIcon(QtGui.QIcon('plus.png'))
                self.advOptionsNONROADexpandWidget.setVisible(False)
            else:
                self.labelAdvOptionsNONROADExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelAdvOptionsNONROADExpand.setIcon(QtGui.QIcon('minus.png'))
                self.advOptionsNONROADexpandWidget.setVisible(True)

        self.labelAdvOptionsNONROADExpand.clicked.connect(labelAdvOptionsNONROADOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsNONROADGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Region Nonroad Encode Names
        self.labelNonEncodeNames = self.createLabelSmall(text="Encode Names")
        self.labelNonEncodeNames.setObjectName("allLabels")
        self.labelNonEncodeNames.setStyleSheet(" border: 1px solid #000000; ")
        self.labelNonEncodeNames.setToolTip("Encode feedstock, tillage type, and activity names")
        self.comboBoxEncodeNames = QComboBox(self)
        self.comboBoxEncodeNames.setStyleSheet(" border: 1px solid #000000; ")
        self.comboBoxEncodeNames.setFixedWidth(150)
        self.comboBoxEncodeNames.setFixedHeight(30)
        self.comboBoxEncodeNames.addItem("True")
        self.comboBoxEncodeNames.addItem("False")
        self.comboBoxEncodeNames.setCurrentText("True")
        self.comboBoxEncodeNames.setEditable(True)
        self.leditEncodeName = self.comboBoxEncodeNames.lineEdit()
        self.leditEncodeName.setAlignment(QtCore.Qt.AlignCenter)
        self.leditEncodeName = self.comboBoxEncodeNames.lineEdit()
        self.leditEncodeName.setReadOnly(True)
        self.advOptionsNONROADGridLayout.addWidget(self.labelNonEncodeNames, 1, 0)
        self.advOptionsNONROADGridLayout.addWidget(self.comboBoxEncodeNames, 1, 1)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.advOptionsNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 2)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.advOptionsNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 3)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.advOptionsNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 4)

        # Add Empty PlainText - adjust horizontal space
        self.emptyPlainText2 = QLabel()
        self.emptyPlainText2.setStyleSheet("border-color: white;")
        self.emptyPlainText2.setFixedWidth(55)
        self.emptyPlainText2.setFixedHeight(30)
        self.advOptionsNONROADGridLayout.addWidget(self.emptyPlainText2, 1, 5)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.advOptionsNONROADGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 30, 0)

    # Check for consistent input for year
    def handleItemPressed(self, index):

        fieldValues = set()
        fieldNames = []

        if self.tabMoves.isEnabled():
            fieldValues.add(self.comboBoxYear.currentText())
            fieldNames.append("MOVES")

        if self.tabNonroad.isEnabled():
            fieldValues.add(self.comboBoxYearNon.currentText())
            fieldNames.append("NONROAD")

        if len(fieldValues) == 1:
            self.comboBoxYearNon.setStyleSheet("border: 1px solid black;color: black ")
            self.comboBoxYear.setStyleSheet("border: 1px solid black;color: black ")
            self.labelYearErrorMsg.setStyleSheet("border: 1px solid white;")
            self.labelYearNonErrorMsg.setStyleSheet("border: 1px solid white;")
            self.labelYearErrorMsg.setText("")
            self.labelYearNonErrorMsg.setText("")

        else:
            self.comboBoxYearNon.setStyleSheet("border: 2px solid red;color: red ")
            self.comboBoxYear.setStyleSheet("border: 2px solid red;color: red ")
            self.labelYearErrorMsg.setStyleSheet("color: red ;border: 1px solid red;")
            self.labelYearNonErrorMsg.setStyleSheet("color: red ;border: 1px solid red;")

            tabsNamesInSentence = ""
            if len(fieldNames) == 1:
                tabsNamesInSentence = fieldNames[0]
            elif len(fieldNames) > 1:
                tabsNamesInSentence = tabsNamesInSentence.join(fieldNames[0]) + " and " + fieldNames[1]
            message = "Values for Analysis Year should be same for tabs: " + tabsNamesInSentence
            self.labelYearErrorMsg.setText(message)
            self.labelYearNonErrorMsg.setText(message)

    # Functions used for Moves Datafiles

    def getfilesDatafilesNon(self):
        fileName = QFileDialog.getExistingDirectory(self, "Browse")
        if fileName != "":
            selectedFileName = str(fileName).split(',')
            self.lineEditDatafilesNon.setText(selectedFileName[0])

    def getfilesNonExePath(self):
        fileName = QFileDialog.getExistingDirectory(self, "Browse")
        if fileName != "":
            selectedFileName = str(fileName).split(',')
            self.lineEditNonExePath.setText(selectedFileName[0])

    # Functions used for Fips Nonroad

    def getfilesFipsNon(self):
        fileNameFipsNon = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameFipsNon[0] != "":
            selectedFileNameFipsNon = fileNameFipsNon[0].split("FPEAM/")
            self.lineEditFipsNon.setText(selectedFileNameFipsNon[1])

    # Functions used for Nonroad Irrigation

    def getfilesNonIrrig(self):
        fileNameNonEq = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameNonEq[0] != "":
            selectedFileNameNonEq = fileNameNonEq[0].split("FPEAM/")
            self.lineEditNonIrrig.setText(selectedFileNameNonEq[1])

    # Functions used for Nonroad equipment

    def getfilesNonEquip(self):
        fileNameNonEquip = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameNonEquip[0] != "":
            selectedFileNameNonEquip = fileNameNonEquip[0].split("FPEAM/")
            self.lineEditNonEquip.setText(selectedFileNameNonEquip[1])

    ###########################################################################################################################################################

    #####    EmissionFactors Module   ######

    def setupUIEmissionFactors(self):
        # Emission Factors tab created
        self.tabEmissionFactors = QtWidgets.QWidget()
        self.tabEmissionFactors.resize(WIDTH, HEIGHT - 200)
        # Emission Factors tab added
        self.centralwidget.addTab(self.tabEmissionFactors, self.getSpacedNames("Emission Factors"))

        # Emission Factors code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        self.scrollAreaEF = QScrollArea(self.tabEmissionFactors)
        self.scrollAreaEF.setWidgetResizable(True)
        self.scrollAreaEF.resize(WIDTH, HEIGHT)
        self.scrollAreaEF.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaEF.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetEF = QtWidgets.QWidget()
        self.innerWidgetEF.resize(WIDTH, HEIGHT)
        self.scrollAreaEF.setWidget(self.innerWidgetEF)
        self.innerWidgetEF.setLayout(self.windowLayout)

        # Empty label
        emptyLabelTop = QLabel()
        emptyLabelTop.setFixedHeight(30)
        self.windowLayout.addWidget(emptyLabelTop, 0, 0, 1, 5)

        # link to readme in upper left corner
        self.emfactorhelplink = QLabel()
        self.emfactorhelplink.setText(self.createLink("https://github.com/NREL/fpeam/tree/master#emission-factors",
                                                      "Readme"))
        self.emfactorhelplink.setOpenExternalLinks(True)
        self.emfactorhelplink.setFixedHeight(30)
        self.windowLayout.addWidget(self.emfactorhelplink, 1, 0, 1, 4)

        # Created UI element Feedstock Measure Type Emission Factors
        self.labelFeedMeasureTypeEF = self.createLabelBig(text="Feedstock Measure" + "\n" + " Type")
        self.labelFeedMeasureTypeEF.setObjectName("allLabels")
        self.labelFeedMeasureTypeEF.setToolTip("Production table feedstock identifier")
        self.lineEditFeedMeasureTypeEF = QLineEdit()
        self.lineEditFeedMeasureTypeEF.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditFeedMeasureTypeEF.setFixedWidth(116)
        self.lineEditFeedMeasureTypeEF.setFixedHeight(40)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditFeedMeasureTypeEF.setValidator(validator)
        self.lineEditFeedMeasureTypeEF.setText("harvested")
        self.windowLayout.addWidget(self.labelFeedMeasureTypeEF, 2, 0)
        self.windowLayout.addWidget(self.lineEditFeedMeasureTypeEF, 2, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(20)
        self.windowLayout.addWidget(emptyLabelE, 3, 0, 1, 5)

        # Custom Data Filepaths Label EF
        self.customDataFilepathLabelEF = QLabel()
        self.customDataFilepathLabelEF.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#custom-data-filepaths-3",
                                                                      "Custom Data Filepaths"))
        self.customDataFilepathLabelEF.setOpenExternalLinks(True)
        self.customDataFilepathLabelEF.setFixedHeight(30)
        self.customDataFilepathLabelEF.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.customDataFilepathLabelEF, 4, 0, 1, 4)

        # Created UI element - Custom Dtatfiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('line.png')
        pixmap1 = pixmapLine1.scaledToHeight(15)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 5, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Dtatfiles EF
        self.labelcustomDatafileEFExpand = QPushButton()
        self.labelcustomDatafileEFExpand.setFixedHeight(30)
        self.labelcustomDatafileEFExpand.setFixedWidth(30)
        self.labelcustomDatafileEFExpand.setObjectName("expandCollapseIcon")
        self.labelcustomDatafileEFExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelcustomDatafileEFExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelcustomDatafileEFExpand, 4, 4)

        self.customDatafileEFexpandWidget = QtWidgets.QWidget()
        self.customDatafileEFexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.customDatafileEFGridLayout = QtWidgets.QGridLayout()
        self.customDatafileEFexpandWidget.setLayout(self.customDatafileEFGridLayout)
        self.customDatafileEFexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileEFexpandWidget, 6, 0, 1, 4)

        def labelCustomDatafileEFOnClickEvent():
            if self.customDatafileEFexpandWidget.isVisible():
                self.labelcustomDatafileEFExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelcustomDatafileEFExpand.setIcon(QtGui.QIcon('plus.png'))
                self.customDatafileEFexpandWidget.setVisible(False)
            else:
                self.labelcustomDatafileEFExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelcustomDatafileEFExpand.setIcon(QtGui.QIcon('minus.png'))
                self.customDatafileEFexpandWidget.setVisible(True)

        self.labelcustomDatafileEFExpand.clicked.connect(labelCustomDatafileEFOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileEFGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Emission Factors
        self.labelEmiFact = QLabel()
        self.labelEmiFact.setObjectName("allLabels")
        self.labelEmiFact.setStyleSheet(" border: 1px solid #000000; ")
        self.labelEmiFact.setFixedHeight(30)
        self.labelEmiFact.setFixedWidth(160)
        self.labelEmiFact.setAlignment(QtCore.Qt.AlignCenter)
        self.labelEmiFact.setText("Emission Factors")
        self.labelEmiFact.setToolTip("Emission factors as lb pollutant per lb resource subtype")
        self.browseBtnEmiFact = self.createButton(text="Browse")
        self.browseBtnEmiFact.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnEmiFact.clicked.connect(self.getfilesEmiFact)
        self.lineEditEmiFact = QLineEdit(self)
        self.lineEditEmiFact.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditEmiFact.setText("data/inputs/emission_factors.csv")
        self.lineEditEmiFact.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditEmiFact.setFixedHeight(30)
        self.customDatafileEFGridLayout.addWidget(self.labelEmiFact, 1, 0)
        self.customDatafileEFGridLayout.addWidget(self.browseBtnEmiFact, 1, 1)
        self.customDatafileEFGridLayout.addWidget(self.lineEditEmiFact, 1, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileEFGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element Resource Distribution
        self.labelResDist = self.createLabelSmall(text="Resource Distribution")
        self.labelResDist.setObjectName("allLabels")
        self.labelResDist.setStyleSheet(" border: 1px solid #000000; ")
        self.labelResDist.setToolTip("Resource subtype distribution for all resources")
        self.browseBtnReDist = self.createButton(text="Browse")
        self.browseBtnReDist.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnReDist.clicked.connect(self.getfilesResDist)
        self.lineEditResDist = QLineEdit(self)
        self.lineEditResDist.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditResDist.setText("data/inputs/resource_distribution.csv")
        self.lineEditResDist.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditResDist.setFixedHeight(30)
        self.customDatafileEFGridLayout.addWidget(self.labelResDist, 3, 0)
        self.customDatafileEFGridLayout.addWidget(self.browseBtnReDist, 3, 1)
        self.customDatafileEFGridLayout.addWidget(self.lineEditResDist, 3, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileEFGridLayout.addWidget(emptyLabelE, 4, 0, 1, 4)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 8, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 9, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 10, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 11, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 12, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 13, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 14, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 15, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 16, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 17, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 18, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 19, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 20, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 21, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 22, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 23, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 30, 0)

    # Functions used for Emission Factors

    def getfilesEmiFact(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTruckCapa[0] != "":
            selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
            self.lineEditEmiFact.setText(selectedFileNameTruckCapa[1])

    # Functions used for Resource Distribution

    def getfilesResDist(self):
        fileNameTruckCapa = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameTruckCapa[0] != "":
            selectedFileNameTruckCapa = fileNameTruckCapa[0].split("FPEAM/")
            self.lineEditResDist.setText(selectedFileNameTruckCapa[1])

    ###################################################################################################################################################################

    #####    Fugitive Dust  Module   ######

    def setupUIFugitiveDust(self):
        # Fugitive Dust tab created
        self.tabFugitiveDust = QtWidgets.QWidget()
        self.tabFugitiveDust.resize(WIDTH, HEIGHT - 200)
        # Fugitive Dust tab added
        self.centralwidget.addTab(self.tabFugitiveDust, self.getSpacedNames("Fugitive Dust"))

        # Fugitive Dust code start
        self.windowLayout = QGridLayout()
        self.windowLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.windowLayout.setColumnStretch(6, 1)

        self.scrollAreaFD = QScrollArea(self.tabFugitiveDust)
        self.scrollAreaFD.setWidgetResizable(True)
        self.scrollAreaFD.resize(WIDTH, HEIGHT)
        self.scrollAreaFD.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaFD.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.innerWidgetFD = QtWidgets.QWidget()
        self.innerWidgetFD.resize(WIDTH, HEIGHT)
        self.scrollAreaFD.setWidget(self.innerWidgetFD)
        self.innerWidgetFD.setLayout(self.windowLayout)

        # Empty label
        emptyLabelTop = QLabel()
        emptyLabelTop.setFixedHeight(30)
        self.windowLayout.addWidget(emptyLabelTop, 0, 0, 1, 5)

        # link to readme section
        self.fugdusthelplink = QLabel()
        self.fugdusthelplink.setText(self.createLink("https://github.com/NREL/fpeam/tree/master#fugitive-dust",
                                                     "Readme"))
        self.fugdusthelplink.setOpenExternalLinks(True)
        self.fugdusthelplink.setFixedHeight(30)
        self.windowLayout.addWidget(self.fugdusthelplink, 1, 0, 1, 4)

        # Created UI element on-farm Feedstock Measure Type - Fugitive Dust
        self.labelOnfarmFeedMeasureTypeFD = self.createLabelBig(text="On-Farm Feedstock" + "\n" + "Measure Type")
        self.labelOnfarmFeedMeasureTypeFD.setObjectName("allLabels")
        self.labelOnfarmFeedMeasureTypeFD.setToolTip("Enter feedstock measure type used in on-farm fugitive dust calculations")
        self.lineEditOnfarmFeedMeasureTypeFD = QLineEdit(self)
        self.lineEditOnfarmFeedMeasureTypeFD.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditOnfarmFeedMeasureTypeFD.setFixedWidth(116)
        self.lineEditOnfarmFeedMeasureTypeFD.setFixedHeight(40)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditOnfarmFeedMeasureTypeFD.setValidator(validator)
        self.lineEditOnfarmFeedMeasureTypeFD.setText("harvested")
        self.windowLayout.addWidget(self.labelOnfarmFeedMeasureTypeFD, 2, 0)
        self.windowLayout.addWidget(self.lineEditOnfarmFeedMeasureTypeFD, 2, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(20)
        self.windowLayout.addWidget(emptyLabelE, 3, 0, 1, 5)

        # Created UI element on-road Feedstock Measure Type - Fugitive Dust
        self.labelOnroadFeedMeasureTypeFD = self.createLabelBig(text="On-Road Feedstock" + "\n" + "Measure Type")
        self.labelOnroadFeedMeasureTypeFD.setObjectName("allLabels")
        self.labelOnroadFeedMeasureTypeFD.setToolTip("Enter feedstock measure type used in on-road fugitive dust calculations")
        self.lineEditOnroadFeedMeasureTypeFD = QLineEdit(self)
        self.lineEditOnroadFeedMeasureTypeFD.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEditOnroadFeedMeasureTypeFD.setFixedWidth(116)
        self.lineEditOnroadFeedMeasureTypeFD.setFixedHeight(40)
        regex = QtCore.QRegExp("[a-z-A-Z_]+")
        validator = QtGui.QRegExpValidator(regex)
        self.lineEditOnroadFeedMeasureTypeFD.setValidator(validator)
        self.lineEditOnroadFeedMeasureTypeFD.setText("production")
        self.windowLayout.addWidget(self.labelOnroadFeedMeasureTypeFD, 4, 0)
        self.windowLayout.addWidget(self.lineEditOnroadFeedMeasureTypeFD, 4, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(20)
        self.windowLayout.addWidget(emptyLabelE, 5, 0, 1, 5)

        # Custom Data Filepaths Label FD
        self.customDataFilepathLabelFD = QLabel()
        self.customDataFilepathLabelFD.setText(self.createHeadingLink("https://github.com/NREL/fpeam/tree/master#custom-data-filepaths-4",
                                                                      "Custom Data Filepaths"))
        self.customDataFilepathLabelFD.setOpenExternalLinks(True)
        self.customDataFilepathLabelFD.setFixedHeight(30)
        self.customDataFilepathLabelFD.setObjectName("subTitleLabels")
        self.windowLayout.addWidget(self.customDataFilepathLabelFD, 6, 0, 1, 4)

        # Created UI element - Custom Datafiles below Line
        self.labelCustomDatafilsLine = QLabel()
        pixmapLine1 = QPixmap('line.png')
        pixmap1 = pixmapLine1.scaledToHeight(15)
        self.labelCustomDatafilsLine.setPixmap(pixmap1)
        self.resize(pixmap1.width(), pixmap1.height())
        self.windowLayout.addWidget(self.labelCustomDatafilsLine, 7, 0, 1, 5)

        # Expand/Collapse code
        # Created UI element Custom Datafiles FD
        self.labelcustomDatafileFDExpand = QPushButton()
        self.labelcustomDatafileFDExpand.setFixedHeight(30)
        self.labelcustomDatafileFDExpand.setFixedWidth(30)
        self.labelcustomDatafileFDExpand.setObjectName("expandCollapseIcon")
        self.labelcustomDatafileFDExpand.setIconSize(QtCore.QSize(28, 28))
        self.labelcustomDatafileFDExpand.setIcon(QtGui.QIcon('plus.png'))
        self.windowLayout.addWidget(self.labelcustomDatafileFDExpand, 6, 4)

        self.customDatafileFDexpandWidget = QtWidgets.QWidget()
        self.customDatafileFDexpandWidget.setStyleSheet(
            "border-color: #028ACC; border-style: outset; border-width: 3px;border-radius: 5px;")
        self.customDatafileFDGridLayout = QtWidgets.QGridLayout()
        self.customDatafileFDexpandWidget.setLayout(self.customDatafileFDGridLayout)
        self.customDatafileFDexpandWidget.setVisible(False)
        self.windowLayout.addWidget(self.customDatafileFDexpandWidget, 8, 0, 1, 4)

        def labelCustomDatafileFDOnClickEvent():
            if self.customDatafileFDexpandWidget.isVisible():
                self.labelcustomDatafileFDExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelcustomDatafileFDExpand.setIcon(QtGui.QIcon('plus.png'))
                self.customDatafileFDexpandWidget.setVisible(False)
            else:
                self.labelcustomDatafileFDExpand.setIconSize(QtCore.QSize(28, 28))
                self.labelcustomDatafileFDExpand.setIcon(QtGui.QIcon('minus.png'))
                self.customDatafileFDexpandWidget.setVisible(True)

        self.labelcustomDatafileFDExpand.clicked.connect(labelCustomDatafileFDOnClickEvent)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFDGridLayout.addWidget(emptyLabelE, 0, 0, 1, 4)

        # Created UI element Emission Factors - Fugitive Dust
        self.labelEmiFactFD = self.createLabelSmall(text="On-Farm Factors")
        self.labelEmiFactFD.setObjectName("allLabels")
        self.labelEmiFactFD.setStyleSheet(" border: 1px solid #000000; ")
        self.labelEmiFactFD.setToolTip("Select dataset of PM10 and PM2.5 emission rates by acre")
        self.browseBtnEmiFactFD = self.createButton(text="Browse")
        self.browseBtnEmiFactFD.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnEmiFactFD.clicked.connect(self.getfilesEmiFactFD)
        self.lineEditEmiFactFD = QLineEdit(self)
        self.lineEditEmiFactFD.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditEmiFactFD.setText("data/inputs/fugitive_dust_emission_factors.csv")
        self.lineEditEmiFactFD.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditEmiFactFD.setFixedHeight(30)
        self.customDatafileFDGridLayout.addWidget(self.labelEmiFactFD, 1, 0)
        self.customDatafileFDGridLayout.addWidget(self.browseBtnEmiFactFD, 1, 1)
        self.customDatafileFDGridLayout.addWidget(self.lineEditEmiFactFD, 1, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFDGridLayout.addWidget(emptyLabelE, 2, 0, 1, 4)

        # Created UI element onroad constants - Fugitive Dust
        self.labelOnrConst = self.createLabelSmall(text="On-Road Constants")
        self.labelOnrConst.setObjectName("allLabels")
        self.labelOnrConst.setStyleSheet(" border: 1px solid #000000; ")
        self.labelOnrConst.setToolTip("Select dataset of constants for calculating on-road PM10 and PM2.5")
        self.browseBtnOnrConst = self.createButton(text="Browse")
        self.browseBtnOnrConst.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnOnrConst.clicked.connect(self.getfilesOnrConst)
        self.lineEditOnrConst = QLineEdit(self)
        self.lineEditOnrConst.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditOnrConst.setText("data/inputs/fugitive_dust_onroad_constants.csv")
        self.lineEditOnrConst.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditOnrConst.setFixedHeight(30)
        self.customDatafileFDGridLayout.addWidget(self.labelOnrConst, 3, 0)
        self.customDatafileFDGridLayout.addWidget(self.browseBtnOnrConst, 3, 1)
        self.customDatafileFDGridLayout.addWidget(self.lineEditOnrConst, 3, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFDGridLayout.addWidget(emptyLabelE, 4, 0, 1, 4)

        # Created UI element silt content
        self.labelSiltCont = self.createLabelSmall(text="Road Silt Content")
        self.labelSiltCont.setObjectName("allLabels")
        self.labelSiltCont.setStyleSheet(" border: 1px solid #000000; ")
        self.labelSiltCont.setToolTip("Select dataset of on-road silt content by state")
        self.browseBtnSiltCont = self.createButton(text="Browse")
        self.browseBtnSiltCont.setStyleSheet(" border: 1px solid #000000; ")
        self.browseBtnSiltCont.clicked.connect(self.getfilesSiltCont)
        self.lineEditSiltCont = QLineEdit(self)
        self.lineEditSiltCont.setStyleSheet(" border: 1px solid #000000; ")
        self.lineEditSiltCont.setText("data/inputs/fugitive_dust_silt_content.csv")
        self.lineEditSiltCont.setAlignment(QtCore.Qt.AlignLeft)
        self.lineEditSiltCont.setFixedHeight(30)
        self.customDatafileFDGridLayout.addWidget(self.labelSiltCont, 5, 0)
        self.customDatafileFDGridLayout.addWidget(self.browseBtnSiltCont, 5, 1)
        self.customDatafileFDGridLayout.addWidget(self.lineEditSiltCont, 5, 2, 1, 3)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(10)
        emptyLabelE.setStyleSheet("border: white")
        self.customDatafileFDGridLayout.addWidget(emptyLabelE, 6, 0, 1, 4)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 11, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 12, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 13, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 14, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 15, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 16, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 17, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 18, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 19, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 20, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 21, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 22, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 23, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 24, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 25, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 26, 0)

        # Add Empty PlainText
        self.emptyPlainText2 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText2, 27, 0)

        # Add Empty PlainText
        self.emptyPlainText = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText, 28, 0)

        # Add Empty PlainText
        self.emptyPlainText1 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText1, 29, 0)

        # Add Empty PlainText
        self.emptyPlainText3 = QLabel()
        self.windowLayout.addWidget(self.emptyPlainText3, 30, 0)

    # Functions used for Fugitive Dust - EMission factor
    def getfilesEmiFactFD(self):
        fileNameEmiFactFD = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameEmiFactFD[0] != "":
            selectedFileNameEmiFactFD = fileNameEmiFactFD[0].split("FPEAM/")
            self.lineEditEmiFactFD.setText(selectedFileNameEmiFactFD[1])

    # Functions used for onroad constants for Fugitive Dust
    def getfilesOnrConst(self):
        fileNameOnrConst = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameOnrConst[0] != "":
            selectedFileNameOnrConst = fileNameOnrConst[0].split("FPEAM/")
            self.lineEditOnrConst.setText(selectedFileNameOnrConst[1])

    # Functions used for fugitive dust silt content
    def getfilesSiltCont(self):
        fileNameSiltCont = QFileDialog.getOpenFileName(self, 'Browse', "", "CSV files (*.csv)")
        if fileNameSiltCont[0] != "":
            selectedFileNameSiltCont = fileNameSiltCont[0].split("FPEAM/")
            self.lineEditSiltCont.setText(selectedFileNameSiltCont[1])

    # Reset Button Code
    def resetFields(self):

        self.lineEditScenaName.setStyleSheet("border: 2px solid black;")
        self.lineEditProjectPath.setStyleSheet("border: 2px solid black;")

        self.plainTextLog.setPlainText("")

        # FPEAM home page - Attribute Initialization
        self.lineEditScenaName.setText("")
        self.lineEditProjectPath.setText("")
        self.checkBoxMoves.setChecked(True)
        self.checkBoxNonroad.setChecked(True)
        self.checkBoxEmissionFactors.setChecked(True)
        self.checkBoxFugitiveDust.setChecked(True)
        self.index = self.comboBoxVerbosityLevel.findText("DEBUG")
        self.comboBoxVerbosityLevel.setCurrentIndex(self.index)
        self.lineEditEq.setText("data/equipment/bts16_equipment.csv")
        self.lineEditProd.setText("data/production/production_2017_bc1060.csv")
        self.lineEditFedLossFact.setText("data/inputs/feedstock_loss_factors.csv")
        self.lineEditTransGraph.setText("data/inputs/transportation_graph.csv")
        self.lineEditNodeLocs.setText("data/inputs/node_locations.csv")
        self.index = self.comboBoxBF.findText("Yes")
        self.comboBoxBF.setCurrentIndex(self.index)
        self.index = self.comboBoxRE.findText("Yes")
        self.comboBoxRE.setCurrentIndex(self.index)
        self.lineEditVMTperTruck.setText("20")

        # Fugitive Dust module - Attribute Initialization
        self.lineEditOnfarmFeedMeasureTypeFD.setText("harvested")
        self.lineEditOnroadFeedMeasureTypeFD.setText("production")
        self.lineEditEmiFactFD.setText("../data/inputs/fugitive_dust_emission_factors.csv")
        self.lineEditOnrConst.setText("../data/inputs/fugitive_dust_onroad_constants.csv")
        self.lineEditSiltCont.setText("../data/inputs/fugitive_dust_silt_content.csv")

        # Emission Factors Module - Attribute Initialization
        self.lineEditFeedMeasureTypeEF.setText("harvested")
        self.lineEditEmiFact.setText('data/inputs/emission_factors.csv')
        self.lineEditResDist.setText('data/inputs/resource_distribution.csv')

        # Nonroad Module - Attribute Initialization
        self.index = self.comboBoxYearNon.findText("2017")
        self.comboBoxYearNon.setCurrentIndex(self.index)
        self.lineEditDbHostN.setText("localhost")
        self.lineEditDbUsernameN.setText("root")
        self.lineEditDbNameN.setText("movesdb20180517")
        self.lineEditDbPwdN.setText("root")
        self.lineEditFeedMeasureTypeNon.setText("harvested")
        self.lineEditTimeResNamesNon.setText("time")
        self.lineEditForestryNamesNon.setText("'forest whole tree', 'forest residues'")
        self.lineEditFipsNon.setText("../data/inputs/region_fips_map.csv")
        self.lineEditDatafilesNon.setText("C:/Nonroad")
        self.lineEditNonExePath.setText("C:/MOVES2014b/NONROAD/NR08a")
        self.lineEditMinTemp.setText("50.0")
        self.lineEditMaxTemp.setText("68.8")
        self.lineEditMeanTemp.setText("60.0")
        self.lineEditLowHeat.setText("0.12845")
        self.lineEditNH3.setText("0.68")
        self.lineEditHydro.setText("1.053")
        self.lineEditPM10.setText("0.97")
        self.lineEditFeedMeasureTypeIrrigNon.setText("planted")
        self.lineEditFeedIrrigNamesNon.setText("corn grain")
        self.lineEditNonIrrig.setText("../data/inputs/irrigation.csv")
        self.lineEditNonEquip.setText("../data/inputs/nonroad_equipment.csv")
        self.comboBoxEncodeNames.setCurrentText("True")

        # Moves Module - Attribute Initialization
        self.index = self.comboBoxAggLevel.findText("By State")
        self.comboBoxAggLevel.setCurrentIndex(self.index)
        self.index = self.comboBoxCachedResUse.findText("True")
        self.comboBoxCachedResUse.setCurrentIndex(self.index)
        self.lineEditFeedMeasureType.setText("production")
        self.spinBoxNoofTruck.setValue(1)
        self.leditHPMSVtypeId.setValue(60)
        self.leditSourceTypeId.setValue(61)
        self.index = self.comboBoxYear.findText("2017")
        self.comboBoxYear.setCurrentIndex(self.index)
        self.lineEditDbHost.setText("localhost")
        self.lineEditDbUsername.setText("root")
        self.lineEditDbName.setText("movesdb20180517")
        self.lineEditDbPwd.setText("root")
        self.lineEditOutDb.setText('moves_output_db')
        self.lineEditDatafiles.setText("C:/MOVESdata")
        self.lineEditMovesPath.setText("C:/MOVES2014b")
        self.lineEditMysqlBin.setText("C:/Program Files/MySQL/MySQL Server 5.7/bin/mysql.exe")
        self.lineEditMysqlDumpBin.setText("C:/Program Files/MySQL/MySQL Server 5.7/bin/mysqldump.exe")
        self.lineEditTruckCapa.setText("../data/inputs/truck_capacity.csv")
        self.lineEditAVFT.setText("../data/inputs/avft.csv")
        self.lineEditFips.setText("../data/inputs/region_fips_map.csv")
        self.lineEditRuralRes.setText("0.30")
        self.lineEditRuralUnres.setText("0.28")
        self.lineEditUrbanRes.setText("0.21")
        self.lineEditUrbanUnres.setText("0.21")
        self.index = self.comboBoxMonth.findText("10")
        self.comboBoxMonth.setCurrentIndex(self.index)
        self.index = self.comboBoxBegHr.findText("7")
        self.comboBoxBegHr.setCurrentIndex(self.index)
        self.index = self.comboBoxEndHr.findText("18")
        self.comboBoxEndHr.setCurrentIndex(self.index)
        self.index = self.comboBoxDayType.findText("Weekday")
        self.comboBoxDayType.setCurrentIndex(self.index)

    ###################################################################

    # Run Button Code
    def runTheSelectedModules(self):

        self.attributeValueObj = AttributeValueStorage()

        tmpFolder = tempfile.mkdtemp()

        # check if scenario name and project path is entered or not
        if self.lineEditScenaName.text() == "" or self.lineEditProjectPath.text() == "":
            if self.lineEditScenaName.text() == "" and self.lineEditProjectPath.text() != "":
                self.lineEditScenaName.setStyleSheet("border: 2px solid red;")
                self.lineEditProjectPath.setStyleSheet("border: 2px solid black;")
            if self.lineEditProjectPath.text() == "" and self.lineEditScenaName.text() != "":
                self.lineEditScenaName.setStyleSheet("border: 2px solid black;")
                self.lineEditProjectPath.setStyleSheet("border: 2px solid red;")
            if self.lineEditScenaName.text() == "" and self.lineEditProjectPath.text() == "":
                self.lineEditProjectPath.setStyleSheet("border: 2px solid red;")
                self.lineEditScenaName.setStyleSheet("border: 2px solid red;")

            return
        else:

            # FPEAM Home Page attributes value initialization

            self.attributeValueObj.scenarioName = self.lineEditScenaName.text().strip()
            self.attributeValueObj.projectPath = self.lineEditProjectPath.text().strip()

            # Check which module is selected
            selected_module_string = ""
            if self.checkBoxMoves.isChecked():
                selected_module_string += "'" + "MOVES" + "'"
                self.attributeValueObj.module = selected_module_string
                selected_module_string += ", "
            if self.checkBoxNonroad.isChecked():
                selected_module_string += "'" + "NONROAD" + "'"
                self.attributeValueObj.module = selected_module_string
                selected_module_string += ", "
            if self.checkBoxEmissionFactors.isChecked():
                selected_module_string += "'" + "emissionfactors" + "'"
                self.attributeValueObj.module = selected_module_string
                selected_module_string += ", "
            if self.checkBoxFugitiveDust.isChecked():
                selected_module_string += "'" + "fugitivedust" + "'"
                self.attributeValueObj.module = selected_module_string

            changedVerboLoggerLevel = self.comboBoxVerbosityLevel.currentText()
            if changedVerboLoggerLevel:
                self.attributeValueObj.loggerLevel = changedVerboLoggerLevel

            changedBackfill = self.comboBoxBF.currentText()
            if changedBackfill:
                if changedBackfill == "No":
                    changedBackfill = False
                else:
                    changedBackfill = True
                self.attributeValueObj.backfill = changedBackfill

            changedRouterEngine = self.comboBoxRE.currentText()
            if changedRouterEngine:
                if changedRouterEngine == "No":
                    changedRouterEngine = False
                else:
                    changedRouterEngine = True
                self.attributeValueObj.useRouterEngine = changedRouterEngine

            changedForestryFeedNames = self.lineEditForestryNamesNon.text().strip()
            if changedForestryFeedNames:
                self.attributeValueObj.forestryFeedstockNames = changedForestryFeedNames

            changedVMTPerTruck = self.lineEditVMTperTruck.text().strip()
            if changedVMTPerTruck:
                self.attributeValueObj.vMTPerTruck = changedVMTPerTruck

            changedEqPath = self.lineEditEq.text().strip()
            if changedEqPath:
                self.attributeValueObj.equipment = changedEqPath

            changedProdPath = self.lineEditProd.text().strip()
            if changedProdPath:
                self.attributeValueObj.production = changedProdPath

            changedFeedLossFactPath = self.lineEditFedLossFact.text().strip()
            if changedFeedLossFactPath:
                self.attributeValueObj.feedstockLossFactors = changedFeedLossFactPath

            changedTranGraphPath = self.lineEditTransGraph.text().strip()
            if changedTranGraphPath:
                self.attributeValueObj.transportationGraph = changedTranGraphPath

            changedNodeLocsPath = self.lineEditNodeLocs.text().strip()
            if changedNodeLocsPath:
                self.attributeValueObj.nodeLocations = changedNodeLocsPath

            changedTruckCapacityPath = self.lineEditTruckCapa.text().strip()
            if changedTruckCapacityPath:
                self.attributeValueObj.truckCapacity = changedTruckCapacityPath

            ###############################################################################################################

            # Moves attributes value initialization
            changedAggLevel = self.comboBoxAggLevel.currentText()
            # reformat the aggregation level input into two Booleans
            if changedAggLevel == 'By State':
                self.attributeValueObj.aggregation_level_state = True
                self.attributeValueObj.aggregation_level_state_feedstock = False
            elif changedAggLevel == 'By State-Feedstock':
                self.attributeValueObj.aggregation_level_state = False
                self.attributeValueObj.aggregation_level_state_feedstock = True
            else:
                self.attributeValueObj.aggregation_level_state = False
                self.attributeValueObj.aggregation_level_state_feedstock = False

            changedcachedResults = self.comboBoxCachedResUse.currentText()
            if changedcachedResults:
                self.attributeValueObj.cachedResults = changedcachedResults

            changedFeedstockMeasureTypeMoves = self.lineEditFeedMeasureType.text().strip()
            if changedFeedstockMeasureTypeMoves:
                self.attributeValueObj.feedstockMeasureTypeMoves = changedFeedstockMeasureTypeMoves

            changedNoOfTrucksUsed = self.spinBoxNoofTruck.text()
            if changedNoOfTrucksUsed:
                self.attributeValueObj.noOfTrucksUsed = changedNoOfTrucksUsed

            changedHPMSVTypeId = self.leditHPMSVtypeId.text()
            if changedHPMSVTypeId:
                self.attributeValueObj.hpmsvTypeId = changedHPMSVTypeId

            changedSourceTypeId = self.leditSourceTypeId.text()
            if changedSourceTypeId:
                self.attributeValueObj.sourceTypeId = changedSourceTypeId

            changedYearMoves = self.comboBoxYear.currentText()
            if changedYearMoves:
                self.attributeValueObj.yearMoves = changedYearMoves

            changedMonth = self.comboBoxMonth.currentText()
            if changedMonth:
                self.attributeValueObj.month = changedMonth

            changedDbHost = self.lineEditDbHost.text().strip()
            if changedDbHost:
                self.attributeValueObj.dbHost = changedDbHost

            changedDbUsername = self.lineEditDbUsername.text().strip()
            if changedDbUsername:
                self.attributeValueObj.dbUsername = changedDbUsername

            changedDbName = self.lineEditDbName.text().strip()
            if changedDbName:
                self.attributeValueObj.dbName = changedDbName

            changedDbPwd = self.lineEditDbPwd.text().strip()
            if changedDbPwd:
                self.attributeValueObj.dbPwd = changedDbPwd

            changedOutDb = self.lineEditOutDb.text().strip()
            if changedOutDb:
                self.attributeValueObj.outDb = changedOutDb

            changedBegHr = self.comboBoxBegHr.currentText()
            if changedBegHr:
                self.attributeValueObj.beginningHr = changedBegHr

            changedEndHr = self.comboBoxEndHr.currentText()
            if changedEndHr:
                self.attributeValueObj.endingHr = changedEndHr

            if self.comboBoxDayType.currentText() == "Weekday":
                self.attributeValueObj.dayType = "5"
            else:
                self.attributeValueObj.dayType = "2"

            changedAvftPath = self.lineEditAVFT.text().strip()
            if changedAvftPath:
                self.attributeValueObj.avft = changedAvftPath

            changedFipsMapNovesPath = self.lineEditFips.text().strip()
            if changedFipsMapNovesPath:
                self.attributeValueObj.regionFipsMapMoves = changedFipsMapNovesPath

            changedDatafilesMovesPath = self.lineEditDatafiles.text().strip()
            if changedDatafilesMovesPath:
                self.attributeValueObj.movesDatafilesPath = changedDatafilesMovesPath

            changedMysqlBinPath = self.lineEditMysqlBin.text().strip()
            if changedMysqlBinPath:
                self.attributeValueObj.mysqlBinPath = changedMysqlBinPath

            changedMysqlDumpBinPath = self.lineEditMysqlDumpBin.text().strip()
            if changedMysqlDumpBinPath:
                self.attributeValueObj.mysqlDumpBinPath = changedMysqlDumpBinPath

            changedRuralRes = self.lineEditRuralRes.text().strip()
            if changedRuralRes:
                self.attributeValueObj.ruralRestricted = changedRuralRes

            changedRuralUnres = self.lineEditRuralUnres.text().strip()
            if changedRuralUnres:
                self.attributeValueObj.ruralUnrestricted = changedRuralUnres

            changedUrbanRes = self.lineEditUrbanRes.text().strip()
            if changedUrbanRes:
                self.attributeValueObj.urbanRestricted = changedUrbanRes

            changedUrbanUnres = self.lineEditUrbanUnres.text().strip()
            if changedUrbanUnres:
                self.attributeValueObj.urbanUnrestricted = changedUrbanUnres

            ###############################################################################################################

            # Nonroad attributes value initialization

            changedYearNonroad = self.comboBoxYearNon.currentText()
            if changedYearNonroad:
                self.attributeValueObj.yearNonroad = changedYearNonroad

            changedFipsMapNon = self.lineEditFipsNon.text().strip()
            if changedFipsMapNon:
                self.attributeValueObj.regionFipsMapNonroad = changedFipsMapNon

            changedDbHostN = self.lineEditDbHostN.text().strip()
            if changedDbHostN:
                self.attributeValueObj.dbHostN = changedDbHostN

            changedDbUsernameN = self.lineEditDbUsernameN.text().strip()
            if changedDbUsernameN:
                self.attributeValueObj.dbUsernameN = changedDbUsernameN

            changedDbNameN = self.lineEditDbNameN.text().strip()
            if changedDbNameN:
                self.attributeValueObj.dbNameN = changedDbNameN

            changedDbPwdN = self.lineEditDbPwdN.text().strip()
            if changedDbPwdN:
                self.attributeValueObj.dbPwdN = changedDbPwdN

            changedDatafilesNon = self.lineEditDatafilesNon.text().strip()
            if changedDatafilesNon:
                self.attributeValueObj.nonroadDatafilesPath = changedDatafilesNon

            changedNonExePath = self.lineEditNonExePath.text().strip()
            if changedNonExePath:
                self.attributeValueObj.nonroadExePath = changedNonExePath

            changedIrrigNon = self.lineEditNonIrrig.text().strip()
            if changedIrrigNon:
                self.attributeValueObj.irrigation = changedIrrigNon

            changedNonEquip = self.lineEditNonEquip.text().strip()
            if changedNonEquip:
                self.attributeValueObj.nonroad_equipment = changedNonEquip

            changedEncodeName = self.comboBoxEncodeNames.currentText()
            if changedEncodeName:
                self.attributeValueObj.encodeNames = changedEncodeName

            changedFeedstockMeasureTypeNonroad = self.lineEditFeedMeasureTypeNon.text().strip()
            if changedFeedstockMeasureTypeNonroad:
                self.attributeValueObj.feedstockMeasureTypeNon = changedFeedstockMeasureTypeNonroad

            changedIrrigationFeedMeasureType = self.lineEditFeedMeasureTypeIrrigNon.text().strip()
            if changedIrrigationFeedMeasureType:
                self.attributeValueObj.irrigationFeedstockMeasureType = changedIrrigationFeedMeasureType

            changedIrrigationFeedNames = self.lineEditFeedIrrigNamesNon.text().strip()
            if changedIrrigationFeedNames:
                self.attributeValueObj.irrigatedFeedstockNames = changedIrrigationFeedNames

            changedTimeResName = self.lineEditTimeResNamesNon.text().strip()
            if changedTimeResName:
                self.attributeValueObj.timeResourceNameNon = changedTimeResName

            changedTempMin = self.lineEditMinTemp.text().strip()
            if changedTempMin:
                self.attributeValueObj.tempMin = changedTempMin

            changedTempMax = self.lineEditMaxTemp.text().strip()
            if changedTempMax:
                self.attributeValueObj.tempMax = changedTempMax

            changedTempMean = self.lineEditMeanTemp.text().strip()
            if changedTempMean:
                self.attributeValueObj.tempMean = changedTempMean

            changeddieselLHV = self.lineEditLowHeat.text().strip()
            if changeddieselLHV:
                self.attributeValueObj.dieselLHV = changeddieselLHV

            changeddieselNH3 = self.lineEditNH3.text().strip()
            if changeddieselNH3:
                self.attributeValueObj.dieselNh3Ef = changeddieselNH3

            changeddieselHydrotoVOC = self.lineEditHydro.text().strip()
            if changeddieselHydrotoVOC:
                self.attributeValueObj.dieselThcVocConversion = changeddieselHydrotoVOC

            changedPMConversionFact = self.lineEditPM10.text().strip()
            if changedPMConversionFact:
                self.attributeValueObj.dieselPm10topm25 = changedPMConversionFact

            ###############################################################################################################

            # Emission Factors attributes value Initialization

            changedFeedMeasureTypeFEF = self.lineEditFeedMeasureTypeEF.text().strip()
            if changedFeedMeasureTypeFEF:
                self.attributeValueObj.feedMeasureTypeEF = changedFeedMeasureTypeFEF

            changedEmissionFactEFPath = self.lineEditEmiFact.text().strip()
            if changedEmissionFactEFPath:
                self.attributeValueObj.emissionFactorsEF = changedEmissionFactEFPath

            changedResDistriEFPath = self.lineEditResDist.text().strip()
            if changedResDistriEFPath:
                self.attributeValueObj.resourceDistributionEF = changedResDistriEFPath

            ###############################################################################################################

            # Fugititve Dust attributes value initialization

            changedOnfarmFeedMeasureTypeFD = self.lineEditOnfarmFeedMeasureTypeFD.text().strip()
            if changedOnfarmFeedMeasureTypeFD:
                self.attributeValueObj.OnfarmFeedMeasureTypeFD = changedOnfarmFeedMeasureTypeFD

            changedOnroadFeedMeasureTypeFD = self.lineEditOnroadFeedMeasureTypeFD.text().strip()
            if changedOnroadFeedMeasureTypeFD:
                self.attributeValueObj.OnroadFeedMeasureTypeFD = changedOnroadFeedMeasureTypeFD

            changedEmissionFactFDPath = self.lineEditEmiFactFD.text().strip()
            if changedEmissionFactFDPath:
                self.attributeValueObj.emissionFactorsFD = changedEmissionFactFDPath

            changedOnrConstPath = self.lineEditOnrConst.text().strip()
            if changedOnrConstPath:
                self.attributeValueObj.onroadConstants = changedOnrConstPath

            changedSiltContPath = self.lineEditSiltCont.text().strip()
            if changedSiltContPath:
                self.attributeValueObj.siltContent = changedSiltContPath

            ###############################################################################################################

            runConfigObj = runConfigCreation(self.attributeValueObj.projectPath,
                                             self.attributeValueObj,
                                             self.attributeValueObj.scenarioName)

            # Display logs in result tab after completion of running the respective module
            self.centralwidget.setCurrentWidget(self.tabResult)

            # Generate Logs
            _log_fname = f"{self.attributeValueObj.scenarioName}_%Y%m%d_%H%M%S.log"
            loggerOutputFilePath = time.strftime(os.path.join(self.attributeValueObj.projectPath, _log_fname))
            # loggerOutputFilePath = os.path.join(tempfile.gettempdir(), loggerOutputFilePath)

            logging.basicConfig(level=self.attributeValueObj.loggerLevel, format='%(asctime)s, %(levelname)-8s'
                                                      ' [%(filename)s:%(module)s.'
                                                      '%(funcName)s.%(lineno)d] %(message)s',
                                filename=loggerOutputFilePath)

            # Set Logger level according to selection of Verbosity Logger Level on Home Page
            if self.attributeValueObj.loggerLevel == "INFO":
                logging.getLogger().setLevel(logging.INFO)
            elif self.attributeValueObj.loggerLevel == "DEBUG":
                logging.getLogger().setLevel(logging.DEBUG)
            elif self.attributeValueObj.loggerLevel == "WARNING":
                logging.getLogger().setLevel(logging.WARNING)
            elif self.attributeValueObj.loggerLevel == "ERROR":
                logging.getLogger().setLevel(logging.ERROR)
            elif self.attributeValueObj.loggerLevel == "CRITICAL":
                logging.getLogger().setLevel(logging.CRITICAL)
            elif self.attributeValueObj.loggerLevel == "UNSET":
                logging.getLogger().setLevel(logging.NOTSET)

            # Displays the logs of the respective running module simultaneously.
            doRun = True
            t = threading.Thread(target=logsPrinter, args=(self.plainTextLog, loggerOutputFilePath, doRun,))
            t.daemon = True
            t.start()

            self.centralwidget.setTabEnabled(0, False)

            movesConfigCreationObj = None
            nonroadConfigCreationObj = None
            emissionFactorsConfigCreationObj = None
            fugitiveDustConfigCreationObj = None

            _moves_tab_enabled = False
            _nonroad_tab_enabled = False
            _ef_tab_enabled = False
            _fug_dust_tab_enabled = False

            # Check for MOVES tab
            if self.centralwidget.isTabEnabled(1):
                _moves_tab_enabled = True
                self.centralwidget.setTabEnabled(1, False)
                movesConfigCreationObj = movesConfigCreation(self.attributeValueObj.projectPath,
                                                             self.attributeValueObj,
                                                             self.attributeValueObj.scenarioName)

            # Check for NONROAD tab
            if self.centralwidget.isTabEnabled(2):
                _nonroad_tab_enabled = True
                self.centralwidget.setTabEnabled(2, False)
                nonroadConfigCreationObj = nonroadConfigCreation(self.attributeValueObj.projectPath,
                                                                 self.attributeValueObj,
                                                                 self.attributeValueObj.scenarioName)

            # Check for Emission Factors tab
            if self.centralwidget.isTabEnabled(3):
                _ef_tab_enabled = True
                self.centralwidget.setTabEnabled(3, False)
                emissionFactorsConfigCreationObj = emissionFactorsConfigCreation(self.attributeValueObj.projectPath,
                                                                                 self.attributeValueObj,
                                                                                 self.attributeValueObj.scenarioName)

            # Check for Fugitive Dust tab
            if self.centralwidget.isTabEnabled(4):
                _fug_dust_tab_enabled = True
                self.centralwidget.setTabEnabled(4, False)
                fugitiveDustConfigCreationObj = fugitiveDustConfigCreation(self.attributeValueObj.projectPath,
                                                                           self.attributeValueObj,
                                                                           self.attributeValueObj.scenarioName)

            _configs = []
            for _config in [runConfigObj, movesConfigCreationObj, nonroadConfigCreationObj,
                            emissionFactorsConfigCreationObj, fugitiveDustConfigCreationObj]:
                if _config is not None:
                    _configs.append(_config)

            # self.runCommand(configs=_configs)

            import queue

            que = queue.Queue()

            t = threading.Thread(target=lambda q, arg: q.put(self.runCommand(arg)), args=(que, _configs))

            # self.runCommand(_configs)

            # Check which module thread is alive
            self.progressBar.setVisible(True)
            self.plainTextLog.setVisible(True)
            self.progressBar.setRange(0, 0)

            # threadList = [threadMOVES, threadNONROAD, threadEF, threadFD]

            # for t in threadList:
            #     if t:
            t.start()
            while t.is_alive():
                loop = QEventLoop()
                QTimer.singleShot(10, loop.quit)
                loop.exec_()

            result = que.get()

            self.progressBar.setVisible(False)

            self.centralwidget.setTabEnabled(1, _moves_tab_enabled)
            self.centralwidget.setTabEnabled(2, _nonroad_tab_enabled)
            self.centralwidget.setTabEnabled(3, _ef_tab_enabled)
            self.centralwidget.setTabEnabled(4, _fug_dust_tab_enabled)
            self.centralwidget.setTabEnabled(0, True)

            resultImagePaths = self.generateGraphs(result, tmpFolder)

            for k, _path in resultImagePaths.items():
                _pixmap = QtGui.QPixmap(_path)
                self.labelResultGraph.resize(self.width(), self.height())
                self.labelResultGraph.setPixmap(_pixmap.scaled(self.labelResultGraph.size(), QtCore.Qt.IgnoreAspectRatio))

    # Generate graph
    def generateGraphs(self, summaries, tempFolder):

        _fpaths = {}

        if 'normalized' in summaries:

            df = summaries['normalized'][['feedstock', 'feedstock_measure',
                                          'tillage_type', 'region_production',
                                          'feedstock_amount', 'pollutant',
                                          'normalized_pollutant_amount']]

            df_subset = df.loc[
                (df.feedstock_measure == 'production')
                & (df.tillage_type == 'conventional tillage')
                & (df.normalized_pollutant_amount != np.inf)
                ].copy()

            df_subset['pollutant_label'] = df_subset.pollutant.str.upper()
            _order = df_subset.feedstock.unique()
            _names = [_.upper() for _ in df_subset.pollutant.unique()]
            sns.set_context("talk", font_scale=1.5)

            g = sns.catplot(x="feedstock",
                            y="normalized_pollutant_amount",
                            #                 hue="pollutant",
                            col="pollutant_label",
                            data=df_subset,
                            kind="box",
                            height=8,
                            aspect=.8,
                            color='red',
                            sharex=True,
                            sharey=False,
                            margin_titles=False,
                            col_wrap=4,
                            order=_order,
                            saturation=0.6,
                            dodge=False,
                            #                 whis=0.9
                            )
            (g.set_axis_labels("", "Emissions (lb/acre)")
             .set_xticklabels([_.title() for _ in _order], rotation=90)
             .set_titles("{col_name}")
             .set(yscale='log')
             )

            resultPath = os.path.join(tempFolder, "normalized.png")
            plt.savefig(resultPath, format='png', bbox_inches='tight', quality=95, dpi=120)

            _fpaths['by_region_production'] = resultPath

        return _fpaths

    #################################################################################################

    # Result Tab Code
    def setupUIResult(self):
        # Result tab created
        self.tabResult = QtWidgets.QWidget()
        self.tabResult.resize(WIDTH, HEIGHT - 200)
        # Result tab added
        self.centralwidget.addTab(self.tabResult, self.getSpacedNames("Results"))

        # Result tab code started
        windowLayoutResult = QGridLayout()
        windowLayoutResult.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        #windowLayoutResult.setColumnStretch(6, 1)

        # Add scrollbar to Result tab
        self.scrollAreaResult = QScrollArea(self.tabResult)
        self.scrollAreaResult.setWidgetResizable(True)
        self.scrollAreaResult.resize(WIDTH, HEIGHT)
        self.scrollAreaResult.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollAreaResult.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.innerWidgetResult = QtWidgets.QWidget()
        self.innerWidgetResult.resize(WIDTH, HEIGHT)
        self.scrollAreaResult.setWidget(self.innerWidgetResult)
        self.innerWidgetResult.setLayout(windowLayoutResult)

        # Add vertical space at the top
        emptyLabelTop = QLabel()
        emptyLabelTop.setFixedHeight(30)
        self.windowLayout.addWidget(emptyLabelTop, 0, 0, 1, 1)

        # Create UI element - Display Logs
        self.plainTextLog = QPlainTextEdit()
        self.plainTextLog.setVisible(False)
        self.plainTextLog.setPlainText("")
        self.plainTextLog.setReadOnly(True)
        self.plainTextLog.setFixedHeight(250)
        self.plainTextLog.setFixedWidth(WIDTH - 36)
        windowLayoutResult.addWidget(self.plainTextLog, 1, 0, 1, 1)

        # Add Vertical Space between the elements
        emptyLabelE = QLabel()
        emptyLabelE.setFixedHeight(20)
        windowLayoutResult.addWidget(emptyLabelE, 2, 0, 1, 1)

        # Created UI element - Display result
        self.labelResultGraph = QLabel()
        self.labelResultGraph.setFixedHeight(500)
        self.labelResultGraph.setFixedWidth(WIDTH)
        windowLayoutResult.addWidget(self.labelResultGraph, 3, 0, 1, 1)

        # Created UI element - Progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        self.progressBar.setStyleSheet("")
        self.progressBar.setFixedWidth(WIDTH)
        windowLayoutResult.addWidget(self.progressBar, 2, 0, 1, 1)

        #########################################################################################################################

    # Function which calls other function of tabs
    def setupUi(self, mainWindow):

        mainWindow.setObjectName("mainWindow")

        self.centralwidget = QtWidgets.QTabWidget(mainWindow)
        mainWindow.setCentralWidget(self.centralwidget)
        self.centralwidget.setObjectName("centralwidget")
        font = QtGui.QFont()
        font.setPointSize(22)

        self.setupUIHomePage()
        self.setupUIMoves()
        self.setupUINonroad()
        self.setupUIEmissionFactors()
        self.setupUIFugitiveDust()
        self.setupUIResult()

        #############################################################################################################################

    def runCommand(self, configs):

        # load config options
        _config = IO.load_configs(*configs)

        with FPEAM(run_config=_config) as _fpeam:

            _fpeam.run()

            # save the raw results to the project path folder specified in run_config
            _fpath = os.path.join(_fpeam.config['project_path'],
                                  '%s_raw.csv' % _fpeam.config['scenario_name'])
            _fpeam.results.to_csv(_fpath, index=False)

            # save several summarized results files to the project folder
            _fpeam.summarize()

            # print(_fpeam.summaries)

            # self.results = _fpeam.results
            # self.summaries = _fpeam.summaries

            return _fpeam.summaries

            # print("Done")


# Display logs in Result tab
def logsPrinter(textField, loggerOutputFilePath, doRun):
    fileOpened = False
    while not fileOpened:
        try:
            with open(loggerOutputFilePath) as f:
                fileOpened = True
                while doRun:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                    else:
                        textField.appendPlainText(line)
        except FileNotFoundError as e:
            print("Caught Exception ", e)
            print("Trying again")
            time.sleep(1)

# #############################################################################################


# Main function
if __name__ == "__main__":
    # CSS Code
    styleSheet = """
    
    QWidget {
        background-color: #ffffff;
    }


    QLabel#titleFPEAMLine {
        border: 1px solid #000000;
    }

    QLabel#yearErrorMsg {
        width: 160px;
        height: 30px;
        background: #ffffff;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 13px;
        line-height: 16px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #000000;
    }

    QLabel#allLabels {

        background: #ffffff;
        border: 1px solid #000000;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: bold;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #000000;
    }

    QLabel#title {
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 33px;
        line-height: 39px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #028ACC;

    }

    QLabel#subTitleLabels {
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 24px;
        line-height: 28px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #028ACC;
    }

    QCheckBox {
        background: #FFFFFF;
        box-sizing: border-box;
        border-radius: 5px;
        box-shadow: 1px 1px 1px rgba(0, 0, 0, 0.25);
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 13px;
        line-height: 15px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #000000;
        border-radius: 5px;
    }

    QPushButton {
        background: #F4F7F7;
        border: 1px solid #495965;
        box-sizing: border-box;
        box-shadow: 2px 2px 1px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #000000;
        border-radius: 5px;
    }

    QPushButton#resetRunBtn {
        border: 1px solid #000000;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 18px;
        line-height: 21px;
        display: flex;
        align-items: center;
        text-align: center;
        color: #000000;
        border-radius: 5px
    }

    QPushButton#expandCollapseIcon {
        background: #ffffff;
        align-items: center;
        text-align: center;
        color: #000000;
        border: 1px solid #ffffff;
        font-style: bold;
        font-size : 30px
    }

    QLineEdit {
        background: #FFFFFF;
        border: 1px solid #495965;
        box-sizing: border-box;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.25);
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        align-items: center;
        text-align: center;

    }

    QComboBox {
        background: #FFFFFF;
        border: 1px solid #495965;
        box-sizing: border-box;
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        text-align: center;
        color: #000000;
        border-radius: 5px;

    }

    QComboBox#AggLevelCombo {
        background: #FFFFFF;
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        text-align: center;
        color: #000000;
    }

    QSpinBox {
        background: #FFFFFF;
        border: 1px solid #495965;
        box-sizing: border-box;
        border-radius: 5px;
        font-family: "Roboto";
        font-style: normal;
        font-weight: normal;
        font-size: 14px;
        line-height: 16px;
        display: flex;
        text-align: center;
        color: #000000;
        border-radius: 5px;

    }

    QScrollBar {
        background-color: grey;
    }

    QTabBar::tab:selected {
        background: #028ACC;
        color: #ffffff
    }
    
    @font-face {
    font-family: 'Roboto';
    src: url('Roboto-Regular-webfont.eot');
    src: url('Roboto-Regular-webfont.eot?#iefix') format('embedded-opentype'),
         url('Roboto-Regular-webfont.woff') format('woff'),
         url('Roboto-Regular-webfont.ttf') format('truetype'),
         url('Roboto-Regular-webfont.svg#RobotoRegular') format('svg');
    font-weight: normal;
    font-style: normal;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-Italic-webfont.eot');
        src: url('Roboto-Italic-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-Italic-webfont.woff') format('woff'),
             url('Roboto-Italic-webfont.ttf') format('truetype'),
             url('Roboto-Italic-webfont.svg#RobotoItalic') format('svg');
        font-weight: normal;
        font-style: italic;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-Bold-webfont.eot');
        src: url('Roboto-Bold-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-Bold-webfont.woff') format('woff'),
             url('Roboto-Bold-webfont.ttf') format('truetype'),
             url('Roboto-Bold-webfont.svg#RobotoBold') format('svg');
        font-weight: bold;
        font-style: normal;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-BoldItalic-webfont.eot');
        src: url('Roboto-BoldItalic-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-BoldItalic-webfont.woff') format('woff'),
             url('Roboto-BoldItalic-webfont.ttf') format('truetype'),
             url('Roboto-BoldItalic-webfont.svg#RobotoBoldItalic') format('svg');
        font-weight: bold;
        font-style: italic;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-Thin-webfont.eot');
        src: url('Roboto-Thin-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-Thin-webfont.woff') format('woff'),
             url('Roboto-Thin-webfont.ttf') format('truetype'),
             url('Roboto-Thin-webfont.svg#RobotoThin') format('svg');
        font-weight: 200;
        font-style: normal;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-ThinItalic-webfont.eot');
        src: url('Roboto-ThinItalic-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-ThinItalic-webfont.woff') format('woff'),
             url('Roboto-ThinItalic-webfont.ttf') format('truetype'),
             url('Roboto-ThinItalic-webfont.svg#RobotoThinItalic') format('svg'); (under the Apache Software License).
        font-weight: 200;
        font-style: italic;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-Light-webfont.eot');
        src: url('Roboto-Light-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-Light-webfont.woff') format('woff'),
             url('Roboto-Light-webfont.ttf') format('truetype'),
             url('Roboto-Light-webfont.svg#RobotoLight') format('svg');
        font-weight: 100;
        font-style: normal;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-LightItalic-webfont.eot');
        src: url('Roboto-LightItalic-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-LightItalic-webfont.woff') format('woff'),
             url('Roboto-LightItalic-webfont.ttf') format('truetype'),
             url('Roboto-LightItalic-webfont.svg#RobotoLightItalic') format('svg');
        font-weight: 100;
        font-style: italic;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-Medium-webfont.eot');
        src: url('Roboto-Medium-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-Medium-webfont.woff') format('woff'),
             url('Roboto-Medium-webfont.ttf') format('truetype'),
             url('Roboto-Medium-webfont.svg#RobotoMedium') format('svg');
        font-weight: 300;
        font-style: normal;
    }

    @font-face {
        font-family: 'Roboto';
        src: url('Roboto-MediumItalic-webfont.eot');
        src: url('Roboto-MediumItalic-webfont.eot?#iefix') format('embedded-opentype'),
             url('Roboto-MediumItalic-webfont.woff') format('woff'),
             url('Roboto-MediumItalic-webfont.ttf') format('truetype'),
             url('Roboto-MediumItalic-webfont.svg#RobotoMediumItalic') format('svg');
        font-weight: 300;
        font-style: italic;
    }


    """

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(styleSheet)
    mainWindow = Window()
    mainWindow.setMinimumSize(WIDTH, HEIGHT)
    mainWindow.setMaximumWidth(WIDTH)
    mainWindow.setWindowTitle("FPEAM")
    ui = AlltabsModule()

    # Header Code
    headerlabel = QLabel(mainWindow)
    pixmapLine = QPixmap('header.png')
    pixmap = pixmapLine.scaledToHeight(80)
    headerlabel.setPixmap(pixmap)
    headerlabel.setFixedHeight(55)
    header = QDockWidget(mainWindow)
    header.setFeatures(QDockWidget.NoDockWidgetFeatures)
    header.setTitleBarWidget(headerlabel)

    hbox = QtWidgets.QHBoxLayout()
    hbox.addWidget(mainWindow)

    mainWindow.addDockWidget(QtCore.Qt.TopDockWidgetArea, header)

    # Footer Code
    footerlabel = QLabel(mainWindow)
    footerlabel.setFixedHeight(105)
    pixmapLine = QPixmap('footer.png')
    pixmap = pixmapLine.scaledToHeight(80)
    footerlabel.setPixmap(pixmap)

    ui.setupUi(mainWindow)

    scrollAreaList = []
    scrollAreaList.append(ui.scrollAreaFPEAM)
    scrollAreaList.append(ui.scrollAreaMOVES)
    scrollAreaList.append(ui.scrollAreaNONROAD)
    scrollAreaList.append(ui.scrollAreaEF)
    scrollAreaList.append(ui.scrollAreaFD)
    scrollAreaList.append(ui.scrollAreaResult)
    mainWindow.setSizeDependency(scrollAreaList)

    footer = QDockWidget(mainWindow)
    footer.setTitleBarWidget(footerlabel)
    footer.setFloating(False)
    footer.setFeatures(QDockWidget.NoDockWidgetFeatures)
    mainWindow.addDockWidget(QtCore.Qt.BottomDockWidgetArea, footer)

    mainWindow.show()
    sys.exit(app.exec_())
