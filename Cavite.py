import os
import string
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import dicom
from dicom.filereader import InvalidDicomError
from DICOMScalarVolumePlugin import DICOMScalarVolumePluginClass
import PythonQt
import scipy
import SimpleITK as sitk
import sitkUtils
import time
import numpy as np
from scipy import ndimage
from scipy.ndimage import label, generate_binary_structure, maximum
import scipy.ndimage as spyndi
import slicer.util
import vtk.util.numpy_support
import scipy.ndimage as spyndi
import cv2
import math
import string
from vtk.util import numpy_support
# -*- coding: utf-8 -*-


#
# Cavite
#
class Cavite(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = u"Analyse de la cavit\u00e9 abdominale"
    self.parent.categories = [u"Pour le RECEVEUR : Volum\u00e9trie et distances dans la cavit\u00e9 abdominale"]
    self.parent.dependencies = []
    self.parent.contributors = ["Laura Seimpere"]
    self.parent.helpText = u"""
    Segmentation de la cavit\u00e9 abdominale du receveur afin de connaitre ses attributs (volume, distances choisies par l\u00b4utilisateur).
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
"""


#
# CaviteWidget - INTERFACE GRAPHIQUE
#
class CaviteWidget(ScriptedLoadableModuleWidget):

  def __init__(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.logic = CaviteLogic()
    self.logic.logCallback = self.addLogcor
    self.logic.logCallback = self.addLogsag
    self.logic.logCallback = self.addLogax
    self.parameterNode = None
    self.parameterNodeObserver = None
    self.clippingMarkupNode = None
    self.clippingMarkupNodeObserver = None

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self.logicvol = None
    self.grayscaleNode = None
    self.labelNode = None
    self.fileName = None
    self.fileDialog = None
       
    self.step0CollapsibleButton = ctk.ctkCollapsibleButton()
    self.step0CollapsibleButton.text = u"Receveur : Volume et distances de la cavit\u00e9 abdominale"
    self.layout.addWidget(self.step0CollapsibleButton)
    self.step0FormLayout = qt.QFormLayout(self.step0CollapsibleButton)
   
       
		#########
    # Step 1 : Charger images
		#########
    self.stepsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.stepsCollapsibleButton.text = "Etape 1 : Chargement des images"
    self.layout.addWidget(self.stepsCollapsibleButton)
    self.stepsFormLayout = qt.QFormLayout(self.stepsCollapsibleButton)

					# Chargement avec dossier DICOM
					# Bouton de chargement par DICOM mis sur True
    self.loadFromDicom = qt.QRadioButton("Charger depuis DICOM")
    self.loadFromDicom.checked = True
          # Zone de recherche du repertoire contenant les images a traiter
    self.inputDicomSelector = ctk.ctkDirectoryButton()
    self.inputDicomSelector.caption = u'Entr\u00e9es DICOM'
    self.inputDicomSelector.directory = os.path.join(os.path.expanduser("~"),"Documents/TroisDSlicer/ircad/ircad2arterielle/PATIENT_DICOM")
    self.inputDicomSelector.setMaximumWidth(550)
          # Bouton d'importation des images
    self.loadDicomsButton = qt.QPushButton("Importer et charger ")
    self.dicomVolumeNode = None

    self.importDicomLayout = qt.QHBoxLayout()
    self.loadDicomsButton.setMaximumWidth(300)
    self.importDicomLayout.addWidget(self.inputDicomSelector, 9)
    self.importDicomLayout.addWidget(self.loadDicomsButton, 1)
    self.stepsFormLayout.addRow(self.loadFromDicom, self.importDicomLayout)

					# Chargement avec DICOMDatabase Slicer
					# Bouton de chargement par Slicer a selectionner
    self.loadFromSlicer = qt.QRadioButton("Charger depuis SLICER")
    self.slicerVolumeNode = None

					# Choix du volume a traiter parmi ceux prealablement charges
    self.inputSlicer = slicer.qMRMLNodeComboBox()
    self.inputSlicer.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSlicer.selectNodeUponCreation = True
    self.inputSlicer.addEnabled = False
    self.inputSlicer.removeEnabled = False
    self.inputSlicer.noneEnabled = False
    self.inputSlicer.showHidden = False
    self.inputSlicer.showChildNodeTypes = False
    self.inputSlicer.setMRMLScene(slicer.mrmlScene)
    self.inputSlicer.setToolTip(u"Choisir l\u00b4entr\u00e9e de l\u00b4algorithme." )
    self.inputSlicer.setMaximumWidth(550)
    self.importSlicerLayout = qt.QHBoxLayout()

					# Bouton d'importation des images du volume choisi
    self.importim = qt.QPushButton("Importer et charger ")
    self.importim.toolTip = "Importer et charger les images."
    self.importim.setMaximumWidth(300)
    self.stepsFormLayout.addWidget(self.importim)
    
    self.importSlicerLayout.addWidget(self.inputSlicer)
    self.importSlicerLayout.addWidget(self.importim)
    self.stepsFormLayout.addRow(self.loadFromSlicer, self.importSlicerLayout)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.stepsFormLayout.addRow(self.inputDistLabel)

    #########
    # Step 2 : Selection du volume a analyser
	  #########
    self.step2CollapsibleButton = ctk.ctkCollapsibleButton()
    self.step2CollapsibleButton.text = u"Etape 2 : S\u00e9lection du volume \u00e0 analyser"
    self.layout.addWidget(self.step2CollapsibleButton)
    self.step2FormLayout = qt.QFormLayout(self.step2CollapsibleButton)
    
					# Input volume selector
    self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.inputVolumeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode",""))
    self.inputVolumeSelector.addEnabled = False
    self.inputVolumeSelector.removeEnabled = False
    self.inputVolumeSelector.noneEnabled = False
    self.inputVolumeSelector.showHidden = False
    self.inputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.inputVolumeSelector.setToolTip(u"Volume d\u00b4entr\u00e9e qui sera rogn\u00e9.")
    self.inputVolumeSelector.setMaximumWidth(250)
    self.step2FormLayout.addRow(u"  Volume d\u00b4entr\u00e9e : ", self.inputVolumeSelector)

					# Clipping model selector
    self.clippingModelSelector = slicer.qMRMLNodeComboBox()
    self.clippingModelSelector.nodeTypes = (("vtkMRMLModelNode"), "")
    self.clippingModelSelector.addEnabled = True
    self.clippingModelSelector.removeEnabled = False
    self.clippingModelSelector.noneEnabled = False
    self.clippingModelSelector.showHidden = False
    self.clippingModelSelector.renameEnabled = False
    self.clippingModelSelector.selectNodeUponCreation = True
    self.clippingModelSelector.showChildNodeTypes = False
    self.clippingModelSelector.setMRMLScene(slicer.mrmlScene)
    self.clippingModelSelector.setToolTip(u"Choisir le mod\u00e8le de surface rogn\u00e9.")
    self.clippingModelSelector.setMaximumWidth(250)
    self.step2FormLayout.addRow("  Surface de rognage : ", self.clippingModelSelector)
    
					# Markup selector
    self.clippingMarkupSelector = slicer.qMRMLNodeComboBox()
    self.clippingMarkupSelector.nodeTypes = (("vtkMRMLMarkupsFiducialNode"), "")
    self.clippingMarkupSelector.addEnabled = True
    self.clippingMarkupSelector.removeEnabled = False
    self.clippingMarkupSelector.noneEnabled = False
    self.clippingMarkupSelector.showHidden = False
    self.clippingMarkupSelector.renameEnabled = True
    self.clippingMarkupSelector.baseName = "A"
    self.clippingMarkupSelector.setMRMLScene(slicer.mrmlScene)
    self.clippingMarkupSelector.setToolTip(u"Si les marqueurs sont s\u00e9lectionn\u00e9s, la surface de rognage est g\u00e9n\u00e9r\u00e9e \u00e0 partir des points marqueurs. La surface est mise \u00e0 jour automatiquement quand les marqueurs sont d\u00e9plac\u00e9s.")
    self.clippingMarkupSelector.setMaximumWidth(250)
    self.step2FormLayout.addRow("  Surface de rognage par marqueurs : ", self.clippingMarkupSelector)
    
					# Clip inside/outside the surface
    self.clipOutsideSurfaceCheckBox = qt.QCheckBox()
    self.clipOutsideSurfaceCheckBox.checked = False
    self.clipOutsideSurfaceCheckBox.setToolTip(u"Si coch\u00e9, les valeurs de voxels seront remplies hors de la surface de rognage.")
    self.step2FormLayout.addRow(u"  Rognage ext\u00e9rieur : ", self.clipOutsideSurfaceCheckBox)    
        
					# Outside fill value
    self.fillValueEdit = qt.QSpinBox()
    self.fillValueEdit.setToolTip(u"Choisir l\u00b4intensit\u00e9 de voxel qui sera utilis\u00e9e pour remplir les r\u00e9gions rogn\u00e9es.")
    self.fillValueEdit.minimum = -32768
    self.fillValueEdit.maximum = 65535
    
					# Output volume selector
    self.outputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.outputVolumeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputVolumeSelector.selectNodeUponCreation = True
    self.outputVolumeSelector.addEnabled = True
    self.outputVolumeSelector.removeEnabled = True
    self.outputVolumeSelector.noneEnabled = False
    self.outputVolumeSelector.showHidden = False
    self.outputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.outputVolumeSelector.setToolTip(u"Volume de sortie rogn\u00e9. Il doit \u00eatre le m\u00eame que le volume d\u00b4entr\u00e9e pour un rognage cumul\u00e9." )
    self.outputVolumeSelector.setMaximumWidth(250)
    self.step2FormLayout.addRow("  Volume de sortie : ", self.outputVolumeSelector)

					# Apply Button
    self.applyButton = qt.QPushButton(u"Ex\u00e9cuter")
    self.applyButton.toolTip = u"Rogner le volume avec le mod\u00e8le de surface."
    self.applyButton.enabled = False
    self.applyButton.setMaximumWidth(350)
    self.step2FormLayout.addRow(self.applyButton)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.step2FormLayout.addRow(self.inputDistLabel)
    
    
    #########
    # Step 3 : Calcul du volume de la cavite abdominale selectionnee
	  #########
    step09CollapsibleButton = ctk.ctkCollapsibleButton()
    step09CollapsibleButton.text = u"Etape 3 : Calcul du volume de la cavit\u00e9 abdominale s\u00e9lectionn\u00e9e"
    self.layout.addWidget(step09CollapsibleButton)
    self.step3FormLayout = qt.QFormLayout(step09CollapsibleButton)

					# Grayscale volume selector
    self.grayscaleSelectorFrame = qt.QFrame(self.parent)
    self.grayscaleSelectorFrame.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.grayscaleSelectorFrame)

    self.grayscaleSelectorLabel = qt.QLabel("  Volume en niveaux de gris : ", self.grayscaleSelectorFrame)
    self.grayscaleSelectorLabel.setToolTip(u"S\u00e9lectionner le volume en niveaux de gris (scalar volume node en arri\u00e8re plan en niveaux de gris) pour les calculs statistiques.")
    self.grayscaleSelectorFrame.layout().addWidget(self.grayscaleSelectorLabel)

    self.grayscaleSelector = slicer.qMRMLNodeComboBox(self.grayscaleSelectorFrame)
    self.grayscaleSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.grayscaleSelector.selectNodeUponCreation = False
    self.grayscaleSelector.addEnabled = False
    self.grayscaleSelector.removeEnabled = False
    self.grayscaleSelector.noneEnabled = False
    self.grayscaleSelector.showHidden = False
    self.grayscaleSelector.showChildNodeTypes = False
    self.grayscaleSelector.setMRMLScene(slicer.mrmlScene)
    self.grayscaleSelectorFrame.setMaximumWidth(450)
    self.grayscaleSelectorFrame.layout().addWidget(self.grayscaleSelector)

					# Label volume selector
    self.labelSelectorFrame = qt.QFrame()
    self.labelSelectorFrame.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.labelSelectorFrame)
    self.labelSelectorLabel = qt.QLabel()
    self.labelSelectorLabel.setText("  Carte des labels : ")
    self.labelSelectorFrame.layout().addWidget(self.labelSelectorLabel)
    self.labelSelector = slicer.qMRMLNodeComboBox()
    self.labelSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.labelSelector.selectNodeUponCreation = True
    self.labelSelector.addEnabled = True
    self.labelSelector.noneEnabled = False
    self.labelSelector.removeEnabled = False
    self.labelSelector.showHidden = False
    self.labelSelector.showChildNodeTypes = False
    self.labelSelector.setMRMLScene(slicer.mrmlScene)
    self.labelSelectorFrame.setMaximumWidth(447)
    self.labelSelector.setToolTip(u"Choisir la carte des labels \u00e0 \u00e9diter.")
    self.labelSelectorFrame.layout().addWidget(self.labelSelector)

					# Apply Button step 9
    self.applyButton9 = qt.QPushButton(u"Ex\u00e9cuter la Volum\u00e9trie de la Cavit\u00e9")
    self.applyButton9.toolTip = "Calculer les statistiques."
    self.applyButton9.enabled = False
    self.applyButton9.setMaximumWidth(350)
    self.parent.layout().addWidget(self.applyButton9)

					# Model and view for stats table
    self.view = qt.QTableView()
    self.view.sortingEnabled = True
    self.parent.layout().addWidget(self.view)
        
					# Save button
    self.exportToTableButton = qt.QPushButton("Exporter en tableau")
    self.exportToTableButton.toolTip = "Exporter les statistiques en tableau."
    self.exportToTableButton.enabled = False
    self.parent.layout().addWidget(self.exportToTableButton)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.parent.layout().addWidget(self.inputDistLabel)


    #########
    # Step 4 : Calcul des distances dans la cavite abdominale selectionnee
	  #########
    # VUE CORONALE
	  ##############
    stepcorCollapsibleButton = ctk.ctkCollapsibleButton()
    stepcorCollapsibleButton.text = "Etape 4 : Calcul de la distance coronale"
    self.layout.addWidget(stepcorCollapsibleButton)
    self.step4FormLayout = qt.QFormLayout(stepcorCollapsibleButton)
    self.seedCoordsdistcor = {}

					# Setup Button
    self.setupButtoncor = qt.QPushButton("Configurer")
    self.setupButtoncor.toolTip = u"Configurer l\u00b4algorithme."
    self.setupButtoncor.enabled = False
    self.setupButtoncor.setMaximumWidth(350)
    self.step4FormLayout.addRow(self.setupButtoncor)
    
					# Seed selector
    self.pointSelectorcor = slicer.qSlicerSimpleMarkupsWidget()
    self.pointSelectorcor.objectName = u'pointS\u00e9lectorcor'
    self.pointSelectorcor.toolTip = u"S\u00e9lectionner un point."
    self.pointSelectorcor.defaultNodeColor = qt.QColor(0,255,0)
    self.pointSelectorcor.tableWidget().hide()
    self.pointSelectorcor.markupsSelectorComboBox().noneEnabled = False
    self.pointSelectorcor.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup    
    self.pointSelectorcor.markupsPlaceWidget().buttonsVisible = True
    self.pointSelectorcor.markupsPlaceWidget().placeButton().show()
    self.pointSelectorcor.setMRMLScene(slicer.mrmlScene)

    self.pointBoxcor = qt.QHBoxLayout()
    self.pointLabelWidgetcor = qt.QLabel("  Choisir une distance :")
    self.pointBoxcor.addWidget(self.pointLabelWidgetcor)
    self.pointBoxcor.addWidget(self.pointSelectorcor)
    self.pointSelectorcor.setMaximumWidth(340)
    self.step4FormLayout.addRow(self.pointLabelWidgetcor, self.pointSelectorcor)
    
					# Apply button 
    self.applyButtoncor = qt.QPushButton("Calculer la distance")
    self.applyButtoncor.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButtoncor.setMaximumWidth(350)
    self.applyButtoncor.enabled = False
    self.step4FormLayout.addWidget(self.applyButtoncor)

					# Box des resultats
    self.statusLabelcor = qt.QPlainTextEdit()
    self.statusLabelcor.setTextInteractionFlags(qt.Qt.TextSelectableByMouse)
    self.step4FormLayout.addRow(self.statusLabelcor)
    
					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.step4FormLayout.addRow(self.inputDistLabel)


    # VUE SAGITTALE
	  ###############
    stepsagCollapsibleButton = ctk.ctkCollapsibleButton()
    stepsagCollapsibleButton.text = "Etape 5 : Calcul de la distance sagittale"
    self.layout.addWidget(stepsagCollapsibleButton)
    self.step5FormLayout = qt.QFormLayout(stepsagCollapsibleButton)
    self.seedCoordsdistsag = {}

					# Setup Button
    self.setupButtonsag = qt.QPushButton("Configurer")
    self.setupButtonsag.toolTip = u"Configurer l\u00b4algorithme."
    self.setupButtonsag.enabled = False
    self.setupButtonsag.setMaximumWidth(350)
    self.step5FormLayout.addRow(self.setupButtonsag)
    
					# Seed selector
    self.pointSelectorsag = slicer.qSlicerSimpleMarkupsWidget()
    self.pointSelectorsag.objectName = u'pointS\u00e9lectorsag'
    self.pointSelectorsag.toolTip = u"S\u00e9lectionner un point."
    self.pointSelectorsag.defaultNodeColor = qt.QColor(0,255,0)
    self.pointSelectorsag.tableWidget().hide()
    self.pointSelectorsag.markupsSelectorComboBox().noneEnabled = False
    self.pointSelectorsag.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup    
    self.pointSelectorsag.markupsPlaceWidget().buttonsVisible = True
    self.pointSelectorsag.markupsPlaceWidget().placeButton().show()
    self.pointSelectorsag.setMRMLScene(slicer.mrmlScene)

    self.pointBoxsag = qt.QHBoxLayout()
    self.pointLabelWidgetsag = qt.QLabel("  Choisir une distance :")
    self.pointBoxsag.addWidget(self.pointLabelWidgetsag)
    self.pointBoxsag.addWidget(self.pointSelectorsag)
    self.pointSelectorsag.setMaximumWidth(340)
    self.step5FormLayout.addRow(self.pointLabelWidgetsag, self.pointSelectorsag)
    
					# Apply button
    self.applyButtonsag = qt.QPushButton("Calculer la distance")
    self.applyButtonsag.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButtonsag.setMaximumWidth(350)
    self.applyButtonsag.enabled = False
    self.step5FormLayout.addWidget(self.applyButtonsag)
    
					# Box des resultats
    self.statusLabelsag = qt.QPlainTextEdit()
    self.statusLabelsag.setTextInteractionFlags(qt.Qt.TextSelectableByMouse)
    self.step5FormLayout.addRow(self.statusLabelsag)
    
					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.step5FormLayout.addRow(self.inputDistLabel)


    # VUE AXIALE
	  ############
    stepaxCollapsibleButton = ctk.ctkCollapsibleButton()
    stepaxCollapsibleButton.text = "Etape 6 : Calcul de la distance axiale"
    self.layout.addWidget(stepaxCollapsibleButton)
    self.step6FormLayout = qt.QFormLayout(stepaxCollapsibleButton)
    self.seedCoordsdistax = {}

					# Setup Button
    self.setupButtonax = qt.QPushButton("Configurer")
    self.setupButtonax.toolTip = u"Configurer l\u00b4algorithme."
    self.setupButtonax.enabled = False
    self.setupButtonax.setMaximumWidth(350)
    self.step6FormLayout.addRow(self.setupButtonax)
    
					# Seed selector
    self.pointSelectorax = slicer.qSlicerSimpleMarkupsWidget()
    self.pointSelectorax.objectName = u'pointS\u00e9lectorax'
    self.pointSelectorax.toolTip = u"S\u00e9lectionner un point."
    self.pointSelectorax.defaultNodeColor = qt.QColor(0,255,0)
    self.pointSelectorax.tableWidget().hide()
    self.pointSelectorax.markupsSelectorComboBox().noneEnabled = False
    self.pointSelectorax.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup    
    self.pointSelectorax.markupsPlaceWidget().buttonsVisible = True
    self.pointSelectorax.markupsPlaceWidget().placeButton().show()
    self.pointSelectorax.setMRMLScene(slicer.mrmlScene)

    self.pointBoxax = qt.QHBoxLayout()
    self.pointLabelWidgetax = qt.QLabel("  Choisir une distance :")
    self.pointBoxax.addWidget(self.pointLabelWidgetax)
    self.pointBoxax.addWidget(self.pointSelectorax)
    self.pointSelectorax.setMaximumWidth(340)
    self.step6FormLayout.addRow(self.pointLabelWidgetax, self.pointSelectorax)
    
					# Apply button step 8
    self.applyButtonax = qt.QPushButton("Calculer la distance")
    self.applyButtonax.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButtonax.setMaximumWidth(350)
    self.applyButtonax.enabled = False
    self.step6FormLayout.addWidget(self.applyButtonax)

					# Box des resultats
    self.statusLabelax = qt.QPlainTextEdit()
    self.statusLabelax.setTextInteractionFlags(qt.Qt.TextSelectableByMouse)
    self.step6FormLayout.addRow(self.statusLabelax)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.step6FormLayout.addRow(self.inputDistLabel)

	  #############
    # Connections
    #############
    self.loadFromDicom.connect("clicked(bool)", self.onSelect)
    self.loadDicomsButton.connect("clicked(bool)", self.onDicomImportClicked)
    self.loadDicomsButton.connect("clicked(bool)", self.onSelect)

    self.loadFromSlicer.connect("clicked(bool)", self.onSlicer)
    self.importim.connect('clicked()', self.onImportIm)
    self.inputSlicer.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputVolumeSelect)
    self.clippingModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onClippingModelSelect)
    self.clippingMarkupSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onClippingMarkupSelect)
    self.outputVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onOutputVolumeSelect)
    
    self.applyButton9.connect('clicked(bool)', self.onApplyButton9)
    self.exportToTableButton.connect('clicked(bool)', self.onExportToTable)
    self.grayscaleSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onGrayscaleSelect)
    self.labelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect)
    
    self.setupButtoncor.connect('clicked(bool)', self.onSetupButtoncor)
    self.applyButtoncor.connect('clicked(bool)', self.onApplyButtoncor)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.pointSelectorcor, 'setMRMLScene(vtkMRMLScene*)')
    
    self.setupButtonsag.connect('clicked(bool)', self.onSetupButtonsag)
    self.applyButtonsag.connect('clicked(bool)', self.onApplyButtonsag)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.pointSelectorsag, 'setMRMLScene(vtkMRMLScene*)')
    
    self.setupButtonax.connect('clicked(bool)', self.onSetupButtonax)
    self.applyButtonax.connect('clicked(bool)', self.onApplyButtonax)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.pointSelectorax, 'setMRMLScene(vtkMRMLScene*)')
        
    self.tmpNodescor = []
    self.tmpNodesvolcor = []
    self.tmpNodesdistcor = []
    
    self.tmpNodesax = []
    self.tmpNodesvolax = []
    self.tmpNodesdistax = []
    
    self.tmpNodessag = []
    self.tmpNodesvolsag = []
    self.tmpNodesdistsag = []
    
					# Define list of widgets for updateGUIFromParameterNode, updateParameterNodeFromGUI, and addGUIObservers
    self.valueEditWidgets = {"RognerHorsSurface": self.clipOutsideSurfaceCheckBox, "ValeurRemplissage": self.fillValueEdit}
    self.nodeSelectorWidgets = {"InputVolume": self.inputVolumeSelector, "ModeleRognage": self.clippingModelSelector, "MarqueurRognage": self.clippingMarkupSelector, "VolumedeSortie": self.outputVolumeSelector}

					# Use singleton parameter node (it is created if does not exist yet)
    parameterNode = self.logic.getParameterNode()
    
					# Set parameter node (widget will observe it and also updates GUI)
    self.setAndObserveParameterNode(parameterNode)

    self.setAndObserveClippingMarkupNode(self.clippingMarkupSelector.currentNode())
    
    self.addGUIObservers()
 
					# Add vertical spacer
    self.layout.addStretch(1)  
 
					# Refresh Apply button state
    self.onSelect()


  def cleanup(self):
    self.removeGUIObservers()
    self.setAndObserveParameterNode(None)
    self.setAndObserveClippingMarkupNode(None)
    pass
    

  def onSelect(self):
    if self.loadFromDicom.checked:
      self.masterVolumeNode = self.dicomVolumeNode
    if self.loadFromSlicer.checked:
      self.masterVolumeNode = self.inputSlicer.currentNode()
    self.applyButton.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton9.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtoncor.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButtoncor.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonax.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButtonax.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonsag.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButtonsag.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    
    
  def onSlicer(self):
    if self.loadFromSlicer.checked:  
      prompt = ctk.ctkMessageBox()
      scriptpath = os.path.dirname(__file__)
      iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'Cavite.png')
      iconpath = iconpath.replace('\\', '/')
      icon = qt.QIcon(iconpath)
      prompt.setWindowIcon(icon)
      prompt.setWindowTitle("Charger les images")
      prompt.setIcon(qt.QMessageBox.Information)
      prompt.setText("Parcourir les images dans Show DICOM Browser, les importer en cliquant sur 'Load' puis les charger en cliquant sur \"%s\"" % self.importim.text)
      prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
      prompt.setDefaultButton(qt.QMessageBox.Ok)
      answer = prompt.exec_()
      if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return 
      reformatModuleWidget = slicer.modules.dicom.createNewWidgetRepresentation()
      reformatModuleWidget.setMRMLScene(slicer.app.mrmlScene())
      reformatModuleWidget.show() 
      self.masterVolumeNode = self.inputSlicer.currentNode() 
    self.applyButton.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton9.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtoncor.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButtoncor.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonax.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButtonax.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonsag.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButtonsag.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    
    

