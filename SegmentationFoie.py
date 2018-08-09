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
from PythonQt import QtGui, QtCore
from PythonQt.QtGui import *
from PythonQt.QtCore import *
import scipy
from scipy import signal
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
import itk
import math
import string
import sys
import vtkSegmentationCorePython as vtkSegmentationCore
from ctk import ctkDICOMObjectListWidget, ctkDICOMDatabase, ctkDICOMIndexer, ctkDICOMBrowser, ctkPopupWidget, ctkExpandButton
from scipy.spatial import distance

# -*- coding: utf-8 -*-

#########
# SegmentationFoie
#########

class SegmentationFoie(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Etapes de la segmentation du foie"
    self.parent.categories = ["Pour le DONNEUR : Segmentation semi-automatique du foie"]
    self.parent.dependencies = []
    self.parent.contributors = ["Laura Seimpere"]
    self.parent.helpText = u"""
Segmentation du foie du donneur par une succession d'\u00e9tapes; obtention des distances principales et du volume du foie segment\u00e9 par la m\u00e9thode; comparaison avec le volume r\u00e9f\u00e9rence du m\u00eame foie segment\u00e9 'parfaitement' pour quantifier la fiabilit\u00e9 du module cr\u00e9\u00e9.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
"""  


#Pour ecrire un e accent aigu u"\u00e9" ; pour a accent aigu \u00e0; pour e accent grave \u00e8


#####################################
# SegmentationFoieWidget - INTERFACE GRAPHIQUE
#####################################

class SegmentationFoieWidget(ScriptedLoadableModuleWidget):
					# Initialisation
  def __init__(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.logic = SegmentationFoieLogic()
    self.logic.logCallback = self.addLog
    self.logic.logCallbackhisto = self.addLoghisto
    self.logic.logCallbackextract = self.addLogextract
    self.logic.logCallbackdistauto = self.addLogdistauto
    self.logic.logCallbackdistclic = self.addLogdistclic
    self.logic.logCallbackValid = self.addLogValid
    self.parameterNode = None
   
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
					# Pour calcul du volume
    self.logicvol = None
    self.logicvolref = None
    self.grayscaleNode = None
    self.labelNode = None
    self.fileName = None
    self.fileDialog = None

					# Instantiate and connect widgets ...
					# Cadre general
    self.step0CollapsibleButton = ctk.ctkCollapsibleButton()
    self.step0CollapsibleButton.text = "Donneur : Segmentation du foie"
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
    self.loadDicomsButton.toolTip = "Importer et charger les images."
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
    # Step 2 : Estimation du bruit dans le foie
	  #########
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = u"Etape 2 : Calcul de sigma sur une zone homog\u00e8ne (\u00e9tape optionnelle !)"
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
   
					# ROI selector
    self.clippingRoiSelectorLabel = qt.QLabel()
    self.clippingRoiSelectorLabel.setText( u"  R\u00e9gion d\u00b4int\u00e9r\u00eat \u00e0 rogner :            " )
    self.clippingRoiSelector = slicer.qMRMLNodeComboBox()
    self.clippingRoiSelector.nodeTypes = ( "vtkMRMLAnnotationROINode", "" )
    self.clippingRoiSelector.noneEnabled = False
    self.clippingRoiSelector.selectNodeUponCreation = True
    self.clippingRoiSelector.setMRMLScene( slicer.mrmlScene )
    self.clippingRoiSelector.setToolTip( u"Choisir la r\u00e9gion d\u00b4int\u00e9r\u00eat \u00e0 rogner (ROI)." )
    parametersFormLayout.addRow(self.clippingRoiSelectorLabel, self.clippingRoiSelector)
    self.clippingRoiSelector.setMaximumWidth(250)

					# Clip inside / outside the surface
    self.clipOutsideSurfaceCheckBox = qt.QCheckBox()
    self.clipOutsideSurfaceCheckBox.checked = False
    self.clipOutsideSurfaceCheckBox.setToolTip(u"Si coch\u00e9, les valeurs de voxels seront remplies hors de la r\u00e9gion ROI.")
    parametersFormLayout.addRow(u"  Rognage ext\u00e9rieur :            ", self.clipOutsideSurfaceCheckBox)
    
					# Output volume selector
    self.outputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.outputVolumeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputVolumeSelector.selectNodeUponCreation = True
    self.outputVolumeSelector.addEnabled = True
    self.outputVolumeSelector.removeEnabled = True
    self.outputVolumeSelector.noneEnabled = False
    self.outputVolumeSelector.showHidden = False
    self.outputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.outputVolumeSelector.setToolTip( u"Volume de sortie rogn\u00e9. Il peut \u00eatre le m\u00eame que celui d\u00b4entr\u00e9e pour un rognage cumul\u00e9." )
    self.outputVolumeSelector.setMaximumWidth(250)
    parametersFormLayout.addRow("  Volume de sortie :            ", self.outputVolumeSelector)

					# Apply button step 2 
    self.applyButton = qt.QPushButton(u"Ex\u00e9cuter le rognage")
    self.applyButton.toolTip = "Rogner le volume avec ROI."
    parametersFormLayout.addRow(self.applyButton)
    self.applyButton.setMaximumWidth(350)
    self.updateApplyButtonState()

    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    parametersFormLayout.addRow(self.inputDistLabel)
    
					# Box des resultats
    self.statusLabel = qt.QPlainTextEdit()
    parametersFormLayout.addRow(self.statusLabel)

					# Espace pour une meilleure visibilite dans l'affichage    
    self.inputDistLabel = qt.QLabel("")
    parametersFormLayout.addRow(self.inputDistLabel)
    
    
	  #########
    # Step 3 : Filtrage
	  #########
    step03CollapsibleButton = ctk.ctkCollapsibleButton()
    step03CollapsibleButton.text = "Etape 3 : Filtrage"
    self.layout.addWidget(step03CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step03CollapsibleButton)

					# Filtres selector
    self.filtreMedian = qt.QRadioButton(u"Filtre m\u00e9dian (en moyenne, taille du rayon = 3)   ")
    self.filtreMedian1 = qt.QComboBox()
    self.filtreMedian1.addItem("1",0)
    self.filtreMedian1.addItem("2",1)
    self.filtreMedian1.addItem("3",2)
    self.filtreMedian1.addItem("4",3)
    self.filtreMedian1.addItem("5",4)
    self.filtreMedian1.addItem("6",5)
    self.filtreMedian1.addItem("7",6)

    self.filtreGaussian = qt.QRadioButton(u"Filtre gaussien (en moyenne, valeur de l'\u00e9cart-type = 3)   ")
    self.filtreGaussian2 = qt.QComboBox()
    self.filtreGaussian2.addItem("1",0)
    self.filtreGaussian2.addItem("2",1)
    self.filtreGaussian2.addItem("3",2)
    self.filtreGaussian2.addItem("4",3)
    self.filtreGaussian2.addItem("5",4)
    self.filtreGaussian2.addItem("6",5)
    self.filtreGaussian2.addItem("7",6)
    
    self.filtreGaussian.checked = True
		
    stepsFormLayout.addRow(self.filtreMedian, self.filtreMedian1)
    stepsFormLayout.addRow(self.filtreGaussian, self.filtreGaussian2)
    self.filtreMedian1.setMaximumWidth(44)
    self.filtreGaussian2.setMaximumWidth(44)
 
					# Apply button step 3
    self.applyButton3 = qt.QPushButton(u"Ex\u00e9cuter le filtrage")
    self.applyButton3.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton3.setMaximumWidth(350)
    self.applyButton3.enabled = False
    stepsFormLayout.addRow(self.applyButton3)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    
	  #########
    # Step 4 : Histogramme et seuillage
	  #########
    step04CollapsibleButton = ctk.ctkCollapsibleButton()
    step04CollapsibleButton.text = "Etape 4 : Histogramme et seuillage"
    self.layout.addWidget(step04CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step04CollapsibleButton)

					# Setup Button
    self.setupButtonhisto = qt.QPushButton(u"Configurer l\u00b4histogramme")
    self.setupButtonhisto.toolTip = u"Configurer l\u00b4algorithme."
    self.setupButtonhisto.enabled = False
    self.setupButtonhisto.setMaximumWidth(350)
    stepsFormLayout.addRow(self.setupButtonhisto)
    
    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    stepsFormLayout.addRow(self.inputDistLabel)
    
					# Box des resultats
    self.statusLabelhisto = qt.QPlainTextEdit()
    stepsFormLayout.addRow(self.statusLabelhisto)
    
					# Threshold value
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = 0
    self.imageThresholdSliderWidget.maximum = 110
    self.imageThresholdSliderWidget.value = 50
    self.imageThresholdSliderWidget.setToolTip(u"R\u00e9gler la valeur du seuil pour l\u00b4image de sortie. Les voxels d\u00b4intensit\u00e9s inf\u00e9rieures \u00e0 ce seuil seront mis \u00e0 0.")
    self.inputDistLabel = qt.QLabel(u"  Bornes \u00e0 s\u00e9lectionner :")
    stepsFormLayout.addRow(self.inputDistLabel)
    stepsFormLayout.addRow("  Avant le pic du foie", self.imageThresholdSliderWidget)

    self.imageThresholdSliderWidget2 = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget2.singleStep = 0.1
    self.imageThresholdSliderWidget2.minimum = 0
    self.imageThresholdSliderWidget2.maximum = 110
    self.imageThresholdSliderWidget2.value = 50
    self.imageThresholdSliderWidget2.setToolTip(u"R\u00e9gler la valeur du seuil pour l\u00b4image de sortie. Les voxels d\u00b4intensit\u00e9s inf\u00e9rieures \u00e0 ce seuil seront mis \u00e0 0.")
    stepsFormLayout.addRow(u"  Apr\u00e8s le pic du foie", self.imageThresholdSliderWidget2)

					# Apply button step 4
    self.applyButton4 = qt.QPushButton(u"Ex\u00e9cuter l\u00b4histogramme et le seuillage")
    self.applyButton4.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton4.setMaximumWidth(350)
    self.applyButton4.enabled = False
    stepsFormLayout.addRow(self.applyButton4)
				
					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    
	  #########
    # Step 5 : Operations de morphologie mathematique
	  #########
    step05CollapsibleButton = ctk.ctkCollapsibleButton()
    step05CollapsibleButton.text = u"Etape 5 : Op\u00e9rations de morphologie math\u00e9matique"
    self.layout.addWidget(step05CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step05CollapsibleButton)

					# Input volume selector
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip(u"Choisir l\u00b4entr\u00e9e de l\u00b4algorithme." )
    self.inputSelector.setMaximumWidth(250)
    stepsFormLayout.addRow(u"  Volume d\u00b4entr\u00e9e :                        ", self.inputSelector)
    
					# Choix des operations de morphologie mathematique
    self.opening = qt.QRadioButton("Ouverture            ")
    self.elemstruc = qt.QComboBox()
    self.inputDistLabel = qt.QLabel(u"  Taille de l\u00b4\u00e9l\u00e9ment structurant : ")
    self.elemstruc.addItem("2",1)
    self.elemstruc.addItem("3",2)
    self.elemstruc.addItem("4",3)
    self.elemstruc.addItem("5",4)
    self.elemstruc.addItem("6",5)
    self.elemstruc.addItem("7",6)
    self.elemstruc.addItem("8",7)
    self.elemstruc.addItem("9",8)
    self.elemstruc.addItem("10",9)
    self.dilate = qt.QRadioButton("Dilatation            ")
    self.erosion = qt.QRadioButton("Erosion")
    self.closing = qt.QRadioButton("Fermeture")
    self.remp = qt.QRadioButton("Remplisage des trous")
    self.opening.checked = True
    stepsFormLayout.addRow(self.inputDistLabel, self.elemstruc)
    stepsFormLayout.addRow(self.opening, self.closing)
    self.elemstruc.setMaximumWidth(44)
    stepsFormLayout.addRow(self.dilate, self.erosion)
    stepsFormLayout.addRow(self.remp)
     
					# Apply button step 5
    self.applyButton5 = qt.QPushButton(u"Ex\u00e9cuter l\u00b4op\u00e9ration de morphologie math\u00e9matique")
    self.applyButton5.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton5.setMaximumWidth(350)
    self.applyButton5.enabled = False
    stepsFormLayout.addRow(self.applyButton5)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    
	  #########
    # Step 6 : Extraction des composantes connexes
	  #########
    step06CollapsibleButton = ctk.ctkCollapsibleButton()
    step06CollapsibleButton.text = "Etape 6 : Extraction de la composante connexe du foie"
    self.layout.addWidget(step06CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step06CollapsibleButton)
    self.seedCoords = {}

					# Input volume selector
    self.inputSelectorextrac = slicer.qMRMLNodeComboBox()
    self.inputSelectorextrac.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelectorextrac.selectNodeUponCreation = True
    self.inputSelectorextrac.addEnabled = False
    self.inputSelectorextrac.removeEnabled = False
    self.inputSelectorextrac.noneEnabled = False
    self.inputSelectorextrac.showHidden = False
    self.inputSelectorextrac.showChildNodeTypes = False
    self.inputSelectorextrac.setMRMLScene( slicer.mrmlScene )
    self.inputSelectorextrac.setToolTip(u"Choisir l\u00b4entr\u00e9e de l\u00b4algorithme." )
    self.inputSelectorextrac.setMaximumWidth(250)
    stepsFormLayout.addRow(u"  Volume d\u00b4entr\u00e9e :                        ", self.inputSelectorextrac)
    
					# Setup Button
    self.setupButton = qt.QPushButton(u"Configurer l\u00b4extraction du foie")
    self.setupButton.toolTip = u"Configurer l\u00b4algorithme."
    self.setupButton.enabled = False
    self.setupButton.setMaximumWidth(350)
    stepsFormLayout.addRow(self.setupButton)
    
					# Seed selector = Selectionner le foie sur l'image
    self.pointSelector = slicer.qSlicerSimpleMarkupsWidget()
    self.pointSelector.objectName = u'pointS\u00e9lecteur'
    self.pointSelector.toolTip = u"S\u00e9lectionner un point."
    self.pointSelector.defaultNodeColor = qt.QColor(0,255,0)
    self.pointSelector.tableWidget().hide()
    self.pointSelector.markupsSelectorComboBox().noneEnabled = False
    self.pointSelector.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup    
    self.pointSelector.markupsPlaceWidget().buttonsVisible = False
    self.pointSelector.markupsPlaceWidget().placeButton().show()
    self.pointSelector.setMRMLScene(slicer.mrmlScene)

    self.pointBox = qt.QHBoxLayout()
    self.pointLabelWidget = qt.QLabel("  Choisir un point :                        ")
    self.pointBox.addWidget(self.pointLabelWidget)
    self.pointBox.addWidget(self.pointSelector)
    self.pointSelector.setMaximumWidth(250)
    stepsFormLayout.addRow(self.pointLabelWidget, self.pointSelector)
    
					# Apply button step 6
    self.applyButton6 = qt.QPushButton(u"Ex\u00e9cuter l\u00b4extraction")
    self.applyButton6.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton6.setMaximumWidth(350)
    self.applyButton6.enabled = False
    stepsFormLayout.addRow(self.applyButton6)
    
    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    stepsFormLayout.addRow(self.inputDistLabel)
    
					# Box des resultats
    self.statusLabelextract = qt.QPlainTextEdit()
    stepsFormLayout.addRow(self.statusLabelextract)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    
	  #########
    # Step 7 : Fermeture morphologique
	  #########
    step07CollapsibleButton = ctk.ctkCollapsibleButton()
    step07CollapsibleButton.text = u"Etape 7 : Op\u00e9rations de morphologie math\u00e9matique pour affiner la segmentation"
    self.layout.addWidget(step07CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step07CollapsibleButton)
    
					# Input volume selector
    self.inputSelector2 = slicer.qMRMLNodeComboBox()
    self.inputSelector2.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector2.selectNodeUponCreation = True
    self.inputSelector2.addEnabled = False
    self.inputSelector2.removeEnabled = False
    self.inputSelector2.noneEnabled = False
    self.inputSelector2.showHidden = False
    self.inputSelector2.showChildNodeTypes = False
    self.inputSelector2.setMRMLScene( slicer.mrmlScene )
    self.inputSelector2.setToolTip(u"Choisir l\u00b4entr\u00e9e de l\u00b4algorithme." )
    self.inputSelector2.setMaximumWidth(250)
    stepsFormLayout.addRow(u"  Volume d\u00b4entr\u00e9e :                        ", self.inputSelector2)

					# Choix des operations de morphologie mathematique
    self.opening2 = qt.QRadioButton("Ouverture")
    self.elemstruc2 = qt.QComboBox()
    self.inputDistLabel = qt.QLabel(u"  Taille de l\u00b4\u00e9l\u00e9ment structurant : ")
    self.elemstruc2.addItem("2",1)
    self.elemstruc2.addItem("3",2)
    self.elemstruc2.addItem("4",3)
    self.elemstruc2.addItem("5",4)
    self.elemstruc2.addItem("6",5)
    self.elemstruc2.addItem("7",6)
    self.elemstruc2.addItem("8",7)
    self.elemstruc2.addItem("9",8)
    self.elemstruc2.addItem("10",9)
    self.dilate2 = qt.QRadioButton("Dilatation")
    self.erosion2 = qt.QRadioButton("Erosion")
    self.closingfinal = qt.QRadioButton("Fermeture")
    self.remp2 = qt.QRadioButton("Remplisage des trous")
    self.closingfinal.checked = True
    self.elemstruc2.setMaximumWidth(44)
    stepsFormLayout.addRow(self.inputDistLabel, self.elemstruc2)
    stepsFormLayout.addRow(self.opening2, self.closingfinal)
    stepsFormLayout.addRow(self.dilate2, self.erosion2)
    stepsFormLayout.addRow(self.remp2)

					# Apply button step 7
    self.applyButton7 = qt.QPushButton(u"Ex\u00e9cuter la segmentation finale")
    self.applyButton7.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton7.setMaximumWidth(350)
    self.applyButton7.enabled = False
    stepsFormLayout.addRow(self.applyButton7)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)

					# Apply button step 7 bis
    self.applyCorrFin = qt.QPushButton("Correction de la segmentation du foie")
    self.applyCorrFin.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyCorrFin.setMinimumWidth(350)
    self.applyCorrFin.enabled = False

					# Apply button step 7 ter
    self.applyCorrfinie = qt.QPushButton(u"R\u00e9sultat de la segmentation du foie")
    self.applyCorrfinie.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyCorrfinie.setMaximumWidth(350)
    self.applyCorrfinie.enabled = False
    stepsFormLayout.addRow(self.applyCorrFin, self.applyCorrfinie)
    
					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    
    #########
    # Step 8 : Calcul de la distance entre deux points sur le foie
	  #########
    step08CollapsibleButton = ctk.ctkCollapsibleButton()
    step08CollapsibleButton.text = "Etape 8 : Calcul de la distance entre deux points sur le foie"
    self.layout.addWidget(step08CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step08CollapsibleButton)
    
    self.inputDistLabel = qt.QLabel("  OPTION 1 : Distances automatiques du foie")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    			# Apply button step 8-1
    self.applyButton81 = qt.QPushButton("Calculer les distances automatiques")
    self.applyButton81.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton81.setMaximumWidth(350)
    self.applyButton81.enabled = False
    stepsFormLayout.addRow(self.applyButton81)
    
    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    stepsFormLayout.addRow(self.inputDistLabel)
    
					# Box des resultats
    self.statusLabeldistauto = qt.QPlainTextEdit()
    stepsFormLayout.addRow(self.statusLabeldistauto)
    
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    self.inputDistLabel = qt.QLabel("  OPTION 2 : Distances manuelles du foie")
    stepsFormLayout.addRow(self.inputDistLabel)
    self.seedCoordsdist = {}

					# Setup Button
    self.setupButton8 = qt.QPushButton("Configurer les distances manuelles")
    self.setupButton8.toolTip = u"Configurer l\u00b4algorithme."
    self.setupButton8.enabled = False
    self.setupButton8.setMaximumWidth(350)
    stepsFormLayout.addRow(self.setupButton8)
    
					# Seed selector
    self.pointSelector8 = slicer.qSlicerSimpleMarkupsWidget()
    self.pointSelector8.objectName = u'pointS\u00e9lector'
    self.pointSelector8.toolTip = u"S\u00e9lectionner un point."
    self.pointSelector8.defaultNodeColor = qt.QColor(0,255,0)
    self.pointSelector8.tableWidget().hide()
    self.pointSelector8.markupsSelectorComboBox().noneEnabled = False
    self.pointSelector8.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup    
    self.pointSelector8.markupsPlaceWidget().buttonsVisible = True
    self.pointSelector8.markupsPlaceWidget().placeButton().show()
    self.pointSelector8.setMRMLScene(slicer.mrmlScene)

    self.pointBox8 = qt.QHBoxLayout()
    self.pointLabelWidget8 = qt.QLabel("  Choisir une distance :                    ")
    self.pointBox8.addWidget(self.pointLabelWidget8)
    self.pointBox8.addWidget(self.pointSelector8)
    self.pointSelector8.setMaximumWidth(340)
    stepsFormLayout.addRow(self.pointLabelWidget8, self.pointSelector8)
    
					# Apply button step 8-2
    self.applyButton82 = qt.QPushButton("Calculer les distances manuelles")
    self.applyButton82.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton82.setMaximumWidth(350)
    self.applyButton82.enabled = False
    stepsFormLayout.addRow(self.applyButton82)

    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    stepsFormLayout.addRow(self.inputDistLabel)
    
					# Box des resultats
    self.statusLabeldistclic = qt.QPlainTextEdit()
    stepsFormLayout.addRow(self.statusLabeldistclic)
    
					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    
    #########
    # Step 9 : Calcul du volume du foie
	  #########
    step09CollapsibleButton = ctk.ctkCollapsibleButton()
    step09CollapsibleButton.text = "Etape 9 : Calcul du volume du foie"
    self.layout.addWidget(step09CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step09CollapsibleButton)

					# Grayscale volume selector
    self.grayscaleSelectorFrame = qt.QFrame(self.parent)
    self.grayscaleSelectorFrame.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.grayscaleSelectorFrame)

    self.grayscaleSelectorLabel = qt.QLabel("  Volume en niveaux de gris :        ", self.grayscaleSelectorFrame)
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
    self.labelSelectorLabel.setText("  Carte des labels :                          ")
    self.labelSelectorFrame.layout().addWidget(self.labelSelectorLabel)
    self.labelSelector = slicer.qMRMLNodeComboBox()
    self.labelSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.labelSelector.selectNodeUponCreation = False
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
    self.applyButton9 = qt.QPushButton(u"Ex\u00e9cuter la Volum\u00e9trie de la Segmentation")
    self.applyButton9.toolTip = "Calculer les statistiques."
    self.applyButton9.enabled = False
    self.applyButton9.setMaximumWidth(350)
    self.parent.layout().addWidget(self.applyButton9)

    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    self.parent.layout().addWidget(self.inputDistLabel)
    
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
    # Step 10 : Validation quantitative des resultats de la segmentation
	  #########
    step10CollapsibleButton = ctk.ctkCollapsibleButton()
    step10CollapsibleButton.text = u"Etape 10 : Validation quantitative des r\u00e9sultats de la segmentation"
    self.layout.addWidget(step10CollapsibleButton)
    stepsFormLayout = qt.QFormLayout(step10CollapsibleButton)

					# Chargement avec dossier DICOM
					# Bouton de chargement par DICOM mis sur True
    self.loadFromDicomRef = qt.QRadioButton(u"Charger le foie r\u00e9f\u00e9rent (V\u00e9rit\u00e9 Terrain) :")
    self.loadFromDicomRef.checked = True
          # Zone de recherche du repertoire contenant les images a traiter
    self.inputDicomSelectorRef = ctk.ctkDirectoryButton()
    self.inputDicomSelectorRef.caption = u'Entr\u00e9es DICOM'
    self.inputDicomSelectorRef.directory = os.path.join(os.path.expanduser("~"),"Documents/TroisDSlicer/VeriteTerrainDonneursPietro/")
    self.inputDicomSelectorRef.setMaximumWidth(450)
          # Bouton d'importation des images
    self.loadDicomsButtonRef = qt.QPushButton("Importer et charger")
    self.dicomVolumeNodeRef = None
    self.importDicomLayoutRef = qt.QHBoxLayout()
    self.loadDicomsButtonRef.setMaximumWidth(300)
    self.importDicomLayoutRef.addWidget(self.inputDicomSelectorRef, 9)
    self.importDicomLayoutRef.addWidget(self.loadDicomsButtonRef, 1)
    stepsFormLayout.addRow(self.loadFromDicomRef, self.importDicomLayoutRef)
    
					# Grayscale volume selector
    self.grayscaleSelectorFrame10 = qt.QFrame(self.parent)
    self.grayscaleSelectorFrame10.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.grayscaleSelectorFrame10)

    self.grayscaleSelectorLabel10 = qt.QLabel("  Volume en niveaux de gris :        ", self.grayscaleSelectorFrame10)
    self.grayscaleSelectorLabel10.setToolTip( u"S\u00e9lectionner le volume en niveaux de gris (scalar volume node en arri\u00e8re plan en niveaux de gris) pour les calculs statistiques.")
    self.grayscaleSelectorFrame10.layout().addWidget(self.grayscaleSelectorLabel10)

    self.grayscaleSelector10 = slicer.qMRMLNodeComboBox(self.grayscaleSelectorFrame10)
    self.grayscaleSelector10.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.grayscaleSelector10.selectNodeUponCreation = False
    self.grayscaleSelector10.addEnabled = False
    self.grayscaleSelector10.removeEnabled = False
    self.grayscaleSelector10.noneEnabled = False
    self.grayscaleSelector10.showHidden = False
    self.grayscaleSelector10.showChildNodeTypes = False
    self.grayscaleSelectorFrame10.setMaximumWidth(450)
    self.grayscaleSelector10.setMRMLScene(slicer.mrmlScene)
    self.grayscaleSelectorFrame10.layout().addWidget(self.grayscaleSelector10)
    
					# Label volume selector
    self.labelSelectorFrame10 = qt.QFrame()
    self.labelSelectorFrame10.setLayout(qt.QHBoxLayout())
    self.parent.layout().addWidget(self.labelSelectorFrame10)
    self.labelSelectorLabel10 = qt.QLabel()
    self.labelSelectorLabel10.setText("  Carte des labels :                      ")
    self.labelSelectorFrame10.layout().addWidget(self.labelSelectorLabel10)
    self.labelSelector10 = slicer.qMRMLNodeComboBox()
    self.labelSelector10.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.labelSelector10.selectNodeUponCreation = False
    self.labelSelector10.addEnabled = True
    self.labelSelector10.noneEnabled = False
    self.labelSelector10.removeEnabled = False
    self.labelSelector10.showHidden = False
    self.labelSelector10.showChildNodeTypes = False
    self.labelSelector10.setMRMLScene(slicer.mrmlScene)
    self.labelSelectorFrame10.setMaximumWidth(440)
    self.labelSelector10.setToolTip(u"Choisir la carte des labels \u00e0 \u00e9diter.")
    self.labelSelectorFrame10.layout().addWidget(self.labelSelector10)

					# Apply Button step 9
    self.applyButton10 = qt.QPushButton(u"Ex\u00e9cuter la Volum\u00e9trie de la Segmentation de R\u00e9f\u00e9rence")
    self.applyButton10.toolTip = "Calculer les statistiques."
    self.applyButton10.enabled = False
    self.applyButton10.setMaximumWidth(400)
    self.parent.layout().addWidget(self.applyButton10)

    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    self.parent.layout().addWidget(self.inputDistLabel)
    
					# Model and view for stats table
    self.view10 = qt.QTableView()
    self.view10.sortingEnabled = True
    self.parent.layout().addWidget(self.view10)
       
					# Save button
    self.exportToTableButton10 = qt.QPushButton("Exporter en tableau")
    self.exportToTableButton10.toolTip = "Exporter les statistiques en tableau."
    self.exportToTableButton10.enabled = False
    self.parent.layout().addWidget(self.exportToTableButton10)

					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.parent.layout().addWidget(self.inputDistLabel)
    
        	# Setup Button
    self.setupButtonValid = qt.QPushButton(u"Configurer la volum\u00e9trie")
    self.setupButtonValid.toolTip = u"Configurer l\u00b4algorithme."
    self.setupButtonValid.enabled = False
    self.setupButtonValid.setMaximumWidth(350)
    self.parent.layout().addWidget(self.setupButtonValid)
    
    self.inputDistLabel = qt.QLabel(u"  R\u00e9sultats : ")
    self.parent.layout().addWidget(self.inputDistLabel)
    
					# Box des resultats
    self.statusLabelValid = qt.QPlainTextEdit()
    self.parent.layout().addWidget(self.statusLabelValid)
    
					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    self.parent.layout().addWidget(self.inputDistLabel)
    self.inputDistLabel = qt.QLabel("")
    self.parent.layout().addWidget(self.inputDistLabel)
    

	  #############
    # Connections
    #############
    self.loadFromDicom.connect("clicked(bool)", self.onSelect)
    self.loadDicomsButton.connect("clicked(bool)", self.onDicomImportClicked)
    self.loadDicomsButton.connect("clicked(bool)", self.onSelect)
    self.loadFromSlicer.connect("clicked(bool)", self.onSlicer)
    self.importim.connect('clicked()', self.onImportIm)
    self.inputSlicer.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    self.applyButton.connect("clicked(bool)", self.onApply)
    self.clippingRoiSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onClippingRoiSelect)
    self.outputVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onOutputVolumeSelect)

    self.filtreMedian.connect("clicked(bool)", self.onSelect)
    self.filtreGaussian.connect("clicked(bool)", self.onSelect)
    self.applyButton3.connect('clicked()', self.onApplyButton)

    self.setupButtonhisto.connect('clicked()', self.onSetupButtonhisto)
    self.applyButton4.connect('clicked()', self.onApplyButtonHisto)

    self.opening.connect("clicked(bool)", self.onSelect)
    self.dilate.connect("clicked(bool)", self.onSelect)
    self.erosion.connect("clicked(bool)", self.onSelect)
    self.closing.connect("clicked(bool)", self.onSelect)
    self.remp.connect("clicked(bool)", self.onSelect)
    self.applyButton5.connect('clicked(bool)', self.onApplyButtonOpMorpho)

    self.setupButton.connect('clicked()', self.onSetupButton)
    self.applyButton6.connect('clicked()', self.onApplyButtonExtract)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.pointSelector, 'setMRMLScene(vtkMRMLScene*)')
    
    self.opening2.connect("clicked(bool)", self.onSelect)
    self.dilate2.connect("clicked(bool)", self.onSelect)
    self.erosion2.connect("clicked(bool)", self.onSelect)
    self.closingfinal.connect("clicked(bool)", self.onSelect)
    self.remp2.connect("clicked(bool)", self.onSelect)
    self.applyButton7.connect('clicked(bool)', self.onApplyButtonClosing)
    self.applyCorrFin.connect('clicked(bool)', self.onApplyCorr)
    self.applyCorrfinie.connect('clicked(bool)', self.onApplyCorrfinie)
    
    self.applyButton81.connect('clicked(bool)', self.onApplyButton81)
    self.setupButton8.connect('clicked(bool)', self.onSetupButton8)
    self.applyButton82.connect('clicked(bool)', self.onApplyButton82)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.pointSelector8, 'setMRMLScene(vtkMRMLScene*)')
   
    self.applyButton9.connect('clicked(bool)', self.onApplyButton9)
    self.exportToTableButton.connect('clicked(bool)', self.onExportToTable)
    self.grayscaleSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onGrayscaleSelect)
    self.labelSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect)

    self.loadFromDicomRef.connect("clicked(bool)", self.onSelect)
    self.loadDicomsButtonRef.connect("clicked(bool)", self.onDicomImportClickedRef)
    self.loadDicomsButtonRef.connect("clicked(bool)", self.onSelect)
    self.grayscaleSelector10.connect('currentNodeChanged(vtkMRMLNode*)', self.onRefSelect)
    self.setupButtonValid.connect('clicked()', self.onSetupButtonValid)
    self.applyButton10.connect('clicked(bool)', self.onApplyButton10)
    self.exportToTableButton10.connect('clicked(bool)', self.onExportToTable10)
    self.labelSelector10.connect('currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect10)   
    

    self.tmpNodes = []
    self.tmpNodesvol = []
    self.tmpNodesdist = []
    
					# Pour le crop
					# Define list of widgets for updateGUIFromParameterNode, updateParameterNodeFromGUI, and addGUIObservers
    self.valueEditWidgets = {"RognerHorsSurface": self.clipOutsideSurfaceCheckBox}
    self.nodeSelectorWidgets = {"RognageROI": self.clippingRoiSelector, "VolumedeSortie": self.outputVolumeSelector}
					# Use singleton parameter node (it is created if does not exist yet)
    parameterNode = self.logic.getParameterNode()
					# Set parameter node (widget will observe it and also updates GUI)
    self.setAndObserveParameterNode(parameterNode)
    self.addGUIObservers()
        
					# Add vertical spacer
    self.layout.addStretch(1)   

					# Refresh Apply button state
    self.onSelect()


  def cleanup(self):
    pass


  def onSelect(self):
    if self.loadFromDicom.checked:
      self.masterVolumeNode = self.dicomVolumeNode 
    if self.loadFromSlicer.checked:
      self.masterVolumeNode = self.inputSlicer.currentNode()
    if self.loadFromDicomRef.checked:
      self.refmaster = self.dicomVolumeNodeRef

    self.applyButton.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton3.enabled = self.filtreGaussian and self.filtreMedian and self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton4.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonhisto.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton5.enabled = self.opening and self.erosion and self.dilate and self.closing and self.remp and self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton6.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton7.enabled = self.opening2 and self.erosion2 and self.dilate2 and self.closingfinal and self.remp2 and self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyCorrFin.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyCorrfinie.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButton.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButton8.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton81.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton82.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton9.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonValid.enabled = self.refmaster and slicer.mrmlScene.GetNodeByID(self.refmaster.GetID()) 
    self.applyButton10.enabled = self.masterVolumeNode and self.refmaster and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID()) and slicer.mrmlScene.GetNodeByID(self.refmaster.GetID())

  
  def onSlicer(self):
    if self.loadFromSlicer.checked:  
      reformatModuleWidget = slicer.modules.dicom.createNewWidgetRepresentation()
      reformatModuleWidget.setMRMLScene(slicer.app.mrmlScene())
      reformatModuleWidget.show() 
      self.masterVolumeNode = self.inputSlicer.currentNode() 

      prompt = ctk.ctkMessageBox()
      scriptpath = os.path.dirname(__file__)
      iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
      iconpath = iconpath.replace('\\', '/')
      icon = qt.QIcon(iconpath)
      prompt.setWindowIcon(icon)
      prompt.setWindowTitle("Charger les images")
      prompt.setIcon(qt.QMessageBox.Information)
      prompt.setText("Parcourir les images dans Show DICOM Browser, les importer en cliquant sur \"Load\" puis les charger en cliquant sur \"%s\"" % self.importim.text)
      prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
      prompt.setDefaultButton(qt.QMessageBox.Ok)
      answer = prompt.exec_()
      if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return 
		
    self.applyButton.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton3.enabled = self.filtreGaussian and self.filtreMedian and self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton4.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonhisto.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton5.enabled = self.opening and self.erosion and self.dilate and self.closing and self.remp and self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton6.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton7.enabled = self.opening2 and self.erosion2 and self.dilate2 and self.closingfinal and self.remp2 and self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyCorrFin.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyCorrfinie.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButton.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButton8.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton81.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton82.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.applyButton9.enabled = self.masterVolumeNode and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID())
    self.setupButtonValid.enabled = self.refmaster and slicer.mrmlScene.GetNodeByID(self.refmaster.GetID())
    self.applyButton10.enabled = self.masterVolumeNode and self.refmaster and slicer.mrmlScene.GetNodeByID(self.masterVolumeNode.GetID()) and slicer.mrmlScene.GetNodeByID(self.refmaster.GetID())

    

