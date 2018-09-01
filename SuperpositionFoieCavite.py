import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
# -*- coding: utf-8 -*-

#
# SuperpositionFoieCavite
#

class SuperpositionFoieCavite(ScriptedLoadableModule):
  def __init__(self, parent):
      ScriptedLoadableModule.__init__(self, parent)
      self.parent.title = u"Superposition de la cavit\u00e9 abdominale avec le foie segment\u00e9"
      self.parent.categories = ["SUPERPOSITION donneur / receveur"]
      self.parent.dependencies = []
      self.parent.contributors = ["Laura Seimpere"]
      self.parent.helpText = u"""
Superposition du foie segment\u00e9 et de la cavit\u00e9 abdominale segment\u00e9e par les modules pr\u00e9c\u00e9dents et apr\u00e8s recalage rigide 3D entre les deux volumes charg\u00e9s.
        """
      self.parent.helpText += self.getDefaultModuleDocumentationLink()
      self.parent.acknowledgementText = """
        """

#
# SuperpositionFoieCaviteWidget
#

class SuperpositionFoieCaviteWidget(ScriptedLoadableModuleWidget):
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    #########
    # Step 1 : Charger les images
    #########
    stepsCollapsibleButton = ctk.ctkCollapsibleButton()
    stepsCollapsibleButton.text = u"SUPERPOSITION cavit\u00e9 du receveur / foie segment\u00e9 du donneur"
    self.layout.addWidget(stepsCollapsibleButton)
    stepsFormLayout = qt.QFormLayout(stepsCollapsibleButton)
    
    # Chargement avec dossier DICOM
    # Bouton de chargement par DICOM mis sur True
    self.loadcavite = qt.QRadioButton("Charger la CAVITE SEGMENTEE")
    self.loadcavite.checked = True
    stepsFormLayout.addRow(self.loadcavite)
    self.VolumeNodecavite = None
    self.VolumeNodefoie = None
    
    # Chargement avec dossier DICOM
    # Bouton de chargement par DICOM mis sur True
    self.loadfoie = qt.QRadioButton("Charger le FOIE SEGMENTE")
    stepsFormLayout.addRow(self.loadfoie)
    
    # Apply Button
    self.applyButton = qt.QPushButton(u"Ex\u00e9cuter")
    self.applyButton.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.applyButton.enabled = True
    self.applyButton.setMaximumWidth(350)
    stepsFormLayout.addRow(self.applyButton)
    
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
    stepsFormLayout.addRow(u"  Volume de la cavit\u00e9 segment\u00e9e :                        ", self.inputSelector1)
    
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
    stepsFormLayout.addRow(u"  Volume du foie segment\u00e9 apr\u00e8s recalage :                        ", self.inputSelector2)
    
    # Superposition Button
    self.superposButton = qt.QPushButton(u"Superposer les segmentations")
    self.superposButton.toolTip = u"Ex\u00e9cuter l\u00b4algorithme."
    self.superposButton.enabled = True
    self.superposButton.setMaximumWidth(350)
    stepsFormLayout.addRow(self.superposButton)
    
    # Connections
    self.loadcavite.connect("clicked(bool)", self.onSelect)
    self.loadfoie.connect("clicked(bool)", self.onSelect)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.superposButton.connect('clicked(bool)', self.onSuperposButton)
    
    # Add vertical spacer
    self.layout.addStretch(1)
        
        
  def cleanup(self):
    pass
                
  def onSelect(self):
    # Recherche du fichier NIFTI pour charger la cavite segmentee
    if self.loadcavite.checked:
      self.VolumeNodecavite = os.path.join(os.path.expanduser("~"),"Documents/TroisDSlicer/Imageasuperposer/")
      slicer.util.openAddVolumeDialog()
      self.masterVolumeNode = self.VolumeNodecavite
    
      cavite = slicer.util.getNode('CaviteAbdoReceveur')
      volumeLogic = slicer.modules.volumes.logic()
      volrefcavite = volumeLogic.CloneVolume(slicer.mrmlScene, cavite, 'CaviteAbdoReceveur_Labelmap')
    
      volextractcavite = slicer.util.getNode('CaviteAbdoReceveur_Labelmap')
      vollabelcavite = volumeLogic.CreateAndAddLabelVolume(slicer.mrmlScene, volextractcavite, "Label_volume_cavite" )
      self.labelNodeCavite = volumeLogic.CreateLabelVolumeFromVolume(slicer.mrmlScene, vollabelcavite, volextractcavite)


      # Recherche du fichier NIFTI pour charger le foie segmente
    if self.loadfoie.checked:
      self.VolumeNodefoie = os.path.join(os.path.expanduser("~"),"Documents/TroisDSlicer/Imageasuperposer/")
      slicer.util.openAddVolumeDialog()
      self.masterVolumeNode = self.VolumeNodefoie

      foie = slicer.util.getNode('FoieSegmenteDonneur')
      volumeLogic = slicer.modules.volumes.logic()
      volreffoie = volumeLogic.CloneVolume(slicer.mrmlScene, foie, 'FoieSegmenteDonneur_Labelmap')
          
      volextractfoie = slicer.util.getNode('FoieSegmenteDonneur_Labelmap')
      vollabelfoie = volumeLogic.CreateAndAddLabelVolume(slicer.mrmlScene, volextractfoie, "Label_volume_foie" )
      self.labelNodeFoie = volumeLogic.CreateLabelVolumeFromVolume(slicer.mrmlScene, vollabelfoie, volextractfoie)
    
    self.applyButton.enabled = self.masterVolumeNode
                                                        
                                                        
  def onApplyButton(self):
      # Creer segmentation a partir labelmap
    volumeLogic = slicer.modules.volumes.logic()

    labelmapVolumeNodecavite = slicer.util.getNode('Label_volume_cavite')
    segmentationcavite = volumeLogic.CloneVolume(slicer.mrmlScene, labelmapVolumeNodecavite, 'SegmentationCaviteAbdoReceveur_Labelmap')
    segcavite = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(segmentationcavite, segcavite)
    segcavite.CreateClosedSurfaceRepresentation()
    slicer.mrmlScene.RemoveNode(segmentationcavite)
    
    
    labelmapVolumeNodefoie = slicer.util.getNode('Label_volume_foie')
    segmentationfoie = volumeLogic.CloneVolume(slicer.mrmlScene, labelmapVolumeNodefoie, 'SegmentationFoieSegmenteDonneur_Labelmap')
    seg = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(segmentationfoie, seg)
    seg.CreateClosedSurfaceRepresentation()
    slicer.mrmlScene.RemoveNode(segmentationfoie)

    reformatModuleWidget = slicer.modules.segmentregistration.createNewWidgetRepresentation()
    reformatModuleWidget.setMRMLScene(slicer.app.mrmlScene())
    reformatModuleWidget.show()
        
        
  def onSuperposButton(self):
    logic = SuperpositionFoieCaviteLogic()
    lm = slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    VolumeNodecavite = self.inputSelector1.currentNode()
    VolumeNodefoie = self.inputSelector2.currentNode()
    
    # Affichage de la superposition entre le foie segmente et recale et la cavite abdominale segmentee
    lm = slicer.app.layoutManager()
    for sliceViewName in lm.sliceViewNames():
      sliceWidget = lm.sliceWidget(sliceViewName)
      view = lm.sliceWidget(sliceViewName).sliceView()
      sliceNode = view.mrmlSliceNode()
      sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
      compositeNode = sliceLogic.GetSliceCompositeNode()
    # Volume du fond = volume du foie segmente puis recale par le module General Registration
      compositeNode.SetBackgroundVolumeID(VolumeNodefoie.GetID())
    # Volume au premier plan = volume de la cavite abdominale segmentee
      compositeNode.SetForegroundVolumeID(VolumeNodecavite.GetID())
    # Changer l'opacite du volume au premier plan
      compositeNode.SetForegroundOpacity(0.3)
                                                                                                                                        
    # Sauvegarde du volume du foie segmente puis recale au format NIFTI
    slicer.util.saveNode(VolumeNodefoie, '~\Documents\TroisDSlicer\FoieRecalage.nii')
    # Sauvegarde des elements de la scene dans un dossier
    filename = os.path.join(os.path.expanduser("~"),'\Documents\TroisDSlicer\FoieRecalageData')
    slicer.util.saveScene(filename)


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
  def setUp(self):
    slicer.mrmlScene.Clear(0)
    
  def runTest(self):
    self.setUp()
    self.test_SuperpositionFoieCavite1()
        
  def test_SuperpositionFoieCavite1(self):
    self.delayDisplay("Starting the test")
    self.delayDisplay('Test passed !')