#######################
# FONCTIONS POUR ETAPES
#######################
#######################
# Fonctions pour step 1 : Chargement des images
#######################
# DICOM
#######
					# Importation des fichiers du repertoire
  def onDicomImportClicked(self):
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    self.dicomVolumeNode = self.loadDicoms(self.inputDicomSelector.directory)
    d = self.dicomVolumeNode.GetDisplayNode()
					# Visualisation en niveaux de gris
    d.SetAutoWindowLevel(0)
    d.SetWindowLevel(350,40)
					# Visualisation 3D
    redWidget = lm.sliceWidget('Red')
    redWidget.sliceController().setSliceLink(True)
    redWidget.sliceController().setSliceVisible(True)
    threeDWidget = lm.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()
    
					# Chargement des fichiers DICOM
  def loadDicoms(self, dcmpath):
    volArray = []
    files = os.listdir(dcmpath)
    files = [os.path.join(dcmpath, file) for file in files]
    volDir = self.inputDicomSelector.directory
    for file in files:
      if os.path.isfile(file):
        try:
          ds = dicom.read_file(file)
          sn = ds.SeriesNumber
          volArray.append(file)
        except InvalidDicomError as ex:
          pass  
    if len(volArray) == 0:
      logging.info(u"Aucun fichier DICOM trouv\u00e9 dans le r\u00e9pertoire" + dcmpath)
      logging.info(u"Recherche r\u00e9cursive en cours...")
      qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
      recdcms = self.findDicoms(dcmpath)
      qt.QApplication.restoreOverrideCursor()
      if len(recdcms) == 0:
        return None
      else:
        keys = recdcms.keys()
        diag = qt.QInputDialog()
        scriptpath = os.path.dirname(__file__)
        iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationCavite.png')
        iconpath = iconpath.replace('\\', '/')
        icon = qt.QIcon(iconpath)
        diag.setWindowIcon(icon)
        ok = PythonQt.BoolResult()
        sn = qt.QInputDialog.getItem(diag,"Choisir le Volume", u"Choisir le num\u00e9ro de s\u00e9ries :", keys, 0, False, ok)
        volArray = recdcms[str(sn)]
        volDir = os.path.dirname(volArray[0])
        if not ok:
          logging.error(u"Aucun volume s\u00e9lectionn\u00e9. Fin en cours...")
          return None
    self.inputDicomSelector.directory = volDir
    importer = DICOMScalarVolumePluginClass()
    volNode = importer.load(importer.examine([volArray])[0])
    volNode.SetName(str(sn))
    volNode.SetName("IRCAD Volume")
    return volNode

					# Recherche des fichiers DICOM
  def findDicoms(self, dcmpath):
    dcmdict = {}
    for root, dirs, files in os.walk(dcmpath):
      files = [os.path.join(root, filename) for filename in files]
      for file in files:
        try:
          ds = dicom.read_file(file)
          sn = str(ds.SeriesNumber)
          if sn not in dcmdict:
            dcmdict[sn] = []
          dcmdict[sn].append(file)
        except Exception as e:
          pass
    if len(dcmdict) == 0:
      logging.error(u"Aucun fichier DICOM trouv\u00e9 r\u00e9cursivement dans le r\u00e9pertoire" + dcmpath)
    return dcmdict