#######################
# FONCTIONS POUR ETAPES
#######################   
#######################
# Fonctions pour step 1 : Charger images
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
        iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
        iconpath = iconpath.replace('\\', '/')
        icon = qt.QIcon(iconpath)
        diag.setWindowIcon(icon)
        ok = PythonQt.BoolResult()
        sn = qt.QInputDialog.getItem(diag, "Choisir le Volume", u"Choisir le num\u00e9ro de s\u00e9ries :", keys, 0, False, ok)
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
# Fonctions pour step 2 : Estimation du bruit dans le foie par crop
#######################
  def setAndObserveParameterNode(self, parameterNode):
    if parameterNode == self.parameterNode and self.parameterNodeObserver:
					# No change and node is already observed
      return
					# Remove observer to old parameter node
    if self.parameterNode and self.parameterNodeObserver:
      self.parameterNode.RemoveObserver(self.parameterNodeObserver)
      self.parameterNodeObserver = None
					# Set and observe new parameter node
    self.parameterNode = parameterNode
    if self.parameterNode:
      self.parameterNodeObserver = self.parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)
					# Update GUI
    self.updateGUIFromParameterNode()


  def getParameterNode(self):
    return self.parameterNode


  def onParameterNodeModified(self, observer, eventid):
    self.updateGUIFromParameterNode()


  def updateGUIFromParameterNode(self):
    parameterNode = self.getParameterNode()
    for parameterName in self.valueEditWidgets:
      oldBlockSignalsState = self.valueEditWidgets[parameterName].blockSignals(True)
      widgetClassName = self.valueEditWidgets[parameterName].metaObject().className()      
      if widgetClassName=="QCheckBox":
        checked = ((parameterNode.GetParameter(parameterName)) != 0)
        self.valueEditWidgets[parameterName].setChecked(checked)
      elif widgetClassName=="QSpinBox" or widgetClassName=="QDoubleSpinBox":
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
      elif widgetClassName=="QSpinBox" or widgetClassName=="QDoubleSpinBox":
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
      if widgetClassName=="QDoubleSpinBox":
        self.valueEditWidgets[parameterName].connect("valueChanged(double)", self.updateParameterNodeFromGUI)
      elif widgetClassName=="QCheckBox":
        self.valueEditWidgets[parameterName].connect("clicked()", self.updateParameterNodeFromGUI)
    for parameterName in self.nodeSelectorWidgets:
      self.nodeSelectorWidgets[parameterName].connect("currentNodeIDChanged(QString)", self.updateParameterNodeFromGUI)


  def updateApplyButtonState(self):
    if self.clippingRoiSelector.currentNode() and self.outputVolumeSelector.currentNode():
      self.applyButton.enabled = True
    else:
      self.applyButton.enabled = False      
    
    
  def onClippingRoiSelect(self, node):
    taille = slicer.util.arrayFromVolume(self.masterVolumeNode)
    #print('taille', taille.shape)
    v= taille.shape
    if self.clippingRoiSelector.currentNode():
      self.clippingRoiSelector.currentNode().SetXYZ(-120,-240,140)
      self.clippingRoiSelector.currentNode().SetRadiusXYZ(10.,10.,10.)
    self.updateApplyButtonState()


  def onOutputVolumeSelect(self, node):
    self.updateApplyButtonState()


  def onApply(self):
    self.applyButton.text = "Working..."
    self.applyButton.repaint()
    slicer.app.processEvents()
    clipOutsideSurface = self.clipOutsideSurfaceCheckBox.checked
    clippingRoi = self.clippingRoiSelector.currentNode()
    outputVolume = self.outputVolumeSelector.currentNode()
    self.logic.clipVolumeWithRoi(clippingRoi, self.masterVolumeNode, clipOutsideSurface, outputVolume)
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
    
    annotationROI = slicer.mrmlScene.GetFirstNodeByName('AnnotationROI')
    annotationROI.SetDisplayVisibility(False)
    self.applyButton.text = u"Ex\u00e9cuter le rognage"
    self.cleanup()


