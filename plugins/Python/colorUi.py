import sys
#from compiler.ast import Node
sys.dont_write_bytecode=1

from rv import rvtypes, commands, extra_commands
from PySide import QtGui,QtCore, QtUiTools
import os
import colorUi # need to get at the module itself

import qtColorWheel
import logging
import shiboken

import re

_log = logging.getLogger('colorUi')


class ColorUi(rvtypes.MinorMode):
    "interface for rvs color node"
    
    def __init__(self):
        rvtypes.MinorMode.__init__(self)
        
        self.showOnStartup = commands.readSettings("rvColorUi", "showOnStartUp", False)
        self.copySourceToNuke = commands.readSettings("rvColorUi", "copySourceToNuke", False)

        self.init("color-ui", 
                  None, 
                  None,
                  [("Color Ui",
                    [("Show Color Interface", self.showUi,"", None),
                     ("Copy to Nuke", self.createNodesForNuke,"", None),
                     ("Propagate to All", self.propagateToAllRvColor,"", None),
                     ("Preferences",
                      [("show Color Ui on Startup", self.toggleShowOnStartup, "", self.showOnStartupState),
                       ("copy Source to Nuke", self.toggleCopyToNuke,"",self.copyToNukeState)
                       ]
                      )
                     ]
                    )] 
                  )
        self.NOT_INIT = True
        self.node = ''
        if self.showOnStartup:
            self.showUi('') #need to pass sth to event
        
    def initUi(self):
        self.loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(os.path.join(self.supportPath(colorUi, "colorUi"), "colorUiGui.ui"))
        uifile.open(QtCore.QFile.ReadOnly)
        self.widgets = self.loader.load(uifile)

        self.colorWheelScale = qtColorWheel.ColorWheelWidget(name='scale')
        self.colorWheelGamma = qtColorWheel.ColorWheelWidget(name='gamma')
        self.colorWheelExposure = qtColorWheel.ColorWheelWidget(name='exposure')
        self.colorWheelOffset = qtColorWheel.ColorWheelWidget(name='offset')
        
        self.widgets.gainWheel.takeAt(0) 
        self.widgets.gainWheel.insertWidget(0,self.colorWheelScale)
        self.widgets.gammaWheel.takeAt(0) 
        self.widgets.gammaWheel.insertWidget(0,self.colorWheelGamma)
        self.widgets.exposureWheel.takeAt(0) 
        self.widgets.exposureWheel.insertWidget(0,self.colorWheelExposure)
        self.widgets.offsetWheel.takeAt(0) 
        self.widgets.offsetWheel.insertWidget(0,self.colorWheelOffset)

        uifile.close()
         
        for w in QtGui.qApp.allWidgets():
            if w.inherits("QMainWindow"):
                ptr = shiboken.getCppPointer(w)
                self.mainWindow = shiboken.wrapInstance(long(ptr[0]), QtGui.QMainWindow)
                self.dialog = QtGui.QDockWidget("color ui", self.mainWindow)
                self.mainWindow.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dialog)
        self.dialog.setWidget(self.widgets)

        self.active  = self.dialog.findChild(QtGui.QCheckBox, "active")
        self.invert  = self.dialog.findChild(QtGui.QCheckBox, "invert")
        self.createNodesNuke  = self.dialog.findChild(QtGui.QPushButton, "createNodesNuke")
        self.propagateToAllColor = self.dialog.findChild(QtGui.QPushButton, "propagateToAllColor")
        self.getSettingsNuke = self.dialog.findChild(QtGui.QPushButton, "getSettingsNuke")
        self.resetButton = self.dialog.findChild(QtGui.QPushButton, "reset")
        
        self.normalize  = self.dialog.findChild(QtGui.QCheckBox, "normalize")
        self.scaleCheck  = self.dialog.findChild(QtGui.QCheckBox, "gainCheckbox")
        self.gammaCheck  = self.dialog.findChild(QtGui.QCheckBox, "gammaCheckbox")
        self.exposureCheck = self.dialog.findChild(QtGui.QCheckBox, "exposureCheckbox")
        self.offsetCheck  = self.dialog.findChild(QtGui.QCheckBox, "offsetCheckbox")
        self.saturation = self.dialog.findChild(QtGui.QDoubleSpinBox, "saturation")
        self.hue = self.dialog.findChild(QtGui.QDoubleSpinBox, "hue")
        self.gamma = self.findSet(QtGui.QDoubleSpinBox, ["gammaRed", "gammaGreen", "gammaBlue"])
        self.scale = self.findSet(QtGui.QDoubleSpinBox, ["gainRed", "gainGreen", "gainBlue"])
        self.offset = self.findSet(QtGui.QDoubleSpinBox, ["offsetRed", "offsetGreen", "offsetBlue"])
        self.exposure = self.findSet(QtGui.QDoubleSpinBox, ["exposureRed", "exposureGreen", "exposureBlue"])
        
        commands.bind("default", "global", "frame-changed", self.onFrameChangeAndAddDelSource, 'New frame')
        commands.bind("default", "global", "source-group-complete", self.onFrameChangeAndAddDelSource, 'New frame')
        commands.bind("default", "global", "after-source-delete", self.onFrameChangeAndAddDelSource, 'New frame')
        
        #commands.bind("default", "global", "graph-state-change", self.onGraphStateChange, 'New frame')
        #maybe put the update in a thread to get rid of the sluggishness
        
        #connections for the wheels
        self.colorWheelScale.colorSignal.connect(self.changeRvColor)
        self.colorWheelGamma.colorSignal.connect(self.changeRvColor)
        self.colorWheelExposure.colorSignal.connect(self.changeRvColor)
        self.colorWheelOffset.colorSignal.connect(self.changeRvColor)
        
        #connections for the toggle states
        self.scaleCheck.stateChanged.connect(lambda: self.toggleCorrection('scale'))
        self.gammaCheck.stateChanged.connect(lambda: self.toggleCorrection('gamma'))
        self.exposureCheck.stateChanged.connect(lambda: self.toggleCorrection('exposure'))
        self.offsetCheck.stateChanged.connect(lambda: self.toggleCorrection('offset'))
        
        #connections to the helper functions
        self.createNodesNuke.clicked.connect(self.createNodesForNuke)
        self.propagateToAllColor.clicked.connect(self.propagateToAllRvColor)
        self.resetButton.clicked.connect(self.resetAllUi)
        
    def toggleShowOnStartup(self,event):
        if not self.showOnStartup:
            commands.writeSettings("rvColorUi", "showOnStartUp", True)
            self.showOnStartup = True
        else:
            commands.writeSettings("rvColorUi", "showOnStartUp", False)
            self.showOnStartup = False

    def showOnStartupState(self):
        if self.showOnStartup:
            return commands.CheckedMenuState
        else:
            return commands.UncheckedMenuState
        
    def toggleCopyToNuke(self,event):
        if not self.copySourceToNuke:
            commands.writeSettings("rvColorUi", "copySourceToNuke", True)
            self.copySourceToNuke = True
        else:
            commands.writeSettings("rvColorUi", "copySourceToNuke", False)
            self.copySourceToNuke = False

    def copyToNukeState(self):
        if self.copySourceToNuke:
            return commands.CheckedMenuState
        else:
            return commands.UncheckedMenuState

    def checkBoxPressed(self, checkbox, prop):
        def F():
            try:
                if checkbox.isChecked():
                    commands.setIntProperty(prop, [1], True)
                else:
                    commands.setIntProperty(prop, [0], True)
            except Exception, e:
                print e
        return F
    
    @QtCore.Slot(list)
    def changeRvColor(self, values):
        '''
        changes the rv color node coming from the colorwheels
        @param values: list [float,float,float,string,Bool]
        '''
        property = values[-2]
        updateSpinBoxes = values[-1]
        if property in ('exposure','offset'):
            rgb = [x-1.0 for x in values[:-2]]
        else:
            rgb = values[:-2]
        try:
            commands.setFloatProperty("%s.color.%s" % (self.node,property), rgb, True)
        except Exception, e:
            print e
        else:
            if updateSpinBoxes:
                self.updateSpinBoxes(property,rgb)
            
    @QtCore.Slot(str)
    def changeRvColorFromSpinBox(self, property):
        change = getattr(self, property)
        rgb = self.getValuesFromList(change)
        try:
            commands.setFloatProperty("%s.color.%s" % (self.node,property), rgb, True)
        except Exception, e:
            print e
    
    @QtCore.Slot(str)
    def toggleCorrection(self,property):
        change = getattr(self, 'colorWheel%s' % property.capitalize())
        box = getattr(self, '%sCheck' %property)
        print change
        print box
        if not box.isChecked():
            change.colorSignal.disconnect(self.changeRvColor)
            rgb = [1.0,1.0,1.0,property,False]
            if property in ('exposure','offset'):
                rgb = [0.0,0.0,0.0,property,False]
            self.changeRvColor(rgb)
        else:
            change.colorSignal.connect(self.changeRvColor)
            self.updateSpinBoxes(property, change.getRgbFloat()[:-2])
            self.changeRvColorFromSpinBox(property)
            
    def updateSpinBoxes(self,property,rgb):
        change = getattr(self, property)
        if not isinstance(change, list):
            change.setValue(rgb[0])
            return
        for e,color in enumerate(rgb):
            change[e].setValue(color)
            
    def findSet(self, typeObj, names):
        array = []
        for n in names:
            array.append(self.dialog.findChild(typeObj, n))
            if array[-1] == None:
                print "Can't find", n
        return array

    def getValuesFromList(self,x):
        if isinstance(x, list):
            ret = list()
            for e,item in enumerate(x):
                ret.append(item.value())
        else:
            ret = [x.value()]
        return ret

    def getCurrentColorNode(self):
        check = commands.nodesOfType('RVSource')
        if check:
            sourceNode = extra_commands.sourceMetaInfoAtFrame(commands.frame(), commands.viewNode())
            nodes = commands.nodesOfType('RVColor')
            for node in nodes:
                if node.startswith(sourceNode.get('node','').split('_')[0]):
                    _log.info('found %s' % node)
                    return node
        else:
            return
        
    def onGraphStateChange(self,event):
        '''
        used to get updates from the color node
        wanted to get the shortcuts relfected in the ui too
        might be better to just override the shortcuts exactly in this module than link to updates from the nodegraph
        '''
        x = event.contents()
        #y = event.contentType()
        print x
        self.node = self.getCurrentColorNode()
        for gamma in self.gamma:
            try:
                gamma.valueChanged.disconnect(lambda: self.changeRvColorFromSpinBox("gamma"))
            except:
                pass

        #self.updateSpinBoxes('scale', [x for x in commands.getFloatProperty("%s.color.scale" % self.node,0,2500)])
        self.updateSpinBoxes('gamma', [x for x in commands.getFloatProperty("%s.color.gamma" % self.node,0,2500)])
        #self.updateSpinBoxes('exposure', [x for x in commands.getFloatProperty("%s.color.exposure" % self.node,0,2500)])
        #self.updateSpinBoxes('offset', [x for x in commands.getFloatProperty("%s.color.offset" % self.node,0,2500)])
        for gamma in self.gamma:
            gamma.valueChanged.connect(lambda: self.changeRvColorFromSpinBox("gamma"))
        
    def onFrameChangeAndAddDelSource(self, event):
        '''
        do the main updates in here
        first update the gui with the current settings from the RVColor Node
        then connect to the gui change events update procedures on the RVColor Node
        '''
        
        node = self.getCurrentColorNode()
        if node == self.node:
            return #we do not have to run updates if we are still on the same color node as all connections are set
        else:
            self.node=node
        ##this seems to not be working as the color active is not a per node setting ?! need to ask support
        if int(commands.getIntProperty("%s.color.active" % self.node,0,2500)[0]) == int(1):
            self.active.setCheckState(QtCore.Qt.Checked)
        else:
            self.active.setCheckState(QtCore.Qt.Unchecked)
        
        self.updateSpinBoxes('scale', [x for x in commands.getFloatProperty("%s.color.scale" % self.node,0,2500)])
        self.updateSpinBoxes('gamma', [x for x in commands.getFloatProperty("%s.color.gamma" % self.node,0,2500)])
        self.updateSpinBoxes('exposure', [x for x in commands.getFloatProperty("%s.color.exposure" % self.node,0,2500)])
        self.updateSpinBoxes('offset', [x for x in commands.getFloatProperty("%s.color.offset" % self.node,0,2500)])
        self.updateSpinBoxes('saturation', [x for x in commands.getFloatProperty("%s.color.saturation" % self.node,0,2500)])
        self.updateSpinBoxes('hue', [x for x in commands.getFloatProperty("%s.color.hue" % self.node,0,2500)])
        
        self.active.released.connect(self.checkBoxPressed(self.active, "%s.color.active" % self.node))
        self.invert.released.connect(self.checkBoxPressed(self.invert, "%s.color.invert" % self.node))
        
        for gamma in self.gamma:
            gamma.valueChanged.connect(lambda: self.changeRvColorFromSpinBox("gamma"))
        for scale in self.scale:
            scale.valueChanged.connect(lambda: self.changeRvColorFromSpinBox("scale"))
        for offset in self.offset:
            offset.valueChanged.connect(lambda: self.changeRvColorFromSpinBox("offset"))
        for exp in self.exposure:
            exp.valueChanged.connect(lambda: self.changeRvColorFromSpinBox("exposure"))
        
        self.saturation.valueChanged.connect(lambda: self.changeRvColorFromSpinBox("saturation"))
        self.hue.valueChanged.connect(lambda: self.changeRvColorFromSpinBox("hue"))
        
        
    def filterClipboardfromNuke(self):
        clipboard = QtGui.QApplication.clipboard()
        text = clipboard.text()
        #pattern detect grades and saturation nodes iterate through them and sum them up and apply the changes to 
        #rvs color node
        pattern = re.compile(r'(Saturation \{[a-zA-Z0-9{}]+\}|Grade \{[a-zA-Z0-9{}]+\})')
        
    def testValueList(self, values, filter):
        '''
        filter a list for a given value return false if all values match filter
        '''
        for i in values:
            if i != filter:
                return True
        return False
        
    def sanityCheckUpdatesForClipboard(self,values,filter,name):
        ret = False
        if self.testValueList(values, filter):
            if self.NOT_INIT:
                ret = True
            else:
                checkbox = getattr(self, '%sCheck' % name)
                if checkbox.isChecked():
                    ret = True
        return ret
    
    def createNodesForNuke(self,*event):
        '''
        creates nodes for nuke and copys them to the clipboard
        ctrl+v in nuke creates them

        Grade {
         white {0.9 1 1 1} gain
         multiply 1.1 abused to represent exposure
        }
        Saturation {
         saturation 0.9 saturation
        }
        '''
        self.node = self.getCurrentColorNode()
        if not self.node:
            return
        scale = [x for x in commands.getFloatProperty("%s.color.scale" % self.node,0,2500)]
        exposure = [x+1 for x in commands.getFloatProperty("%s.color.exposure" % self.node,0,2500)]
        offset =  [x for x in commands.getFloatProperty("%s.color.offset" % self.node,0,2500)]
        gamma =  [x for x in commands.getFloatProperty("%s.color.gamma" % self.node,0,2500)]
        saturation = [x for x in commands.getFloatProperty("%s.color.saturation" % self.node,0,2500)]
        
        text = ''
        if self.sanityCheckUpdatesForClipboard(scale, 1.0, 'scale') :
            text +=' white {%s %s %s 1}\n' % (scale[0],scale[1],scale[2])
        if self.sanityCheckUpdatesForClipboard(exposure, 1.0,'exposure') :
            text +=' multiply {%s %s %s 1}\n' % (exposure[0],exposure[1],exposure[2])
        if self.sanityCheckUpdatesForClipboard(offset, 0.0,'offset'):
            text +=' add {%s %s %s 1}\n' % (offset[0],offset[1],offset[2])
        if self.sanityCheckUpdatesForClipboard(gamma, 1.0, 'gamma'):
            text +=' gamma {%s %s %s 1}\n' % (gamma[0],gamma[1],gamma[2])
            
        if text:
            text ='Grade {\n%s}\n\n' % (text)
        if self.testValueList(saturation, 1.0):
            text +='Saturation {\n'
            text +=' saturation %s\n' % saturation
            text +='}\n'
        if self.copySourceToNuke:
            # build a read node and prepend it to text
            pass
        
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(text)
            
    def propagateToAllRvColor(self,*event):
        '''
        sets the current settings to all rvcolor nodes found 
        '''
        self.node = self.getCurrentColorNode()
        if not self.node:
            return
        nodes = commands.nodesOfType('RVColor')
        propList = ['gamma','scale','offset','exposure','saturation']
        for node in nodes:
            for prop in propList:
                values = [x for x in commands.getFloatProperty("%s.color.%s" % (self.node,prop),0,2500)]
                try:
                    if node != self.node:
                        commands.setFloatProperty("%s.color.%s" % (node,prop), values, True)
                except Exception, e:
                    print e

    def resetAllUi(self):
        for wheel in [self.colorWheelScale,self.colorWheelExposure,self.colorWheelGamma,self.colorWheelOffset]:
            x= '' # need to see what this is for
            wheel.reset(x)
        for check in [self.scaleCheck,self.gammaCheck,self.exposureCheck,self.offsetCheck]:
            check.setCheckState(QtCore.Qt.Checked)
        self.saturation.setValue(1.0)

    def showUi(self, event):
        if self.NOT_INIT:
            self.initUi()
            self.NOT_INIT = False
        self.dialog.show()
        self.node = self.getCurrentColorNode()
        
    def activate(self):
        rvtypes.MinorMode.activate(self)

    def deactivate(self):
        rvtypes.MinorMode.deactivate(self)
        self.dialog.hide()

def createMode():
    "Required to initialize the module. RV will call this function to create your mode."
    return ColorUi()