# SLICER
########
					# Importation des images		
  def onImportIm(self) :
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    self.slicerVolumeNode = self.inputSlicer.currentNode()
    d = self.slicerVolumeNode.GetDisplayNode()
    d.SetAutoWindowLevel(0)
    d.SetWindowLevel(350,40)
    redWidget = lm.sliceWidget('Red')
    redWidget.sliceController().setSliceLink(True)
    redWidget.sliceController().setSliceVisible(True)
    threeDWidget = lm.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()
    
    
#######################
# Fonctions pour step 2 : Entourage de la cavite
#######################  
  def setAndObserveParameterNode(self, parameterNode):
    if parameterNode == self.parameterNode and self.parameterNodeObserver:
					# Pas de changement et le noeud est deja observe
      return
					# Enlever observateur au dernier parametre du noeud 
    if self.parameterNode and self.parameterNodeObserver:
      self.parameterNode.RemoveObserver(self.parameterNodeObserver)
      self.parameterNodeObserver = None
					# Charger et observer le nouveau parametre du noeud 
    self.parameterNode = parameterNode
    if self.parameterNode:
      self.parameterNodeObserver = self.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)
					# Mettre a jour GUI
    self.updateGUIFromParameterNode()


  def setAndObserveClippingMarkupNode(self, clippingMarkupNode):
    if clippingMarkupNode == self.clippingMarkupNode and self.clippingMarkupNodeObserver:
					# Pas de changement et le noeud est deja observe
      return
					# Enlever observateur au dernier parametre du noeud 
    if self.clippingMarkupNode and self.clippingMarkupNodeObserver:
      self.clippingMarkupNode.RemoveObserver(self.clippingMarkupNodeObserver)
      self.clippingMarkupNodeObserver = None
					# Charger et observer le nouveau parametre du noeud 
    self.clippingMarkupNode = clippingMarkupNode
    if self.clippingMarkupNode:
      self.clippingMarkupNodeObserver = self.clippingMarkupNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onClippingMarkupNodeModified)
					# Mettre a jour GUI
    self.updateModelFromClippingMarkupNode()
    
    
  def getParameterNode(self):
    return self.parameterNode


  def onClippingMarkupNodeModified(self, observer, eventid):
    self.updateModelFromClippingMarkupNode()
    
    
  def onParameterNodeModified(self, observer, eventid):
    self.updateGUIFromParameterNode()


  def updateModelFromClippingMarkupNode(self):
    if not self.clippingMarkupNode or not self.clippingModelSelector.currentNode():
      return
    self.logic.updateModelFromMarkup(self.clippingMarkupNode, self.clippingModelSelector.currentNode())


  def updateGUIFromParameterNode(self):
    parameterNode = self.getParameterNode()
    if not parameterNode:
      return
    for parameterName in self.valueEditWidgets:
      oldBlockSignalsState = self.valueEditWidgets[parameterName].blockSignals(True)
      widgetClassName = self.valueEditWidgets[parameterName].metaObject().className()      
      if widgetClassName=="QCheckBox":
        checked = ((parameterNode.GetParameter(parameterName)) != 0)
        self.valueEditWidgets[parameterName].setChecked(checked)
      elif widgetClassName=="QSpinBox":
        self.valueEditWidgets[parameterName].setValue(float(parameterNode.GetParameter(parameterName)))
      else:
        raise Exception("Unexpected widget class: {0}".format(widgetClassName))
      self.valueEditWidgets[parameterName].blockSignals(oldBlockSignalsState)
    for parameterName in self.nodeSelectorWidgets:
      oldBlockSignalsState = self.nodeSelectorWidgets[parameterName].blockSignals(True)
      self.nodeSelectorWidgets[parameterName].setCurrentNodeID(parameterNode.GetNodeReferenceID(parameterName))
      self.nodeSelectorWidgets[parameterName].blockSignals(oldBlockSignalsState)


  def updateParameterNodeFromGUI(self):
    parameterNode = self.getParameterNode()
    oldModifiedState = parameterNode.StartModify()
    for parameterName in self.valueEditWidgets:
      widgetClassName = self.valueEditWidgets[parameterName].metaObject().className()      
      if widgetClassName=="QCheckBox":
        if self.valueEditWidgets[parameterName].checked:
          parameterNode.SetParameter(parameterName, "1")
        else:
          parameterNode.SetParameter(parameterName, "0")
      elif widgetClassName=="QSpinBox":
        parameterNode.SetParameter(parameterName, str(self.valueEditWidgets[parameterName].value))
      else:
        raise Exception("Unexpected widget class: {0}".format(widgetClassName))
    for parameterName in self.nodeSelectorWidgets:
      parameterNode.SetNodeReferenceID(parameterName, self.nodeSelectorWidgets[parameterName].currentNodeID)
    parameterNode.EndModify(oldModifiedState)


  def addGUIObservers(self):
    for parameterName in self.valueEditWidgets:
      widgetClassName = self.valueEditWidgets[parameterName].metaObject().className()      
      if widgetClassName=="QSpinBox":
        self.valueEditWidgets[parameterName].connect("valueChanged(int)", self.updateParameterNodeFromGUI)
      elif widgetClassName=="QCheckBox":
        self.valueEditWidgets[parameterName].connect("clicked()", self.updateParameterNodeFromGUI)
    for parameterName in self.nodeSelectorWidgets:
      self.nodeSelectorWidgets[parameterName].connect("currentNodeIDChanged(QString)", self.updateParameterNodeFromGUI)


  def removeGUIObservers(self):
    for parameterName in self.valueEditWidgets:
      widgetClassName = self.valueEditWidgets[parameterName].metaObject().className()      
      if widgetClassName=="QSpinBox":
        self.valueEditWidgets[parameterName].disconnect("valueChanged(int)", self.updateParameterNodeFromGUI)
      elif widgetClassName=="QCheckBox":
        self.valueEditWidgets[parameterName].disconnect("clicked()", self.updateParameterNodeFromGUI)
    for parameterName in self.nodeSelectorWidgets:
      self.nodeSelectorWidgets[parameterName].disconnect("currentNodeIDChanged(QString)", self.updateParameterNodeFromGUI)
      
      
					# Mise a jour du bouton execution
  def updateApplyButtonState(self):
    if not self.inputVolumeSelector.currentNode():
      self.applyButton.toolTip = u"Volume d\u00b4entr\u00e9e n\u00e9cessaire. Volume de rognage avec mod\u00e8le de surface est d\u00e9sactiv\u00e9."
      self.applyButton.enabled = False
    elif not self.clippingModelSelector.currentNode():
      self.applyButton.toolTip = u"Surface de rognage est n\u00e9cessaire (cr\u00e9er un nouveau mod\u00e8le ou s\u00e9lectionner un existant). Volume de rognage avec mod\u00e8le de surface est d\u00e9sactiv\u00e9."
      self.applyButton.enabled = False
    elif not self.outputVolumeSelector.currentNode():
      self.applyButton.toolTip = u"Output volume is required (cr\u00e9er un nouveau volume ou s\u00e9lectionner un existant). Volume de rognage avec mod\u00e8le de surface est d\u00e9sactiv\u00e9."
      self.applyButton.enabled = False
    else:
      self.applyButton.toolTip = u"Volume de rognage avec mod\u00e8le de surface."
      self.applyButton.enabled = True
      
      
  def onInputVolumeSelect(self, node):
    self.updateApplyButtonState()


  def onClippingModelSelect(self, node):
    self.updateApplyButtonState()


  def onClippingMarkupSelect(self, node):
    placeModePersistence = 1
    slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
    if self.clippingMarkupSelector.currentNode() :
      prompt = ctk.ctkMessageBox()
      prompt.setWindowTitle("Ajouter des points")
      prompt.setIcon(qt.QMessageBox.Information)
      prompt.setText(u"Cliquer pour s\u00e9lectionner une zone sur diff\u00e9rentes vues et diff\u00e9rentes coupes")
      prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
      prompt.setDefaultButton(qt.QMessageBox.Ok)
      answer = prompt.exec_()
      if answer == qt.QMessageBox.Cancel:
          logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
          return   
    self.setAndObserveClippingMarkupNode(self.clippingMarkupSelector.currentNode())
    

  def onOutputVolumeSelect(self, node):
    self.updateApplyButtonState()    
    
  def onApplyButton(self):
    self.applyButton.text = "Working..."
    self.applyButton.repaint()
    inputVolume = self.inputVolumeSelector.currentNode()
    outputVolume = self.outputVolumeSelector.currentNode()
    clippingModel = self.clippingModelSelector.currentNode()
    clipOutsideSurface = self.clipOutsideSurfaceCheckBox.checked
    fillValue = self.fillValueEdit.value
    outputVolume = self.logic.clipVolumeWithModel(inputVolume, clippingModel, clipOutsideSurface, fillValue, outputVolume)
    			# Affichage 
    lm = slicer.app.layoutManager()
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
					# Setup background volume
      compositeNode.SetBackgroundVolumeID(self.masterVolumeNode.GetID())
					# Setup foreground volume
      compositeNode.SetForegroundVolumeID(outputVolume.GetID())
					# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)
    self.applyButton.text = u"Ex\u00e9cuter"
    annotationFoie = slicer.mrmlScene.GetFirstNodeByName('A')
    annotationFoie.SetDisplayVisibility(0)
    self.cleanup()
   