#######################
# Fonction pour step 3 : Filtrage
#######################  
  def onApplyButton(self):
    self.applyButton3.text = "Working..."
    self.applyButton3.repaint()
    slicer.app.processEvents()
    size = self.filtreMedian1.itemData(self.filtreMedian1.currentIndex)
    sigma = self.filtreGaussian2.itemData(self.filtreGaussian2.currentIndex)
    self.logic.run(self.masterVolumeNode, self.filtreMedian, self.filtreGaussian, size, sigma)
    self.applyButton3.text = u"Ex\u00e9cuter le filtrage"
    self.cleanup()


#######################
# Fonction pour step 4 : Histogramme et seuillage
#######################    
  def onSetupButtonhisto(self):
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Pic du foie")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText(u"Ajuster les curseurs autour du pic du foie en fonction de la valeur de l\u00b4indice affich\u00e9e dans la box des r\u00e9sultats pour un meilleur seuillage puis cliquer sur \"%s\"" % self.applyButton4.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return  
    self.logic.pic(self.masterVolumeNode)


  def onApplyButtonHisto(self):
    self.applyButton4.text = "Working..."
    self.applyButton4.repaint()
    #slicer.app.processEvents()
    imageThreshold = self.imageThresholdSliderWidget.value
    imageThreshold2 = self.imageThresholdSliderWidget2.value
    result = self.logic.histo(self.masterVolumeNode, imageThreshold, imageThreshold2)
    a = result.GetDisplayNode()
    a.SetColor(1,0,0)
    self.applyButton4.text = u"Ex\u00e9cuter l\u00b4histogramme et le seuillage"
    self.cleanup()


