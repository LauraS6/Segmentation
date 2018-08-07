import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# SuperpositionFoieCavite
#

class SuperpositionFoieCavite(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = u"Superposition de la cavit\u00e9 abdominale avec le foie segment\u00e9"
    self.parent.categories = ["SUPERPOSITION donneur / receveur"]
    self.parent.dependencies = []
    self.parent.contributors = ["Laura Seimpere"]
    self.parent.helpText = """
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
"""

#
# SuperpositionFoieCaviteWidget
#

class SuperpositionFoieCaviteWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

		#########
    # Step 1 : Charger images
		#########
    stepsCollapsibleButton = ctk.ctkCollapsibleButton()
    stepsCollapsibleButton.text = u"SUPERPOSITION cavit\u00e9 du receveur / foie segment\u00e9 du donneur"
    self.layout.addWidget(stepsCollapsibleButton)
    stepsFormLayout = qt.QFormLayout(stepsCollapsibleButton)

					# Chargement avec dossier DICOM
					# Bouton de chargement par DICOM mis sur True
    self.loadcavite = qt.QRadioButton("Charger la CAVITE")
    self.loadcavite.checked = True
    stepsFormLayout.addRow(self.loadcavite)
    self.VolumeNode1 = None
    self.VolumeNode2 = None

					# Chargement avec dossier DICOM
					# Bouton de chargement par DICOM mis sur True
    self.loadfoie = qt.QRadioButton("Charger le FOIE SEGMENTE")
    stepsFormLayout.addRow(self.loadfoie)
    
					# Espace pour une meilleure visibilite dans l'affichage
    self.inputDistLabel = qt.QLabel("")
    stepsFormLayout.addRow(self.inputDistLabel)
    
    					# Input volume selector
    self.inputSelector1 = slicer.qMRMLNodeComboBox()
    self.inputSelector1.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector1.selectNodeUponCreation = True
    self.inputSelector1.addEnabled = False
    self.inputSelector1.removeEnabled = False
    self.inputSelector1.noneEnabled = False
    self.inputSelector1.showHidden = False
    self.inputSelector1.showChildNodeTypes = False
    self.inputSelector1.setMRMLScene( slicer.mrmlScene)
    self.inputSelector1.setToolTip(u"Choisir l\u00b4entr\u00e9e de l\u00b4algorithme." )
    self.inputSelector1.setMaximumWidth(250)
    stepsFormLayout.addRow(u"  Volume d\u00b4entr\u00e9e de la cavit\u00e9 :                        ", self.inputSelector1)
    
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
    stepsFormLayout.addRow(u"  Volume d\u00b4entr\u00e9e du foie :                        ", self.inputSelector2)
    
    # Apply Button
    self.applyButton = qt.QPushButton(u"Ex\u00e9cuter")
    self.applyButton.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton.enabled = True
    stepsFormLayout.addRow(self.applyButton)

    # Connections
    self.loadcavite.connect("clicked(bool)", self.onSelect)
    self.loadfoie.connect("clicked(bool)", self.onSelect)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass


  def onSelect(self):
    if self.loadcavite.checked:
      self.VolumeNode1 = os.path.join(os.path.expanduser("~"),"Documents/TroisDSlicer/Imageasuperposer/")
      slicer.util.openAddVolumeDialog()
      self.masterVolumeNode = self.VolumeNode1
      
    if self.loadfoie.checked:
      self.VolumeNode2 = os.path.join(os.path.expanduser("~"),"Documents/TroisDSlicer/Imageasuperposer/")
      slicer.util.openAddVolumeDialog()
      self.masterVolumeNode = self.VolumeNode2
    self.applyButton.enabled = self.masterVolumeNode


  def onApplyButton(self):
    logic = SuperpositionFoieCaviteLogic()
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    self.VolumeNode1 = self.inputSelector1.currentNode()
    self.VolumeNode2 = self.inputSelector2.currentNode()
    
            			## Affichage 
    lm = slicer.app.layoutManager()
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
					# Setup background volume
      compositeNode.SetBackgroundVolumeID(self.VolumeNode1.GetID())
					# Setup foreground volume
      compositeNode.SetForegroundVolumeID(self.VolumeNode2.GetID())
					# Changer l'opacite
      compositeNode.SetForegroundOpacity(0.7)


#
# SuperpositionFoieCaviteLogic
#
class SuperpositionFoieCaviteLogic(ScriptedLoadableModuleLogic):
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


class SuperpositionFoieCaviteTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SuperpositionFoieCavite1()

  def test_SuperpositionFoieCavite1(self):
    self.delayDisplay("Starting the test")
    self.delayDisplay('Test passed !')