#######################
# Fonctions pour step 3 : Calcul du volume de la cavite abdominale
#######################
  def onGrayscaleSelect(self, node):
    self.grayscaleNode = node
    self.applyButton9.enabled = bool(self.grayscaleNode) and bool(self.labelNode)


  def onLabelSelect(self):
    volumesLogic = slicer.modules.volumes.logic()
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    if self.labelSelector.currentNode():
      inputVolume = self.inputVolumeSelector.currentNode()
      outputVolume = self.outputVolumeSelector.currentNode()
      clippingModel = self.clippingModelSelector.currentNode()
      clipOutsideSurface = self.clipOutsideSurfaceCheckBox.checked
      fillValue = self.fillValueEdit.value
      volextract2 = self.logic.clipVolumeWithModel(inputVolume, clippingModel, clipOutsideSurface, fillValue, outputVolume)
    
      volamodif = slicer.util.arrayFromVolume(volextract2)
      volumeLogic = slicer.modules.volumes.logic()
      outfin = volumeLogic.CloneVolume(slicer.mrmlScene, volextract2, 'Volume Final')
      vshape = tuple(reversed(volamodif.shape))
      vcomponents = 1
      vimage = outfin.GetImageData()
    
      volvol = np.array(volamodif)
      volvol[volvol != 0] = 1
      volvol[volvol == 0] = 0

      vtype = vtk.util.numpy_support.get_vtk_array_type(volvol.dtype)
      vimage.SetDimensions(vshape)
      vimage.AllocateScalars(vtype, vcomponents)
      narrayTarget = slicer.util.arrayFromVolume(outfin)
      narrayTarget[:] = volvol
			
      vollabel= volumesLogic.CreateAndAddLabelVolume(slicer.mrmlScene, outfin, "cavite_label" )
      self.labelNode = volumesLogic.CreateLabelVolumeFromVolume(slicer.mrmlScene, vollabel, outfin)
      self.applyButton9.enabled = bool(self.grayscaleNode) and bool(self.labelNode)


  def onApplyButton9(self):
    """Calculate the label statistics
    """ 
    self.applyButton9.text = "Working..."
    self.applyButton9.repaint()
    slicer.app.processEvents()
    
    			# Affichage 
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    
					# Resample the label to the space of the grayscale if needed
    volumesLogic = slicer.modules.volumes.logic()
    warnings = volumesLogic.CheckForLabelVolumeValidity(self.grayscaleNode, self.labelNode)
    resampledLabelNode = None
 
    if warnings != "":
      if 'mismatch' in warnings:
        resampledLabelNode = volumesLogic.ResampleVolumeToReferenceVolume(self.labelNode, self.grayscaleNode)
					# ResampledLabelNode does not have a display node, therefore the colorNode has to be passed to it
        self.logicvol = LabelStatLogic(self.grayscaleNode, resampledLabelNode, colorNode=self.labelNode.GetDisplayNode().GetColorNode(), nodeBaseName=self.labelNode.GetName())
      else:
        slicer.util.warningDisplay(u"Les volumes n\u00b4ont pas la m\u00eame g\u00e9om\u00e9trie.\n%s" % warnings, windowTitle="Label Statistics")
        return
    else:
      self.logicvol = LabelStatLogic(self.grayscaleNode, self.labelNode)
    self.populateStats()
    if resampledLabelNode:
      slicer.mrmlScene.RemoveNode(resampledLabelNode)
    self.exportToTableButton.enabled = True
    self.applyButton9.text = u"Ex\u00e9cuter la Volum\u00e9trie de la Cavit\u00e9"


					# Fonction d'exportation
  def onExportToTable(self):
    """write the label statistics to a table node
    """
    table = self.logicvol.exportToTable()
					# Add table to the scene and show it
    slicer.mrmlScene.AddNode(table)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView)
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(table.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()


					# Fonction de sauvegarde des resultats
  def onSave(self):
    """save the label statistics
    """
    if not self.fileDialog:
      self.fileDialog = qt.QFileDialog(self.parent)
      self.fileDialog.options = self.fileDialog.DontUseNativeDialog
      self.fileDialog.acceptMode = self.fileDialog.AcceptSave
      self.fileDialog.defaultSuffix = "csv"
      self.fileDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.fileDialog.connect("fileSelected(QString)", self.onFileSelected)
    self.fileDialog.show()


  def onFileSelected(self,fileName):
    self.logicvol.saveStats(fileName)


  def populateStats(self):
    if not self.logicvol:
      return
    displayNode = self.labelNode.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    row = 0
    for i in self.logicvol.labelStats["Labels"]:
      col = 0
      color = qt.QColor()
      rgb = lut.GetTableValue(i)
      color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
      item = qt.QStandardItem()
      item.setData(color,qt.Qt.DecorationRole)
      item.setToolTip(colorNode.GetColorName(i))
      item.setEditable(False)
      self.model.setItem(row,col,item)
      self.items.append(item)
      col += 1
      
      item = qt.QStandardItem()
      item.setData(colorNode.GetColorName(i),qt.Qt.DisplayRole)
      item.setEditable(False)
      self.model.setItem(row,col,item)
      self.items.append(item)
      col += 1
      for k in self.logicvol.keys:
        item = qt.QStandardItem()
					# Set data as float with Qt::DisplayRole
        item.setData(float(self.logicvol.labelStats[i,k]),qt.Qt.DisplayRole)
        item.setToolTip(colorNode.GetColorName(i))
        item.setEditable(False)
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1
    self.view.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    self.model.setHeaderData(1,1,"Type")
    col = 2
    for k in self.logicvol.keys:
      self.view.setColumnWidth(col,19*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1
 

#######################
# Fonctions pour step 4 : Calcul des distances dans la cavite abdominale
####################### 
# VUE CORONALE
##############
  def onSetupButtoncor(self):
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
            			# Affichage 
    lm = slicer.app.layoutManager()
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
					# Setup background volume
					# Setup foreground volume
      compositeNode.SetForegroundVolumeID(self.masterVolumeNode.GetID())
					# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)
      
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'Cavite.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Calcul de distances")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText("Choisir 2 points sur la coupe coronale puis cliquer sur \"%s\"" % self.applyButtoncor.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return   
    #self.addLogcor('COUPE CORONALE')

    self.DistancecorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Coupe Coronale")
    self.DistancecorNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onSeedSelectdistcor)
    self.DistancecorNode.GetDisplayNode().SetSelectedColor(0,0.8,0.2)
    placeModePersistence = 1
    slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
    self.pointSelectorcor.setCurrentNode(self.DistancecorNode)
        
    self.tmpNodesdistcor = [self.DistancecorNode]
  
  
  def onSeedSelectdistcor(self, caller, event):
    if self.DistancecorNode :
      self.applyButtoncor.enabled = self.DistancecorNode.GetNumberOfMarkups()
    else:
	    self.applyButtoncor.enabled = False
	   
	   
  def onApplyButtoncor(self):  
    self.applyButtoncor.text = "Working..."
    self.applyButtoncor.repaint()
    slicer.app.processEvents()
    positionfinaledistcor = self.addSeedCoordsdistcor(self.DistancecorNode, self.masterVolumeNode)
    self.applyButtoncor.text = "Calculer la distance"
    self.cleanup()
   
   
  def addSeedCoordsdistcor(self, fidNode, masterVolumeNode):
    seed = fidNode.GetName()
    if seed not in self.seedCoordsdistcor:
      self.seedCoordsdistcor[seed] = []
    fidList = slicer.util.getNode('Coupe Coronale')
    for n in range(fidList.GetNumberOfMarkups()):
				posE = [0,0,0,0]
				posS = [0,0,0,0]
				fidList.GetNthFiducialWorldCoordinates(0,posE)
				fidList.GetNthFiducialWorldCoordinates(n,posS)
				#ruler = slicer.mrmlScene.AddNode(slicer.vtkMRMLAnnotationRulerNode())		
				#ruler.SetPosition2(posS[0],posS[1],posS[2])			
				volumeNode = masterVolumeNode
				mat = vtk.vtkMatrix4x4()
				volumeNode.GetRASToIJKMatrix(mat)
						# Multiplie la matrice de transformation par le tableau de coordonnees RAS 
						#(autrement dit convertit les coordonnees RAS de pos en coordonnees IJK)
				poscorE = [int(round(c)) for c in mat.MultiplyFloatPoint(posE)[:3]]
				poscorS = [int(round(c)) for c in mat.MultiplyFloatPoint(posS)[:3]]
    print('Point 1 longueur : ', posE)
    print('Point 2 longueur : ', posS)
    rulerLengthMm = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(poscorE[0:3],poscorS[0:3]))
    print('La longueur maximale est de :', rulerLengthMm, 'mm')			

    #self.addLogcor("Position point 1 : {0}".format(posE))
    #self.addLogcor("Position point 2 : {0}".format(posS))
    #self.addLogcor("Position convertie point 1 : {0}".format(poscorE))
    #self.addLogcor("Position convertie point 2 : {0}".format(poscorS))
    self.addLogcor("La longueur maximale est de {0} mm".format(rulerLengthMm))   
    self.addLogcor('')

    