#######################
# Fonction pour step 5 : Operations de morphologie mathematique
#######################  
  def onApplyButtonOpMorpho(self):
    self.applyButton5.text = "Working..."
    self.applyButton5.repaint()
    slicer.app.processEvents()
    taille = self.elemstruc.itemData(self.elemstruc.currentIndex)
    inputVolume = self.inputSelector.currentNode()
    self.logic.morpho(self.masterVolumeNode, self.opening, taille, self.dilate, self.erosion, self.closing, self.remp, inputVolume)
    self.applyButton5.text = u"Ex\u00e9cuter l\u00b4op\u00e9ration de morphologie math\u00e9matique"
    self.cleanup()

    
#######################
# Fonctions pour step 6 : Extraction des composantes connexes
#######################
						# Initialisation step 6
  def onSetupButton(self):
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Extraction du foie")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText(u"Pointer le foie avec le marqueur s\u00e9lectionn\u00e9 puis cliquer sur \"%s\"" % self.applyButton6.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return
    self.bgNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Foie")
    self.tmpNodes = [self.bgNode]
    self.bgNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onSeedSelect)
    self.bgNode.GetDisplayNode().SetSelectedColor(1,0,1)
    placeModePersistence = 1
    slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
    self.pointSelector.setCurrentNode(self.bgNode)
    slicer.modules.markups.logic().StartPlaceMode(0)
    self.addLogextract("")
						
						
						# Selection des points
  def onSeedSelect(self, caller, event):
    if self.bgNode:
      self.applyButton6.enabled = self.bgNode.GetNumberOfMarkups()
    else:
	    self.applyButton6.enabled = False
	    
	    
						# Affichage du resultat du calcul
  def onApplyButtonExtract(self):
    self.applyButton6.text = "Working..."
    self.applyButton6.repaint()
    slicer.app.processEvents()
    posIJK = self.addSeedCoords(self.bgNode, self.masterVolumeNode)
    inputVolume = self.inputSelector.currentNode()
    inputVolume2 = self.inputSelectorextrac.currentNode()
    taille = self.elemstruc.itemData(self.elemstruc.currentIndex)
    outmorpho = self.logic.morpho(self.masterVolumeNode, self.opening, taille, self.dilate, self.erosion, self.closing, self.remp, inputVolume)
    self.logic.extractedcomponents(self.masterVolumeNode, self.seedCoords, posIJK, outmorpho, inputVolume2)
    self.applyButton6.text = u"Ex\u00e9cuter l\u00b4extraction"
    annotationFoie = slicer.mrmlScene.GetFirstNodeByName('Foie')
    annotationFoie.SetDisplayVisibility(0)
    self.cleanup()

    
						# Traitement du point selectionne
  def addSeedCoords(self, fidNode, masterVolumeNode):
    seed = fidNode.GetName()
    if seed not in self.seedCoords:
      self.seedCoords[seed] = []
						# Liste des fiducials
    fidList = slicer.util.getNode('Foie')

    for i in range(fidList.GetNumberOfMarkups()):	
						# Stocke dans le tableau 'pos' les coordonnees RAS du ieme fiducial :
      pos = [0,0,0,0]
      fidList.GetNthFiducialWorldCoordinates(i,pos)
      #self.addLogextract(u'Les coordonn\u00e9es du point physique (positions en mm) sont : {0}'.format(pos))
						# Recupere le noeud appele "FOIE"
      volumeNode = masterVolumeNode
						# Initialise une matrice identite en vtk
      mat = vtk.vtkMatrix4x4()
						#	Stocke dans 'mat' la matrice de transformation 
      volumeNode.GetRASToIJKMatrix(mat)
						# Multiplie la matrice de transformation par le tableau de coordonnees RAS 
						#(autrement dit convertit les coordonnees RAS de pos en coordonnees IJK)
      posIJK = [int(round(c)) for c in mat.MultiplyFloatPoint(pos)[:3]]
      #self.addLogextract(u'Les coordonn\u00e9es de la position image sont : {0}'.format(posIJK))
      #self.addLogextract("")
      return posIJK


########################
# Fonctions pour step 7 : Operations de morphologie mathematique finales
########################  
  def onApplyButtonClosing(self):
    self.applyButton7.text = "Working..."
    self.applyButton7.repaint()
    slicer.app.processEvents()
    inputVolumeclose = self.inputSelector2.currentNode()
    taille2 = self.elemstruc2.itemData(self.elemstruc2.currentIndex)
    self.logic.closing(self.masterVolumeNode, self.opening2, taille2, self.dilate2, self.erosion2, self.closingfinal, self.remp2, inputVolumeclose)
    self.applyButton7.text = u"Ex\u00e9cuter la segmentation finale"
    
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Segmentation du foie")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText("Si la segmentation n'est pas satisfaisante, l'affiner en cliquant sur \"%s\"" % self.applyCorrFin.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return  
    self.cleanup()
   
  
						# Fonction d'application du peaufinage de la segmentation par SegmentEditor dans le module Segmentation
  def onApplyCorr(self) :
    self.applyCorrFin.text = "Working..."
    self.applyCorrFin.repaint()
    slicer.app.processEvents()
    inputVolumeclose = self.inputSelector2.currentNode()
    taille2 = self.elemstruc2.itemData(self.elemstruc2.currentIndex)
    inputVolCor = self.logic.closing (self.masterVolumeNode, self.opening2, taille2, self.dilate2, self.erosion2, self.closingfinal, self.remp2, inputVolumeclose)
    self.logic.CorrectionFinale(self.masterVolumeNode, inputVolCor)
    self.applyCorrFin.text = "Correction de la segmentation du foie"
    
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Segmentation du foie")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText(u"Une fois la segmentation satisfaisante, afficher le volume r\u00e9sultant en cliquant sur \"%s\"" % self.applyCorrfinie.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return  
    self.cleanup()


  def onApplyCorrfinie(self) :
    self.applyCorrfinie.text = "Working..."
    self.applyCorrfinie.repaint()
    slicer.app.processEvents()
    #inputVolumeclose = self.inputSelector2.currentNode()
    #inputVolume = self.logic.closing (self.masterVolumeNode, self.opening2, self.dilate2, self.erosion2, self.closingfinal, self.remp2, inputVolumeclose)
    inputVolume = slicer.util.getNode('CorrectionSegmentationFoie')
    self.logic.ExportFinal(self.masterVolumeNode, inputVolume)
    self.applyCorrfinie.text = u"R\u00e9sultat de la segmentation du foie"
    labelmapfoiestep7 = slicer.util.getNode("Labelmap du foie")
    slicer.mrmlScene.RemoveNode(labelmapfoiestep7)
    self.cleanup()
  
  
#######################
# Fonctions pour step 8 : Calcul de la distance entre deux points sur le foie
#######################
# AUTOMATIQUES
#############
  def onApplyButton81(self):  
    self.applyButton81.text = "Working..."
    self.applyButton81.repaint()
    slicer.app.processEvents()
    #inputVolumeclose = self.inputSelector2.currentNode()
    #inputVolume = self.logic.closing (self.masterVolumeNode, self.opening2, self.dilate2, self.erosion2, self.closingfinal, self.remp2, inputVolumeclose)
    outfin = slicer.util.getNode('FoieSegmenteApresCorrection')
    #outfin = self.logic.ExportFinal(self.masterVolumeNode, inputVolume)
    self.logic.autodistance(self.masterVolumeNode, outfin)
    self.applyButton81.text = "Calculer les distances automatiques"
    self.cleanup()
    
    