# VUE SAGITTALE
###############
  def onSetupButtonsag(self):
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'Cavite.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Calcul de distances")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText("Choisir deux points sur la coupe sagittale puis cliquer sur \"%s\"" % self.applyButtonsag.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return   
    #self.addLogsag('COUPE SAGITTALE')

    self.DistancesagNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Coupe Sagittale")
    self.DistancesagNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onSeedSelectdistsag)
    placeModePersistence = 1
    slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
    self.DistancesagNode.GetDisplayNode().SetSelectedColor(1,0,0)
    self.pointSelectorsag.setCurrentNode(self.DistancesagNode)
   
    self.tmpNodesdistsag = [self.DistancesagNode]
  
  
  def onSeedSelectdistsag(self, caller, event):
    if self.DistancesagNode:
      self.applyButtonsag.enabled = self.DistancesagNode.GetNumberOfMarkups()
    else:
	    self.applyButtonsag.enabled = False
	   
	   
  def onApplyButtonsag(self):  
    self.logic = CaviteLogic()
    positionfinaledistsag = self.addSeedCoordsdistsag(self.DistancesagNode, self.masterVolumeNode)
    self.cleanup()
   
   
  def addSeedCoordsdistsag(self, fidNode, masterVolumeNode):
    seed = fidNode.GetName()
    if seed not in self.seedCoordsdistsag:
      self.seedCoordsdistsag[seed] = []
    fidList = slicer.util.getNode('Coupe Sagittale')
    for n in range(fidList.GetNumberOfMarkups()):
				posE = [0,0,0,0]
				posS = [0,0,0,0]
				fidList.GetNthFiducialWorldCoordinates(0,posE)
				fidList.GetNthFiducialWorldCoordinates(n,posS)
				#ruler = slicer.mrmlScene.AddNode(slicer.vtkMRMLAnnotationRulerNode())		
				#ruler.SetPosition2(posS[0],posS[1],posS[2])		
				volumeNode = masterVolumeNode
 				mat = vtk.vtkMatrix4x4()
				volumeNode.GetRASToIJKMatrix(mat)
				possagE = [int(round(c)) for c in mat.MultiplyFloatPoint(posE)[:3]]
				possagS = [int(round(c)) for c in mat.MultiplyFloatPoint(posS)[:3]]	
    print('Point 1 longueur : ', posE)
    print('Point 2 longueur : ', posS)
    rulerLengthMm = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(possagE[0:3],possagS[0:3]))
    print('La longueur maximale est de :', rulerLengthMm, 'mm')			
 
    #self.addLogsag("Position point 1 : {0}".format(posE))
    #self.addLogsag("Position convertie point 1 : {0}".format(possagE))
    #self.addLogsag("Position point 2 : {0}".format(posS))
    #self.addLogsag("Position convertie point 1 : {0}".format(possagS))
    self.addLogsag("La longueur maximale est de {0} mm".format(rulerLengthMm))  
    self.addLogsag('')
   

# VUE AXIALE
############
  def onSetupButtonax(self):
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'Cavite.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Calcul de distances")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText("Choisir deux points sur la coupe axiale puis cliquer sur \"%s\"" % self.applyButtonax.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return   
    #self.addLogax('COUPE AXIALE')

    self.DistanceaxNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Coupe Axiale")
    self.DistanceaxNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onSeedSelectdistax)
    placeModePersistence = 1
    slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
    self.DistanceaxNode.GetDisplayNode().SetSelectedColor(1,0,1)
    self.pointSelectorax.setCurrentNode(self.DistanceaxNode)
    
    self.tmpNodesdist = [self.DistanceaxNode]
  
  
  def onSeedSelectdistax(self, caller, event):
    if self.DistanceaxNode :
      self.applyButtonax.enabled = self.DistanceaxNode.GetNumberOfMarkups() 
    else:
	    self.applyButtonax.enabled = False
	   
	   
  def onApplyButtonax(self):  
    self.logic = CaviteLogic()
    positionfinaledistax = self.addSeedCoordsdistax(self.DistanceaxNode, self.masterVolumeNode)
    self.cleanup()
   
   
  def addSeedCoordsdistax(self, fidNode, masterVolumeNode):
    seed = fidNode.GetName()
    if seed not in self.seedCoordsdistax:
      self.seedCoordsdistax[seed] = []
    fidList = slicer.util.getNode('Coupe Axiale')
    for n in range(fidList.GetNumberOfMarkups()):
				posE = [0,0,0,0]
				posS = [0,0,0,0]
				fidList.GetNthFiducialWorldCoordinates(0,posE)
				fidList.GetNthFiducialWorldCoordinates(n,posS)
				#ruler = slicer.mrmlScene.AddNode(slicer.vtkMRMLAnnotationRulerNode())		
				#ruler.SetPosition2(posS[0],posS[1],posS[2])			
				volumeNode = masterVolumeNode
				mat = vtk.vtkMatrix4x4()
				volumeNode.GetRASToIJKMatrix(mat)
				posaxE = [int(round(c)) for c in mat.MultiplyFloatPoint(posE)[:3]]
				posaxS = [int(round(c)) for c in mat.MultiplyFloatPoint(posS)[:3]]
    print('Point 1 longueur : ', posE)
    print('Point 2 longueur : ', posS)
    rulerLengthMm = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(posaxE[0:3],posaxS[0:3]))
    print('La longueur maximale est de :', rulerLengthMm, 'mm')		
	
    #self.addLogax("Position point 1 : {0}".format(posE))
    #self.addLogax("Position point 2 : {0}".format(posS))
    #self.addLogax("Position convertie point 1 : {0}".format(posaxE))
    #self.addLogax("Position convertie point 2 : {0}".format(posaxS))
    self.addLogax("La longueur maximale est de {0} mm".format(rulerLengthMm))   
    self.addLogax('')
    
     
  def addLogcor(self, text):
    """Append text to log window
    """
    self.statusLabelcor.appendPlainText(text)
    slicer.app.processEvents() # force update


  def addLogsag(self, text):
    self.statusLabelsag.appendPlainText(text)
    slicer.app.processEvents()


  def addLogax(self, text):
    self.statusLabelax.appendPlainText(text)
    slicer.app.processEvents()