# MANUELLES
###########
  def onSetupButton8(self):
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    prompt = ctk.ctkMessageBox()
    scriptpath = os.path.dirname(__file__)
    iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
    iconpath = iconpath.replace('\\', '/')
    icon = qt.QIcon(iconpath)
    prompt.setWindowIcon(icon)
    prompt.setWindowTitle("Distances manuelles du foie")
    prompt.setIcon(qt.QMessageBox.Information)
    prompt.setText(u"Choisir deux points sur les diff\u00e9rents plans anatomiques pour calculer des distances comme par exemple, sur la coupe axiale pour la profondeur maximale du foie, sur la coupe sagittale pour la hauteur maximale ou sur la coupe coronale pour la longueur maximale, puis cliquer sur \"%s\"" % self.applyButton82.text)
    prompt.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    prompt.setDefaultButton(qt.QMessageBox.Ok)
    answer = prompt.exec_()
    if answer == qt.QMessageBox.Cancel:
        logging.info(u"Op\u00e9ration annul\u00e9e par l\u00b4utilisateur, fin en cours...")
        return  

    self.Distance1Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Longueur horizontale (coupe coronale)")
    self.Distance1Node.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onSeedSelectdist)
    self.Distance1Node.GetDisplayNode().SetSelectedColor(0,0.8,0.2)
    self.pointSelector8.setCurrentNode(self.Distance1Node)

    self.Distance2Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Hauteur (coupe sagittale)")
    self.Distance2Node.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onSeedSelectdist)
    self.Distance2Node.GetDisplayNode().SetSelectedColor(1,0,0)
    self.pointSelector8.setCurrentNode(self.Distance2Node)

    self.Distance3Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Profondeur (coupe axiale)")
    self.Distance3Node.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onSeedSelectdist)
    self.Distance3Node.GetDisplayNode().SetSelectedColor(1,0,1)   
    placeModePersistence = 1
    slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
    self.pointSelector8.setCurrentNode(self.Distance3Node)

    self.tmpNodesdist = [self.Distance1Node, self.Distance2Node, self.Distance3Node]


  def onSeedSelectdist(self, caller, event):
    if self.Distance1Node and self.Distance3Node and self.Distance2Node :
      self.applyButton82.enabled = self.Distance3Node.GetNumberOfMarkups() and self.Distance2Node.GetNumberOfMarkups() and self.Distance1Node.GetNumberOfMarkups() 
      slicer.modules.markups.logic().StartPlaceMode(1)
    else:
	    self.applyButton82.enabled = False


  def onApplyButton82(self):  
    self.applyButton82.text = "Working..."
    self.applyButton82.repaint()
    slicer.app.processEvents()
    positionfinaledist3 = self.addSeedCoordsdist3(self.Distance3Node, self.masterVolumeNode)
    positionfinaledist2 = self.addSeedCoordsdist2(self.Distance2Node, self.masterVolumeNode)
    positionfinaledist1 = self.addSeedCoordsdist1(self.Distance1Node, self.masterVolumeNode)
    self.applyButton82.text = "Calculer les distances manuelles"
    slicer.modules.markups.logic().StartPlaceMode(0)
    self.cleanup()
   
   
  def addSeedCoordsdist1(self, fidNode, masterVolumeNode):
    seed = fidNode.GetName()
    if seed not in self.seedCoordsdist:
      self.seedCoordsdist[seed] = []
    fidList = slicer.util.getNode('Longueur horizontale (coupe coronale)')
    for n in range(fidList.GetNumberOfMarkups()):
				posE = [0,0,0,0]
				posS = [0,0,0,0]
				fidList.GetNthFiducialWorldCoordinates(0,posE)
				fidList.GetNthFiducialWorldCoordinates(n,posS)
				ruler = slicer.mrmlScene.AddNode(slicer.vtkMRMLAnnotationRulerNode())		
				ruler.SetPosition2(posS[2],posS[1],posS[0])			
				volumeNode = masterVolumeNode
				mat = vtk.vtkMatrix4x4()
				volumeNode.GetRASToIJKMatrix(mat)
						# Multiplie la matrice de transformation par le tableau de coordonnees RAS 
						#(autrement dit convertit les coordonnees RAS de pos en coordonnees IJK)
				poslgrE = [int(round(c)) for c in mat.MultiplyFloatPoint(posE)[:3]]
				poslgrS = [int(round(c)) for c in mat.MultiplyFloatPoint(posS)[:3]]
    
    rulerLengthMm = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(poslgrE[0:3],poslgrS[0:3]))
    #self.addLogdistclic("LONGUEUR HORIZONTALE DU FOIE = x")
    #self.addLogdistclic('PosE : {0}'.format(posE))
    #self.addLogdistclic('PosS : {0}'.format(posS))
    #self.addLogdistclic("Position convertie point 1 : {0}".format(poslgrE))
    #self.addLogdistclic("Position convertie point 2 : {0}".format(poslgrS))
    self.addLogdistclic(u"Longueur horizontale maximale manuelle (gauche \u00e0 droite) : {0} mm".format(rulerLengthMm))   
    #print("Longueur horizontale maximale manuelle (gauche a droite) : {0} mm".format(rulerLengthMm))   
    #self.addLogdistclic("")
    slicer.modules.markups.logic().StartPlaceMode(0)

    
  def addSeedCoordsdist2(self, fidNode, masterVolumeNode):
    seed = fidNode.GetName()
    if seed not in self.seedCoordsdist:
      self.seedCoordsdist[seed] = []
    fidList = slicer.util.getNode('Hauteur (coupe sagittale)')
    for n in range(fidList.GetNumberOfMarkups()):
				posE = [0,0,0,0]
				posS = [0,0,0,0]
				fidList.GetNthFiducialWorldCoordinates(0,posE)
				fidList.GetNthFiducialWorldCoordinates(n,posS)    
				ruler = slicer.mrmlScene.AddNode(slicer.vtkMRMLAnnotationRulerNode())
				ruler.SetPosition2(posS[2],posS[1],posS[0])	
				volumeNode = masterVolumeNode
 				mat = vtk.vtkMatrix4x4()
				volumeNode.GetRASToIJKMatrix(mat)
				poshtrE = [int(round(c)) for c in mat.MultiplyFloatPoint(posE)[:3]]
				poshtrS = [int(round(c)) for c in mat.MultiplyFloatPoint(posS)[:3]]
    
    rulerLengthMm = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(poshtrE[0:3],poshtrS[0:3]))
    #self.addLogdistclic("HAUTEUR DU FOIE = z")
    #self.addLogdistclic('PosE : {0}'.format(posE))
    #self.addLogdistclic('PosS : {0}'.format(posS))
    #self.addLogdistclic("Position convertie point 1 : {0}".format(poshtrE))
    #self.addLogdistclic("Position convertie point 2 : {0}".format(poshtrS))
    self.addLogdistclic(u"Hauteur maximale manuelle (inf\u00e9rieur vers sup\u00e9rieur) : {0} mm".format(rulerLengthMm))   
    #print("Hauteur maximale manuelle (inferieur vers superieur) : {0} mm".format(rulerLengthMm))   
    #self.addLogdistclic("")
    slicer.modules.markups.logic().StartPlaceMode(0)


  def addSeedCoordsdist3(self, fidNode, masterVolumeNode):
    seed = fidNode.GetName()
    if seed not in self.seedCoordsdist:
      self.seedCoordsdist[seed] = []
    fidList = slicer.util.getNode('Profondeur (coupe axiale)')
    for n in range(fidList.GetNumberOfMarkups()):
				posE = [0,0,0,0]
				posS = [0,0,0,0]
				fidList.GetNthFiducialWorldCoordinates(0,posE)
				fidList.GetNthFiducialWorldCoordinates(n,posS)
				ruler = slicer.mrmlScene.AddNode(slicer.vtkMRMLAnnotationRulerNode())
				ruler.SetPosition2(posS[2],posS[1],posS[0])
				volumeNode = masterVolumeNode
				mat = vtk.vtkMatrix4x4()
				volumeNode.GetRASToIJKMatrix(mat)
				pospfrE = [int(round(c)) for c in mat.MultiplyFloatPoint(posE)[:3]]
				pospfrS = [int(round(c)) for c in mat.MultiplyFloatPoint(posS)[:3]]
    
    rulerLengthMm = math.sqrt(vtk.vtkMath.Distance2BetweenPoints(pospfrE[0:3],pospfrS[0:3]))
    #self.addLogdistclic("PROFONDEUR DU FOIE = y")
    #self.addLogdistclic('PosE : {0}'.format(posE))
    #self.addLogdistclic('PosS : {0}'.format(posS))
    #self.addLogdistclic("Position convertie point 1 : {0}".format(pospfrE))
    #self.addLogdistclic("Position convertie point 2 : {0}".format(pospfrS))
    self.addLogdistclic(u"Profondeur maximale manuelle (ant\u00e9rieur post\u00e9rieur) : {0} mm".format(rulerLengthMm))   
    #print("Profondeur maximale manuelle (anterieur posterieur) : {0} mm".format(rulerLengthMm))   
    #self.addLogdistclic("")
    slicer.modules.markups.logic().StartPlaceMode(0)

 
#######################
# Fonctions pour step 9 : Calcul du volume du foie
#######################
  def onLabelSelect(self):
    volumesLogic = slicer.modules.volumes.logic()
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    #inputVolumeclose = self.inputSelector2.currentNode()
    #inputVolume = self.logic.closing (self.masterVolumeNode, self.opening2, self.dilate2, self.erosion2, self.closingfinal, self.remp2, inputVolumeclose)
    #volextract = self.logic.ExportFinal(self.masterVolumeNode,inputVolume)
    volextract = slicer.util.getNode('FoieSegmenteApresCorrection')
    vollabel= volumesLogic.CreateAndAddLabelVolume(slicer.mrmlScene, volextract, "Label_volume_foie_step9" )
    self.labelNode = volumesLogic.CreateLabelVolumeFromVolume(slicer.mrmlScene, vollabel, volextract)
    self.applyButton9.enabled = bool(self.grayscaleNode) and bool(self.labelNode)


  def onGrayscaleSelect(self, node):
    self.grayscaleNode = node
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
    self.applyButton9.text = u"Ex\u00e9cuter la Volum\u00e9trie de la Segmentation"
    labelstep9 = slicer.util.getNode("Label_volume_foie_step9")
    slicer.mrmlScene.RemoveNode(labelstep9)
    labelmapv = slicer.util.getNode("LabelMapVolume")
    slicer.mrmlScene.RemoveNode(labelmapv)


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