#################################################
# CaviteLogic - INTERFACE FONCTIONNELLE : CALCULS
#################################################

class CaviteLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  
  def __init__(self, parent = None):
     ScriptedLoadableModuleLogic.__init__(self, parent)
     self.logCallback = None


  def addLogcor(self, text):
    logging.info(text)
    if self.logCallback:
      self.logCallback(text)


  def addLogsag(self, text):
    logging.info(text)
    if self.logCallback:
      self.logCallback(text)
   
   
  def addLogax(self, text):
    logging.info(text)
    if self.logCallback:
      self.logCallback(text)  
      
      
  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True


  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

#######################
# Fonctions pour step 2 : SELECTION DU VOLUME A ANALYSER
#######################
  def createParameterNode(self):
					# Set default parameters
    node = ScriptedLoadableModuleLogic.createParameterNode(self)
    node.SetName(slicer.mrmlScene.GetUniqueNameByString(self.moduleName))
    node.SetParameter("RognerHorsSurface", "1")
    node.SetParameter("ValeurRemplissage", "0")
    return node


  def clipVolumeWithModel(self, inputVolume, clippingModel, clipOutsideSurface, fillValue, outputVolume):
    """
    Fill voxels of the input volume inside/outside the clipping model with the provided fill value
    """
					# Determine the transform between the box and the image IJK coordinate systems
    rasToModel = vtk.vtkMatrix4x4()    
      
    ijkToRas = vtk.vtkMatrix4x4()
    inputVolume.GetIJKToRASMatrix(ijkToRas)

    ijkToModel = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Multiply4x4(rasToModel,ijkToRas,ijkToModel)
    modelToIjkTransform = vtk.vtkTransform()
    modelToIjkTransform.SetMatrix(ijkToModel)
    modelToIjkTransform.Inverse()
    
    transformModelToIjk=vtk.vtkTransformPolyDataFilter()
    transformModelToIjk.SetTransform(modelToIjkTransform)
    transformModelToIjk.SetInputConnection(clippingModel.GetPolyDataConnection())

					# Use the stencil to fill the volume
					# Convert model to stencil
    polyToStencil = vtk.vtkPolyDataToImageStencil()
    polyToStencil.SetInputConnection(transformModelToIjk.GetOutputPort())
    polyToStencil.SetOutputSpacing(inputVolume.GetImageData().GetSpacing())
    polyToStencil.SetOutputOrigin(inputVolume.GetImageData().GetOrigin())
    polyToStencil.SetOutputWholeExtent(inputVolume.GetImageData().GetExtent())
			
					# Apply the stencil to the volume
    stencilToImage=vtk.vtkImageStencil()
    stencilToImage.SetInputConnection(inputVolume.GetImageDataConnection())
    stencilToImage.SetStencilConnection(polyToStencil.GetOutputPort())
    if clipOutsideSurface:
      stencilToImage.ReverseStencilOff()
    else:
      stencilToImage.ReverseStencilOn()
    stencilToImage.SetBackgroundValue(fillValue)
    stencilToImage.Update()

					# Update the volume with the stencil operation result
    outputImageData = vtk.vtkImageData()
    outputImageData.DeepCopy(stencilToImage.GetOutput())
    
    outputVolume.SetAndObserveImageData(outputImageData);
    outputVolume.SetIJKToRASMatrix(ijkToRas)

					# Add a default display node to output volume node if it does not exist yet
    if not outputVolume.GetDisplayNode:
      displayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
      displayNode.SetAndObserveColorNodeID("vtkMRMLColorTableNodeGrey")
      slicer.mrmlScene.AddNode(displayNode)
      outputVolume.SetAndObserveDisplayNodeID(displayNode.GetID())
      
					# Sauvegarde du volume dans un fichier NIFTI
    c = slicer.util.arrayFromVolume(outputVolume)
    volumeLogic = slicer.modules.volumes.logic()
    outfoie = volumeLogic.CloneVolume(slicer.mrmlScene, outputVolume, 'VolumeCavite')
    vshape = tuple(reversed(c.shape))
    vcomponents = 1
    vimage = outfoie.GetImageData()
		
    ouverture = np.array(c)
    ouverture[c!=0]=255
    ouverture[c==0]=0
    vtype = vtk.util.numpy_support.get_vtk_array_type(ouverture.dtype)
    vimage.SetDimensions(vshape)
    vimage.AllocateScalars(vtype, vcomponents)
    narrayTarget = slicer.util.arrayFromVolume(outfoie)
    narrayTarget[:] = ouverture
    outfoie.StorableModified()
    outfoie.Modified()
    outfoie.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, outputVolume)

    slicer.util.saveNode(outfoie, '~\Documents\TroisDSlicer\CaviteAbdoReceveur.nii')
    filename = os.path.join(os.path.expanduser("~"),'\Documents\TroisDSlicer\CaviteAbdoReceveurData')
    slicer.util.saveScene(filename)
    return outfoie


  def updateModelFromMarkup(self, inputMarkup, outputModel):
    """
    Update model to enclose all points in the input markup list
    """
					# Delaunay triangulation is robust and creates nice smooth surfaces from a small number of points,
					# however it can only generate convex surfaces robustly.
    useDelaunay = True
    
					# Create polydata point set from markup points
    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    
    numberOfPoints = inputMarkup.GetNumberOfFiducials()
    
					# Surface generation algorithms behave unpredictably when there are not enough points
					# return if there are very few points
    if useDelaunay:
      if numberOfPoints<3:
        return
    else:
      if numberOfPoints<10:
        return

    points.SetNumberOfPoints(numberOfPoints)
    new_coord = [0.0, 0.0, 0.0]

    for i in range(numberOfPoints):
      inputMarkup.GetNthFiducialPosition(i,new_coord)
      points.SetPoint(i, new_coord)

    cellArray.InsertNextCell(numberOfPoints)
    for i in range(numberOfPoints):
      cellArray.InsertCellPoint(i)

    pointPolyData = vtk.vtkPolyData()
    pointPolyData.SetLines(cellArray)
    pointPolyData.SetPoints(points)
    
					# Create surface from point set
    if useDelaunay:
      delaunay = vtk.vtkDelaunay3D()
      delaunay.SetInputData(pointPolyData)

      surfaceFilter = vtk.vtkDataSetSurfaceFilter()
      surfaceFilter.SetInputConnection(delaunay.GetOutputPort())

      smoother = vtk.vtkButterflySubdivisionFilter()
      smoother.SetInputConnection(surfaceFilter.GetOutputPort())
      smoother.SetNumberOfSubdivisions(3)
      smoother.Update()

      outputModel.SetPolyDataConnection(smoother.GetOutputPort())
      
    else:
      surf = vtk.vtkSurfaceReconstructionFilter()
      surf.SetInputData(pointPolyData)
      surf.SetNeighborhoodSize(20)
      surf.SetSampleSpacing(80) # lower value follows the small details more closely but more dense pointset is needed as input

      cf = vtk.vtkContourFilter()
      cf.SetInputConnection(surf.GetOutputPort())
      cf.SetValue(0, 0.0)

					# Sometimes the contouring algorithm can create a volume whose gradient
					# vector and ordering of polygon (using the right hand rule) are
					# inconsistent. vtkReverseSense cures this problem.
      reverse = vtk.vtkReverseSense()
      reverse.SetInputConnection(cf.GetOutputPort())
      reverse.ReverseCellsOff()
      reverse.ReverseNormalsOff()

      outputModel.SetPolyDataConnection(reverse.GetOutputPort())

					# Create default model display node if does not exist yet
    if not outputModel.GetDisplayNode():
      modelDisplayNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelDisplayNode")
      modelDisplayNode.SetColor(0,0,1) # Blue
      modelDisplayNode.BackfaceCullingOff()
      modelDisplayNode.SliceIntersectionVisibilityOn()
      modelDisplayNode.SetOpacity(0.9) # Between 0-1, 1 being opaque
      slicer.mrmlScene.AddNode(modelDisplayNode)
      outputModel.SetAndObserveDisplayNodeID(modelDisplayNode.GetID())
  
    outputModel.GetDisplayNode().SliceIntersectionVisibilityOn()
    outputModel.Modified()
    outputModel.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, inputMarkup)

    return outputModel


     