########################
# Fonctions pour step 10 : Validation des resultats par rapport a la reference IRCAD
########################
  def onDicomImportClickedRef(self):
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    self.dicomVolumeNodeRef = self.loadDicomsRef(self.inputDicomSelectorRef.directory)
    d = self.dicomVolumeNodeRef.GetDisplayNode()
					# Visualisation en niveaux de gris
    d.SetAutoWindowLevel(0)
					# Visualisation 3D
    redWidget = lm.sliceWidget('Red')
    redWidget.sliceController().setSliceLink(True)
    redWidget.sliceController().setSliceVisible(True)
    threeDWidget = lm.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()
    labelstep91 = slicer.util.getNode("Label_volume_foie_step9_1")
    slicer.mrmlScene.RemoveNode(labelstep91)


  def loadDicomsRef(self, dcmpath):
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
      qt.QApplication.restoreOverrideCursor()

      diag = qt.QInputDialog()
      scriptpath = os.path.dirname(__file__)
      iconpath = os.path.join(scriptpath, 'Resources', 'Icons', 'SegmentationFoie.png')
      iconpath = iconpath.replace('\\', '/')
      icon = qt.QIcon(iconpath)
      diag.setWindowIcon(icon)
      #ok = PythonQt.BoolResult()
      #volDir = os.path.dirname(volArray[0])
      #if not ok:
       # logging.error("No volume selected. Terminating...")
        #return None
    self.inputDicomSelector.directory = volDir
    importer = DICOMScalarVolumePluginClass()
    volNode = importer.load(importer.examine([volArray])[0])
    volNode.SetName("Volume Foie Reference")
    return volNode

    
  def onLabelSelect10(self):
    self.dicomVolumeNodeRef = self.refmaster
    volumesLogic = slicer.modules.volumes.logic()
    vollabel= volumesLogic.CreateAndAddLabelVolume(slicer.mrmlScene, self.dicomVolumeNodeRef, "Label_volume_foie_step10" )
    self.labelNode = volumesLogic.CreateLabelVolumeFromVolume(slicer.mrmlScene, vollabel, self.dicomVolumeNodeRef)
    self.applyButton10.enabled = bool(self.grayscaleNode) and bool(self.labelNode)
    
 
  def onRefSelect(self, node):
    self.grayscaleNode = node
    self.applyButton10.enabled = bool(self.grayscaleNode) and bool(self.labelNode)


  def onApplyButton10(self):
    """Calculate the label statistics
    """ 
    self.applyButton10.text = "Working..."
    self.applyButton10.repaint()
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
        self.logicvolref = VolumeLogic(self.grayscaleNode, resampledLabelNode, colorNode=self.labelNode.GetDisplayNode().GetColorNode10(), nodeBaseName=self.labelNode.GetName())
      else:
        slicer.util.warningDisplay(u"Les volumes n\u00b4ont pas la m\u00eame g\u00e9om\u00e9trie.\n%s" % warnings, windowTitle="Label Statistics")
        return
    else:
      self.logicvolref = VolumeLogic(self.grayscaleNode, self.labelNode)
    self.populateStats10()
    if resampledLabelNode:
      slicer.mrmlScene.RemoveNode(resampledLabelNode)
    self.exportToTableButton10.enabled = True
    labelstep10 = slicer.util.getNode("Label_volume_foie_step10")
    slicer.mrmlScene.RemoveNode(labelstep10)
    self.applyButton10.text = u"Ex\u00e9cuter la Volum\u00e9trie de la Segmentation de R\u00e9f\u00e9rence"
    #labelstep10 = slicer.util.getNode("Label_volume_foie_step10")
    #slicer.mrmlScene.RemoveNode(labelstep10)
    
    
    				# Fonction d'exportation
  def onExportToTable10(self):
    """write the label statistics to a table node
    """
    table10 = self.logicvolref.exportToTable10()  
    
						# Add table to the scene and show it
    slicer.mrmlScene.AddNode(table10)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView)
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(table10.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()


						# Fonction de sauvegarde des resultats
  def onSave10(self):
    """save the label statistics
    """
    if not self.fileDialog:
      self.fileDialog = qt.QFileDialog(self.parent)
      self.fileDialog.options = self.fileDialog.DontUseNativeDialog
      self.fileDialog.acceptMode = self.fileDialog.AcceptSave
      self.fileDialog.defaultSuffix = "csv"
      self.fileDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.fileDialog.connect("fileSelected(QString)", self.onFileSelected10)
      self.fileDialog.show()


  def onFileSelected10(self,fileName):
    self.logicvolref.saveStats(fileName)


  def populateStats10(self):
    if not self.logicvolref:
      return
    displayNode = self.labelNode.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view10.setModel(self.model)
    self.view10.verticalHeader().visible = False
    row = 0
    for i in self.logicvolref.volumestats["volumestats"]:
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
      for k in self.logicvolref.keys10:
        item = qt.QStandardItem()
						# Set data as float with Qt::DisplayRole
        item.setData(float(self.logicvolref.volumestats[i,k]),qt.Qt.DisplayRole)
        item.setToolTip(colorNode.GetColorName(i))
        item.setEditable(False)
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1
    self.view10.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    self.model.setHeaderData(1,1,"Type")
    col = 2
    for k in self.logicvolref.keys10:
      self.view10.setColumnWidth(col,19*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1
      
      
  def onSetupButtonValid(self):
    volumesLogic = slicer.modules.volumes.logic()
    lm = slicer.app.layoutManager()
    self.setupButtonValid.text = "Working..."
    self.setupButtonValid.repaint()
    slicer.app.processEvents()
    
    if self.loadFromDicom.checked:
			volumesegmente = (float(self.logicvol.labelStats[1,self.logicvol.keys[3]]))
			volumereference = (float(self.logicvolref.volumestats[255,self.logicvolref.keys10[3]]))
			#inputVolumeclose = self.inputSelector2.currentNode()
			#inputVolume = self.logic.closing (self.masterVolumeNode, self.opening2, self.dilate2, self.erosion2, self.closingfinal, self.remp2, inputVolumeclose)
			#outfin = self.logic.ExportFinal(self.masterVolumeNode, inputVolume)
			outfin = slicer.util.getNode('FoieSegmenteApresCorrection')

			volvol = slicer.util.arrayFromVolume(self.refmaster)
			volumeLogic = slicer.modules.volumes.logic()
			volref = volumeLogic.CloneVolume(slicer.mrmlScene, self.refmaster, 'Volume Foie Reference')
			vshape = tuple(reversed(volvol.shape))
			vcomponents = 1
			vimage = volref.GetImageData()
			vol = np.array(volvol)
			vol[vol != 0] = 1
			vol[vol == 0] = 0
			vtype = vtk.util.numpy_support.get_vtk_array_type(vol.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(volref)
			narrayTarget[:] = vol
			
			for sliceViewName in lm.sliceViewNames():
			  sliceWidget = lm.sliceWidget(sliceViewName)
			  view = lm.sliceWidget(sliceViewName).sliceView()
			  sliceNode = view.mrmlSliceNode()
			  sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
			  compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
			  compositeNode.SetBackgroundVolumeID(volref.GetID())
						# Setup foreground volume
			  compositeNode.SetForegroundVolumeID(outfin.GetID())
						# Changer l'opacite
			  compositeNode.SetForegroundOpacity(0.7)
			
	
			volvol = slicer.util.arrayFromVolume(volref)
			A = np.array(volvol)
			B = slicer.util.arrayFromVolume(outfin)
			A = np.asarray(A).astype(np.bool) 
			B = np.asarray(B).astype(np.bool) 
			non_seg_score = 1.0
			im_sum = A.sum() + B.sum()
			if im_sum ==0:
			  return non_seg_score
			intersection = np.logical_and(A, B)
			DICE = 2. * intersection.sum() / im_sum
			self.addLogValid(u"Valeur du Coefficient de similarit\u00e9 DICE : {0}".format(DICE))
			self.addLogValid("Plus la valeur est proche de 1, plus la segmentation est fiable.")
			self.addLogValid("")

			VO = DICE / (2-DICE)
			self.addLogValid("Valeur du Volumetric Overlap : {0}".format(VO))
			VOerror = 100 * (1-VO)
			self.addLogValid("Valeur du Volumetric Overlap Error : {0} %".format(VOerror))
			self.addLogValid(u"0 % correspond \u00e0 une segmentation parfaite mais 100 % si segmentation et v\u00e9rit\u00e9 terrain ne correspondent pas.")
			self.addLogValid("")

			self.addLogValid(u"Volume segment\u00e9 : {0} cc".format(volumesegmente))
			self.addLogValid(u"Volume de r\u00e9f\u00e9rence : {0} cc".format(volumereference))
			RVD = 100 * (abs(volumesegmente - volumereference) / abs(volumereference))
			self.addLogValid(u"Diff\u00e9rence Relative de Volume RVD : {0} %".format(RVD))

    if self.loadFromSlicer.checked:
			volumesegmente = (float(self.logicvol.labelStats[1,self.logicvol.keys[3]]))
			volumereference = (float(self.logicvolref.volumestats[1,self.logicvolref.keys10[3]]))
    
    # Affichage
    # Foreground
			#inputVolumeclose = self.inputSelector2.currentNode()
			#inputVolume = self.logic.closing (self.masterVolumeNode, self.opening2, self.dilate2, self.erosion2, self.closingfinal, self.remp2, inputVolumeclose)
			#outfin = self.logic.ExportFinal(self.masterVolumeNode, inputVolume)
			outfin = slicer.util.getNode('FoieSegmenteApresCorrection')

    # Background
			volvol = slicer.util.arrayFromVolume(self.refmaster)
			volumeLogic = slicer.modules.volumes.logic()
			volref = volumeLogic.CloneVolume(slicer.mrmlScene, self.refmaster, 'Volume Foie Reference')
			vshape = tuple(reversed(volvol.shape))
			vcomponents = 1
			vimage = volref.GetImageData()
			vol = np.array(volvol)
			vol[vol != 1] = 0
			vol[vol == 1] = 1
			vtype = vtk.util.numpy_support.get_vtk_array_type(vol.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(volref)
			narrayTarget[:] = vol

			for sliceViewName in lm.sliceViewNames():
			  sliceWidget = lm.sliceWidget(sliceViewName)
			  view = lm.sliceWidget(sliceViewName).sliceView()
			  sliceNode = view.mrmlSliceNode()
			  sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
			  compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
			  compositeNode.SetBackgroundVolumeID(volref.GetID())
						# Setup foreground volume
			  compositeNode.SetForegroundVolumeID(outfin.GetID())
						# Changer l'opacite
			  compositeNode.SetForegroundOpacity(0.7)
      
			volvol = slicer.util.arrayFromVolume(volref)
			A = np.array(volvol)
			B = slicer.util.arrayFromVolume(outfin)
			A = np.asarray(A).astype(np.bool) 
			B = np.asarray(B).astype(np.bool) 
			non_seg_score = 1.0
			im_sum = A.sum() + B.sum()
			if im_sum ==0:
			  return non_seg_score
			intersection = np.logical_and(A, B)
			DICE = 2. * intersection.sum() / im_sum
			self.addLogValid("Valeur du Coefficient de similarite DICE : {0}".format(DICE))
			self.addLogValid("N.B. : Plus la valeur est proche de 1, plus la segmentation est fiable.")
			self.addLogValid("")

			VO = DICE / (2-DICE)
			self.addLogValid("Valeur du Volumetric Overlap : {0}".format(VO))
			VOerror = 100 * (1-VO)
			self.addLogValid("Valeur du Volumetric Overlap Error : {0} %".format(VOerror))
			self.addLogValid("N.B. : 0 % correspond a une segmentation parfaite mais 100 % si segmentation et verite terrain ne correspondent pas.")

			self.addLogValid("")
			self.addLogValid("Volume segmente : {0} cc".format(volumesegmente))
			self.addLogValid("Volume de reference : {0} cc".format(volumereference))
			RVD = 100 * (abs(volumesegmente - volumereference) / abs(volumereference))
			self.addLogValid("Relative volume difference RVD : {0} %".format(RVD))

    self.setupButtonValid.text = u"Configurer la volum\u00e9trie"


						# Cadre de resultats
  def addLog(self, text):
    """Append text to log window
    """
    self.statusLabel.appendPlainText(text)
    slicer.app.processEvents() # force update

  def addLoghisto(self, text):
    self.statusLabelhisto.appendPlainText(text)
    slicer.app.processEvents()

  def addLogextract(self, text):
    self.statusLabelextract.appendPlainText(text)
    slicer.app.processEvents()

  def addLogdistauto(self, text):
    self.statusLabeldistauto.appendPlainText(text)
    slicer.app.processEvents()

  def addLogdistclic(self, text):
    self.statusLabeldistclic.appendPlainText(text)
    slicer.app.processEvents()
    
  def addLogValid(self, text):
    self.statusLabelValid.appendPlainText(text)
    slicer.app.processEvents()   
       
       
       
#########################################################################
# SegmentationFoieLogic - INTERFACE FONCTIONNELLE : CALCULS, SEGMENTATION
#########################################################################

class SegmentationFoieLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
						# Fonction d'initialisation
  def __init__(self, parent = None):
     ScriptedLoadableModuleLogic.__init__(self, parent)
     self.logCallback = None
     self.logCallbackhisto = None
     self.logCallbackextract = None
     self.logCallbackdistauto = None
     self.logCallbackdistclic = None
    
    
						# Cadre de resultats
  def addLog(self, text):
    logging.info(text)
    if self.logCallback:
      self.logCallback(text) 

  def addLoghisto(self, text):
    logging.info(text)
    if self.logCallbackhisto:
      self.logCallbackhisto(text) 
      
  def addLogextract(self, text):
    logging.info(text)
    if self.logCallbackextract:
      self.logCallbackextract(text) 
      
  def addLogdistauto(self, text):
    logging.info(text)
    if self.logCallbackdistauto:
      self.logCallbackdistauto(text) 
      
  def addLogdistclic(self, text):
    logging.info(text)
    if self.logCallbackdistclic:
      self.logCallbackdistclic(text) 

  def addLogValid(self, text):
    logging.info(text)
    if self.logCallbackValid:
      self.logCallbackValid(text) 
         
          
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
# Fonctions pour step 2 : CROP
#######################
  def createParameterNode(self):
						# Set default parameters
    node = ScriptedLoadableModuleLogic.createParameterNode(self)
    node.SetName(slicer.mrmlScene.GetUniqueNameByString(self.moduleName))
    node.SetParameter("RognerHorsSurface", "1")
    return node
  
  
  def clipVolumeWithRoi(self, roiNode, masterVolumeNode, clipOutsideSurface, outputVolume):
    start = time.time()  
    #logging.info('Crop started')   

						# Create a box implicit function that will be used as a stencil to fill the volume    
    roiBox = vtk.vtkBox()    
    roiCenter = [0, 0, 0]
    roiNode.GetXYZ(roiCenter)
    roiRadius = [0, 0, 0]
    roiNode.GetRadiusXYZ(roiRadius)
    roiBox.SetBounds(roiCenter[0] - roiRadius[0], roiCenter[0] + roiRadius[0], roiCenter[1] - roiRadius[1], roiCenter[1] + roiRadius[1], roiCenter[2] - roiRadius[2], roiCenter[2] + roiRadius[2])

						# Determine the transform between the box and the image IJK coordinate systems
    rasToBox = vtk.vtkMatrix4x4()    
    if roiNode.GetTransformNodeID() != None:
      roiBoxTransformNode = slicer.mrmlScene.GetNodeByID(roiNode.GetTransformNodeID())
      boxToRas = vtk.vtkMatrix4x4()
      roiBoxTransformNode.GetMatrixTransformToWorld(boxToRas)
      rasToBox.DeepCopy(boxToRas)
      rasToBox.Invert()
    ijkToRas = vtk.vtkMatrix4x4()
    masterVolumeNode.GetIJKToRASMatrix(ijkToRas)

    ijkToBox = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Multiply4x4(rasToBox,ijkToRas,ijkToBox)
    ijkToBoxTransform = vtk.vtkTransform()
    ijkToBoxTransform.SetMatrix(ijkToBox)
    roiBox.SetTransform(ijkToBoxTransform)
    
						# Clonage du volume pour ne pas alterer le volume d'origine
    volumeLogic = slicer.modules.volumes.logic()
    outputVolumecrop = volumeLogic.CloneVolume(slicer.mrmlScene, masterVolumeNode, 'Volume Rogne')
    imageData=outputVolumecrop.GetImageData()

						# Convert the implicit function to a stencil
    functionToStencil = vtk.vtkImplicitFunctionToImageStencil()
    functionToStencil.SetInput(roiBox)
    functionToStencil.SetOutputOrigin(imageData.GetOrigin())
    functionToStencil.SetOutputSpacing(imageData.GetSpacing())
    functionToStencil.SetOutputWholeExtent(imageData.GetExtent())
    functionToStencil.Update()

						# Apply the stencil to the volume
    stencilToImage=vtk.vtkImageStencil()
    stencilToImage.SetInputData(imageData)
    stencilToImage.SetStencilData(functionToStencil.GetOutput())
    if clipOutsideSurface:
      stencilToImage.ReverseStencilOff()
    else:
      stencilToImage.ReverseStencilOn()
    stencilToImage.Update()

						# Update the volume with the stencil operation result
    outputImageData = vtk.vtkImageData()
    outputImageData.DeepCopy(stencilToImage.GetOutput())
    outputVolume.SetAndObserveImageData(outputImageData);
    outputVolume.SetIJKToRASMatrix(ijkToRas)
       
						# Calcul de sigma et affichage de la valeur
						# Ecart-type moins ddof egal 1 pour effectuer le calcul 1 sur (n-1)
    testsigma = slicer.util.arrayFromVolume(outputVolume)
    #self.addLog("CROP DATA")
    self.addLog("La moyenne vaut : {0}".format(np.mean(testsigma)))  
    self.addLog("Sigma vaut : {0}".format(np.std(testsigma, ddof=1)))
    #logging.info('Crop completed')
    
						# Affichage 
    slicer.util.setSliceViewerLayers(outputVolume)
      
    
########################
# Fonction pour step 3 : FILTRAGE
########################
  def run(self, masterVolumeNode, filtreMedian, filtreGaussian, size, sigma): 
    start = time.time()  
    #logging.info('Filtrage started')
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    
						# Convertir le volume DICOM en un tableau numpy
    a = slicer.util.arrayFromVolume(masterVolumeNode)

						# Clonage du volume pour ne pas alterer le volume d'origine
    volumeLogic = slicer.modules.volumes.logic()
    outputVolume3 = volumeLogic.CloneVolume(slicer.mrmlScene, masterVolumeNode, 'Volume apres Filtrage')
    vshape = tuple(reversed(a.shape))
    vcomponents = 1
    vimage = outputVolume3.GetImageData()
    			
    if (filtreGaussian.checked) :
			gauss = spyndi.gaussian_filter(a, sigma=sigma, order=0)
			vtype = vtk.util.numpy_support.get_vtk_array_type(gauss.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outputVolume3)
			narrayTarget[:] = gauss
    
    if (filtreMedian.checked):
			median = ndimage.filters.median_filter(a, size=size, footprint=None, output=None, mode='reflect', cval=0.0, origin=0 )
			vtype = vtk.util.numpy_support.get_vtk_array_type(median.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outputVolume3)
			narrayTarget[:] = median

						# Volume modifie apres modification du tableau numpy
    outputVolume3.StorableModified()
    outputVolume3.Modified()
    outputVolume3.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, masterVolumeNode)

						# Affichage 
    slicer.util.setSliceViewerLayers(outputVolume3)
    #logging.info('Filtrage completed')
    return outputVolume3
        
    
####################
# Fonction step 4 : HISTOGRAMME ET SEUILLAGE
####################
  def pic(self, masterVolumeNode) :
    start = time.time()  
    #logging.info('Histogramme + Seuillage started')
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)

    outputVolumehisto = slicer.util.getNode('Volume apres Filtrage')
    b = slicer.util.arrayFromVolume(outputVolumehisto)
    
    rangeHisto = [0,int(np.max(b))] 
    histo,bins_edge = np.histogram(b.flatten(), rangeHisto[1]-rangeHisto[0]+1,rangeHisto)
    
						## Valeur et indice du plus grand pic de l'histogramme
    valMaxHisto = np.max(histo)
    indiceMaxHisto = np.argmax(histo)
    self.addLoghisto("")
    self.addLoghisto(u"La valeur maximale de l'histogramme se situe \u00e0 l'indice [{0}] et vaut {1}".format((indiceMaxHisto + rangeHisto[0]), valMaxHisto))

 
  def histo (self, masterVolumeNode, imageThreshold, imageThreshold2):
    start = time.time()  
    #logging.info('Histogramme + Seuillage started')
    lm = slicer.app.layoutManager()

    outputVolumehisto = slicer.util.getNode('Volume apres Filtrage')
    b = slicer.util.arrayFromVolume(outputVolumehisto)
    volumeLogic = slicer.modules.volumes.logic()
    outhisto = volumeLogic.CloneVolume(slicer.mrmlScene, outputVolumehisto, 'Volume apres Seuillage')
    vshape = tuple(reversed(b.shape))
    vcomponents = 1
    vimage = outhisto.GetImageData()
    
    rangeHisto = [0,int(np.max(b))] 
    histo,bins_edge = np.histogram(b.flatten(), rangeHisto[1]-rangeHisto[0]+1,rangeHisto)
    
						# Affichage de l'histogramme    
						# Save results to a new table node
    tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
    slicer.util.updateTableFromArray(tableNode, histo)
    tableNode.GetTable().GetColumn(0).SetName("Comptage")

						# Create plot
    plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", ' Histogramme du foie')
    plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
    plotSeriesNode.SetXColumnName("Intensity")
    plotSeriesNode.SetYColumnName("Comptage")
    plotSeriesNode.SetPlotType(plotSeriesNode.PlotTypeScatterBar)
    plotSeriesNode.SetColor(1, 0, 0.5)

						# Create chart and add plot
    plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
    plotChartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())
    plotChartNode.YAxisRangeAutoOn()
    plotChartNode.SetXAxisRange(rangeHisto)

						# Show plot in layout
    slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)
    
    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    cliParams2 = {'ThresholdValue' : imageThreshold2, 'ThresholdType' : 'Above'}
    cliNode2 = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams2, wait_for_completion=True)

    borne1 = imageThreshold
    borne2 = imageThreshold2
		
    bornes = [borne1, borne2] 
    self.addLoghisto("Les bornes encadrant le pic du foie sont : {0}".format(bornes))

						# Seuillage entre les bornes en modifiant les valeurs de voxels   
    imgBinary = np.array(b)
    thresholdValue1 = borne1
    imgBinary[b < thresholdValue1] = 0 
    imgBinary2 = np.array(imgBinary)
    thresholdValue2 = borne2
    imgBinary2[imgBinary > thresholdValue2] = 0     
    vtype = vtk.util.numpy_support.get_vtk_array_type(imgBinary2.dtype)
    vimage.SetDimensions(vshape)
    vimage.AllocateScalars(vtype, vcomponents)
    narrayTarget = slicer.util.arrayFromVolume(outhisto)
    narrayTarget[:] = imgBinary2

						# Volume modifie
    outhisto.StorableModified()
    outhisto.Modified()
    outhisto.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, outputVolumehisto)
    outhisto.GetDisplayNode().SetAndObserveColorNodeID('vtkMRMLColorTableNodeInvertedGrey')
    
						# Affichage 
    #slicer.util.setSliceViewerLayers(outhisto)
    
            # Choix du background et du foreground des coupes visualisees
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
						 # Setup background volume
      compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
						 # Setup foreground volume
      compositeNode.SetForegroundVolumeID(outhisto.GetID())
						 # Changer l'opacite
      compositeNode.SetForegroundOpacity(0.9)

    #logging.info('Histogramme + Seuillage completed')
    return outhisto