###################
# Fonction step 3 : CALCULER LE VOLUME DE LA CAVITE
###################
class LabelStatLogic(ScriptedLoadableModuleLogic):
  def __init__(self, grayscaleNode, labelNode, colorNode=None, nodeBaseName=None, fileName=None):  
    self.keys = ("Index", "Comptage", "Volume mm^3", "Volume cc", "Minimum", "Maximum", "Moyenne", "Mediane", "StdDev")
   
    cubicMMPerVoxel = reduce(lambda x,y: x*y, labelNode.GetSpacing())
    ccPerCubicMM = 0.001
		  
    self.labelNode = labelNode
    self.colorNode = colorNode
    self.nodeBaseName = nodeBaseName
       
    if not self.nodeBaseName:
      self.nodeBaseName = labelNode.GetName() if labelNode.GetName() else 'Labels'
    self.labelStats = {}
    self.labelStats['Labels'] = []

    stataccum = vtk.vtkImageAccumulate()
    stataccum.SetInputConnection(labelNode.GetImageDataConnection())
    stataccum.Update()
    lo = int(stataccum.GetMin()[0])
    hi = int(stataccum.GetMax()[0])

    for i in xrange(lo,hi+1):
						# Logic copied from slicer3 LabelStatistics to create the binary volume of the label
      thresholder = vtk.vtkImageThreshold()
      thresholder.SetInputConnection(labelNode.GetImageDataConnection())
      thresholder.SetInValue(1)
      thresholder.SetOutValue(0)
      thresholder.ReplaceOutOn()
      thresholder.ThresholdBetween(i,i)
      thresholder.SetOutputScalarType(grayscaleNode.GetImageData().GetScalarType())
      thresholder.Update()

						# Use vtk's statistics class with the binary labelmap as a stencil
      stencil = vtk.vtkImageToImageStencil()
      stencil.SetInputConnection(thresholder.GetOutputPort())
      stencil.ThresholdBetween(1, 1)

      stat1 = vtk.vtkImageAccumulate()
      stat1.SetInputConnection(grayscaleNode.GetImageDataConnection())
      stencil.Update()
      stat1.SetStencilData(stencil.GetOutput())
      stat1.Update()

      medians = vtk.vtkImageHistogramStatistics()
      medians.SetInputConnection(grayscaleNode.GetImageDataConnection())
      stencil.Update()
      medians.SetStencilData(stencil.GetOutput())
      medians.Update()

      if stat1.GetVoxelCount() > 0:
						# Add an entry to the LabelStats list
        self.labelStats["Labels"].append(i)
        self.labelStats[i,"Index"] = i
        self.labelStats[i,"Comptage"] = round(stat1.GetVoxelCount(),3)
        self.labelStats[i,"Volume mm^3"] = round(self.labelStats[i,"Comptage"] * cubicMMPerVoxel,3)
        self.labelStats[i,"Volume cc"] = self.labelStats[i,"Volume mm^3"] * ccPerCubicMM
        self.labelStats[i,"Minimum"] = stat1.GetMin()[0]
        self.labelStats[i,"Maximum"] = stat1.GetMax()[0]
        self.labelStats[i,"Moyenne"] = round(stat1.GetMean()[0],3)
        self.labelStats[i,"Mediane"] = round(medians.GetMedian(),3)
        self.labelStats[i,"StdDev"] = round(stat1.GetStandardDeviation()[0],3)
   
   
  def getColorNode(self):
    """Returns the color node corresponding to the labelmap. If a color node is explicitly
    specified then that will be used. Otherwise the color node is retrieved from the display node
    of the labelmap node
    """
    if self.colorNode:
      return self.colorNode
    displayNode = self.labelNode.GetDisplayNode()
    if not displayNode:
      return None
    return displayNode.GetColorNode()


  def exportToTable(self):
    """
    Export statistics to table node
    """    
    colorNode = self.getColorNode()
    table = slicer.vtkMRMLTableNode()
    tableWasModified = table.StartModify()
    table.SetName(slicer.mrmlScene.GenerateUniqueName(self.nodeBaseName + ' statistics'))

						# Define table columns
    if colorNode:
      col = table.AddColumn()
      col.SetName("Type")
    for k in self.keys:
      col = table.AddColumn()
      col.SetName(k)
    for i in self.labelStats["Labels"]:
      rowIndex = table.AddEmptyRow()
      columnIndex = 0
      if colorNode:
        table.SetCellText(rowIndex, columnIndex, colorNode.GetColorName(i))
        columnIndex += 1
						# Add other values
      for k in self.keys:
        table.SetCellText(rowIndex, columnIndex, str(self.labelStats[i, k]))
        columnIndex += 1
    table.EndModify(tableWasModified)
    return table


  def statsAsCSV(self):
    """
    print comma separated value file with header keys in quotes
    """
    colorNode = self.getColorNode()  
    csv = ""
    header = ""
    if colorNode:
      header += "\"%s\"" % "Type" + ","
    for k in self.keys[:-1]:
      header += "\"%s\"" % k + ","
    header += "\"%s\"" % self.keys[-1] + "\n"
    csv = header
    for i in self.labelStats["Labels"]:
      line = ""
      if colorNode:
        line += colorNode.GetColorName(i) + ","
      for k in self.keys[:-1]:
        line += str(self.labelStats[i,k]) + ","
      line += str(self.labelStats[i,self.keys[-1]]) + "\n"
      csv += line
    return csv


  def saveStats(self,fileName):
    fp = open(fileName, "w")
    fp.write(self.statsAsCSV())
    fp.close()



#############
# CLASSE TEST
#############
   
class CaviteTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)


  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Cavite1()


  def test_Cavite1(self):
    self.delayDisplay("Starting the test")
    self.delayDisplay('Test passed !')







    