####################
# Fonction step 5 : OPERATIONS DE MORPHOLOGIE MATHEMATIQUE
####################
  def morpho (self, masterVolumeNode, opening, taille, dilate, erosion, closing, remp, inputVolume):#, outputVolume):
    start = time.time()  
   # logging.info('Operations de morphologie mathematique started')
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)

    c = slicer.util.arrayFromVolume(inputVolume)
    volumeLogic = slicer.modules.volumes.logic()
    outmorpho = volumeLogic.CloneVolume(slicer.mrmlScene, inputVolume, 'Volume apres Morphologie Mathematique')
    vshape = tuple(reversed(c.shape))
    vcomponents = 1
    vimage = outmorpho.GetImageData()
    
						# Element structurant pour remplacer skimorpho.ball(2), 26 connectivites
    #struc = np.ones((3,3,3)) 
    struc = np.ones((taille,taille,taille)) 
    
    if (opening.checked):
			ouverture = np.array(c)
			ouv = ndimage.binary_opening(c, struc, iterations = 2)
			ouverture[ouv==1]=255
			ouverture[ouv==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(ouverture.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outmorpho)
			narrayTarget[:] = ouverture
 
    if (dilate.checked):
			dilatation = np.array(c)
			dil = ndimage.binary_dilation(c, struc, iterations = 1)
			dilatation[dil==1]=255
			dilatation[dil==0] = 0
			vtype = vtk.util.numpy_support.get_vtk_array_type(dilatation.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outmorpho)
			narrayTarget[:] = dilatation

    if (erosion.checked):
			ero = np.array(c)
			clo = ndimage.binary_erosion(c, struc, iterations = 1)
			ero[clo==1]=255
			ero[clo==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(ero.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outmorpho)
			narrayTarget[:] = ero
						
    if (closing.checked):
			fermeture = np.array(c)
			clo = ndimage.binary_closing(c, struc, iterations = 2)
			fermeture[clo==1]=255
			fermeture[clo==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(fermeture.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outmorpho)
			narrayTarget[:] = fermeture

    if (remp.checked):
			rempli = np.array(c)
			clo = ndimage.binary_fill_holes(c, struc)
			rempli[clo==1]=255
			rempli[clo==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(rempli.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outmorpho)
			narrayTarget[:] = rempli
			
						# Volume modifie
    outmorpho.StorableModified()
    outmorpho.Modified()
    outmorpho.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, inputVolume)
    outmorpho.GetDisplayNode().SetAndObserveColorNodeID('vtkMRMLColorTableNodeGrey')

						# Affichage   
            # Choix du background et du foreground des coupes visualisees
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
						 # Setup background volume
      compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
						 # Setup foreground volume
      compositeNode.SetForegroundVolumeID(outmorpho.GetID())
						 # Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)
     
    #logging.info('Operations de morphologie mathematique completed')
    return outmorpho


####################
# Fonction step 6 : EXTRACTION DES COMPOSANTES CONNEXES
####################
  def extractedcomponents (self, masterVolumeNode, seedCoords, posIJK, outmorpho, inputVolume2):
    start = time.time()  
    #logging.info('Extracted components started')
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)

    d = slicer.util.arrayFromVolume(inputVolume2)
    volumeLogic = slicer.modules.volumes.logic()
    outextract = volumeLogic.CloneVolume(slicer.mrmlScene, inputVolume2, 'Volume apres Extraction')
    vshape = tuple(reversed(d.shape))
    vcomponents = 1
    vimage = outextract.GetImageData()

						# Element structurant
    struc = np.ones((3,3,3))
    
						# Labellisation
    imagelabel = np.array(d)
    image_labels, nblabels = ndimage.label(d, structure = struc)
    #self.addLogextract("Le nombre de labels est : {0}".format(nblabels))
    #print('Nombre de labels : ', nblabels)
    
						# On attribue la position du curseur pointe par user au label correspondant
    choixlabel = (image_labels[posIJK[2],posIJK[1],posIJK[0]])
    self.addLogextract(u"Le num\u00e9ro du label du foie est : {0}".format(choixlabel))
    self.addLogextract("Le nombre de labels est : {0}".format(nblabels))

    #print('Numero label du foie : ', choixlabel)
    
						# On ne fait apparaitre que la structure pointee
    im=(image_labels == choixlabel)
    imagelabel[im==1]=255
    imagelabel[im==0]=0

    vtype = vtk.util.numpy_support.get_vtk_array_type(imagelabel.dtype)
    vimage.SetDimensions(vshape)
    vimage.AllocateScalars(vtype, vcomponents)
    narrayTarget = slicer.util.arrayFromVolume(outextract)
    narrayTarget[:] = imagelabel

						# Volume modifie
    outextract.StorableModified()
    outextract.Modified()
    outextract.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, inputVolume2)

						# Affichage   
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
      compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
						# Setup foreground volume
      compositeNode.SetForegroundVolumeID(outextract.GetID())
						# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)
      
    #logging.info('Extraction completed')
    return outextract


####################
# Fonction step 7 : OPERATIONS DE MORPHOLOGIE MATHEMATIQUE FINALES
####################
  def closing (self, masterVolumeNode, opening2, taille2, dilate2, erosion2, closingfinal, remp2, inputVolumeclose):
    start = time.time()  
    #logging.info('Operation binaire finale started')
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    e = slicer.util.arrayFromVolume(inputVolumeclose)
    volumeLogic = slicer.modules.volumes.logic()
    outfin = volumeLogic.CloneVolume(slicer.mrmlScene, inputVolumeclose, 'Volume Final')
    vshape = tuple(reversed(e.shape))
    vcomponents = 1
    vimage = outfin.GetImageData()

    #struc = np.ones((3,3,3))
    struc = np.ones((taille2,taille2,taille2))
    
    if (opening2.checked):
			ouverture = np.array(e)
			ouv = ndimage.binary_opening(e, struc, iterations = 2)
			ouverture[ouv==1]=255
			ouverture[ouv==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(ouverture.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outfin)
			narrayTarget[:] = ouverture
			 
    if (dilate2.checked):
			dilatation = np.array(e)
			dil = ndimage.binary_dilation(e, struc, iterations = 1)
			dilatation[dil==1]=255
			dilatation[dil==0] = 0
			vtype = vtk.util.numpy_support.get_vtk_array_type(dilatation.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outfin)
			narrayTarget[:] = dilatation

    if (erosion2.checked):
			ero = np.array(e)
			clo = ndimage.binary_erosion(e, struc, iterations = 1)
			ero[clo==1]=255
			ero[clo==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(ero.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outfin)
			narrayTarget[:] = ero
			
    if (closingfinal.checked):
			fermeture = np.array(e)
			clo = ndimage.binary_closing(e, struc, iterations = 2)
			fermeture[clo==1]=255
			fermeture[clo==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(fermeture.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outfin)
			narrayTarget[:] = fermeture

    if (remp2.checked):
			rempli2 = np.array(e)
			clo = ndimage.binary_fill_holes(e, struc)
			rempli2[clo==1]=255
			rempli2[clo==0]=0
			vtype = vtk.util.numpy_support.get_vtk_array_type(rempli2.dtype)
			vimage.SetDimensions(vshape)
			vimage.AllocateScalars(vtype, vcomponents)
			narrayTarget = slicer.util.arrayFromVolume(outfin)
			narrayTarget[:] = rempli2
			
						# Volume modifie
    outfin.StorableModified()
    outfin.Modified()
    outfin.InvokeEvent(slicer.vtkMRMLVolumeNode.ImageDataModifiedEvent, inputVolumeclose)

						# Affichage 
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
      compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
						# Setup foreground volume
      compositeNode.SetForegroundVolumeID(outfin.GetID())
						# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)
      
    #logging.info('Operation binaire finale completed')
    return outfin


  def CorrectionFinale(self, masterVolumeNode, inputVolCor):
						# Etape 1 : creer un labelmap de mon volume final
    volumesLogic = slicer.modules.volumes.logic()
    vollabel = volumesLogic.CreateAndAddLabelVolume(slicer.mrmlScene, inputVolCor, "Labelmap du foie" )
    labelmaptocorrect = volumesLogic.CreateLabelVolumeFromVolume(slicer.mrmlScene, vollabel, inputVolCor)
    lm = slicer.app.layoutManager()

						# Affichage du labelmap en transparence
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
      compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
						# Setup foreground volume
      compositeNode.SetForegroundVolumeID(labelmaptocorrect.GetID())
						# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)
        
						# Etape 2 : Importation du labelmap dans le module segmentation pour creer une segmentation
    segmentationNode = slicer.vtkMRMLSegmentationNode()
    slicer.mrmlScene.AddNode(segmentationNode)
    segmentationNode.CreateDefaultDisplayNodes()
    segmentationNode.SetName("CorrectionSegmentationFoie")	
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputVolCor)
     
    segmentationLogic = slicer.modules.segmentations.logic()
    importlabelmaptocorrect = segmentationLogic.ImportLabelmapToSegmentationNode (labelmaptocorrect, segmentationNode)
    segmentationNode.CreateClosedSurfaceRepresentation()

						# Etape 3 : Correction de la segmentation par les effets paint / erase 
    editorWidget = slicer.modules.segmenteditor.createNewWidgetRepresentation()
    editorWidget.setMRMLScene(slicer.app.mrmlScene())
    slicer.util.getNode('SegmentEditor').SetAttribute('BrushSphere','1')
    editorWidget.show()
    
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
      compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
						# Setup foreground volume
      compositeNode.SetForegroundVolumeID(labelmaptocorrect.GetID())
						# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)
    
    labelmaptocorrect.GetImageData().Modified()
    labelmaptocorrect.Modified()
    return vollabel

    
  def ExportFinal(self, masterVolumeNode, inputVolume):
						# Exporter le labelmap node de la segmentation et crer le volume correspondant
    seg = slicer.util.getNode('CorrectionSegmentationFoie')
    labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode','Label_Foie_final_step7')
    inputVolume =  slicer.vtkMRMLScalarVolumeNode()
    visibleSegmentIds = vtk.vtkStringArray()
    slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(seg, visibleSegmentIds, labelmapVolumeNode, masterVolumeNode)
    outputvolumenode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", 'FoieSegmenteApresCorrection')
    foiesegmente = slicer.modules.volumes.logic().CreateScalarVolumeFromVolume(slicer.mrmlScene, outputvolumenode, labelmapVolumeNode)    
    slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
    lm = slicer.app.layoutManager()
    for sliceViewName in lm.sliceViewNames():
        sliceWidget = lm.sliceWidget(sliceViewName)
        view = lm.sliceWidget(sliceViewName).sliceView()
        sliceNode = view.mrmlSliceNode()
        sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
        compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
        compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
            # Setup foreground volume
        compositeNode.SetForegroundVolumeID(foiesegmente.GetID())
            # Changer l'opacite
        compositeNode.SetForegroundOpacity(0.7)
       
    slicer.util.saveNode(foiesegmente, '~\Documents\TroisDSlicer\FoieSegmenteDonneur.nii')
    filename = os.path.join(os.path.expanduser("~"),'\Documents\TroisDSlicer\FoieSegmenteDonneurData')
    slicer.util.saveScene(filename)
    return foiesegmente
    
    
###################
# Fonction step 8 : CALCULER LA DISTANCE ENTRE DEUX POINTS DU FOIE
###################
  def autodistance(self, masterVolumeNode, outfin):
    start = time.time()  
    #logging.info('Distances automatiques started')
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    
    abc = slicer.util.arrayFromVolume(outfin)    
						# Recuperer les valeurs du pixel spacing
    mas = slicer.util.arrayFromVolume(masterVolumeNode)
    pixelspacing = masterVolumeNode.GetSpacing()
    #print('Pixel spacing (x,y,z) {} : '.format(pixelspacing))

						# Transformee de distance euclidienne exacte dans le referentiel RAS    
    MAX = np.max(abc.shape)
    
    self.addLogdistauto("")
    #self.addLogdistauto("DISTANCES AUTOMATIQUES DETECTEES")
			
    toty = ndimage.distance_transform_edt(abc==1, [MAX, pixelspacing[1],MAX]) 
    self.addLogdistauto(u"Profondeur automatique max en y (post\u00e9rieur vers ant\u00e9rieur) : {0} mm".format(2*np.max(toty)))
			
    totz = ndimage.distance_transform_edt(abc==1, [pixelspacing[2], MAX, MAX])
    self.addLogdistauto(u"Hauteur automatique max en z (inf\u00e9rieur vers sup\u00e9rieur) : {0} mm".format(2*np.max(totz)))
    
    totx = ndimage.distance_transform_edt(abc==1,[MAX, MAX, pixelspacing[0]])
    self.addLogdistauto(u"Longueur horizontale automatique max en x (de gauche \u00e0 droite) : {0} mm".format(2*np.max(totx)))

    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
						# Setup background volume
      compositeNode.SetBackgroundVolumeID(masterVolumeNode.GetID())
						# Setup foreground volume
      compositeNode.SetForegroundVolumeID(outfin.GetID())
						# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)   
    #logging.info('Distances automatiques completed')
    
    
###################
# Fonction step 9 : CALCULER LE VOLUME DU FOIE SEGMENTE
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


###################
# Fonction step 10 : CALCULER LE VOLUME DU FOIE REFERENCE
###################
class VolumeLogic(ScriptedLoadableModuleLogic):
  def __init__(self, grayscaleNode, labelNode, colorNode=None, nodeBaseName=None, fileName=None):  
    self.keys10 = ("Index", "Comptage", "Volume mm^3", "Volume cc", "Minimum", "Maximum", "Moyenne", "Mediane", "StdDev")

    cubicMMPerVoxel = reduce(lambda x,y: x*y, labelNode.GetSpacing())
    ccPerCubicMM = 0.001
		  
    self.labelNode = labelNode
    self.colorNode = colorNode
    self.nodeBaseName = nodeBaseName
       
    if not self.nodeBaseName:
      self.nodeBaseName = labelNode.GetName() if labelNode.GetName() else 'volumestats'
    self.volumestats = {}
    self.volumestats['volumestats'] = []

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
        self.volumestats["volumestats"].append(i)
        self.volumestats[i,"Index"] = i
        self.volumestats[i,"Comptage"] = round(stat1.GetVoxelCount(),3)
        self.volumestats[i,"Volume mm^3"] = round(self.volumestats[i,"Comptage"] * cubicMMPerVoxel,3)
        self.volumestats[i,"Volume cc"] = self.volumestats[i,"Volume mm^3"] * ccPerCubicMM
        self.volumestats[i,"Minimum"] = stat1.GetMin()[0]
        self.volumestats[i,"Maximum"] = stat1.GetMax()[0]
        self.volumestats[i,"Moyenne"] = round(stat1.GetMean()[0],3)
        self.volumestats[i,"Mediane"] = round(medians.GetMedian(),3)
        self.volumestats[i,"StdDev"] = round(stat1.GetStandardDeviation()[0],3)

           
  def getColorNode10(self):
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

  
  def exportToTable10(self):
    """
    Export statistics to table node
    """    
    colorNode = self.getColorNode10()
    table10 = slicer.vtkMRMLTableNode()
    tableWasModified = table10.StartModify()
    table10.SetName(slicer.mrmlScene.GenerateUniqueName(self.nodeBaseName + ' statistics'))

						# Define table columns
    if colorNode:
      col = table10.AddColumn()
      col.SetName("Type")
    for k in self.keys10:
      col = table10.AddColumn()
      col.SetName(k)
    for i in self.volumestats["volumestats"]:
      rowIndex = table10.AddEmptyRow()
      columnIndex = 0
      if colorNode:
        table10.SetCellText(rowIndex, columnIndex, colorNode.GetColorName(i))
        columnIndex += 1
						# Add other values
      for k in self.keys10:
        table10.SetCellText(rowIndex, columnIndex, str(self.volumestats[i, k]))
        columnIndex += 1
    table10.EndModify(tableWasModified)
    return table10

    
  def statsAsCSV(self):
    """
    print comma separated value file with header keys in quotes
    """
    colorNode = self.getColorNode10()  
    csv = ""
    header = ""
    if colorNode:
      header += "\"%s\"" % "Type" + ","
    for k in self.keys10[:-1]:
      header += "\"%s\"" % k + ","
    header += "\"%s\"" % self.keys10[-1] + "\n"
    csv = header
    for i in self.volumestats["volumestats"]:
      line = ""
      if colorNode:
        line += colorNode.GetColorName(i) + ","
      for k in self.keys10[:-1]:
        line += str(self.volumestats[i,k]) + ","
      line += str(self.volumestats[i,self.keys10[-1]]) + "\n"
      csv += line
    return csv

  def saveStats(self,fileName):
    fp = open(fileName, "w")
    fp.write(self.statsAsCSV())
    fp.close()
    
    
    
############################################
# CLASSE TEST : TESTER SI LE CODE FONCTIONNE
############################################
   
class SegmentationFoieTest(ScriptedLoadableModuleTest):
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
    self.test_SegmentationFoie1()


  def test_SegmentationFoie1(self):
    self.delayDisplay("Commencer le test")
    self.delayDisplay(u'Test r\u00e9ussi !')



    

