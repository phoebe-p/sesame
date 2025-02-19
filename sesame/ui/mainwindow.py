# Copyright 2017 University of Maryland.
#
# This file is part of Sesame. It is subject to the license terms in the file
# LICENSE.rst found in the top-level directory of this distribution.

from .system_tab import BuilderBox
from .simulation_tab import Simulation
from .analysis_tab import Analysis
from .. import plotter
from .common import parseSettings, slotError

import sys
import os
os.environ['QT_API'] = 'pyqt5'
import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from qtconsole.rich_ipython_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython import version_info
from IPython.lib import guisupport

from configparser import ConfigParser
config = ConfigParser()
config.optionxform = str
config.add_section('System')
config.add_section('Simulation')

from ast import literal_eval as ev


def absolute_path(relative_path):
    # The absolute path depends on whether or not the package is frozen
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
 
    return os.path.join(os.path.dirname(__file__), relative_path)


class Window(QMainWindow): 
    """
    Class defining the main window of the GUI.
    """
    def __init__(self):
        super(Window, self).__init__()

        self.init_ui()

    def init_ui(self):
        'init the UI'

        #============================================
        # Menu bar
        #============================================
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)

        # File menu
        fileMenu = menuBar.addMenu("&File")
        newAction = QAction('New', self)
        openAction = QAction('Open...', self)
        saveAction = QAction('Save', self)
        saveAsAction = QAction('Save as...', self)
        exitAction = QAction('Exit', self)
        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addSeparator()
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        # IPython menu
        ipythonMenu = menuBar.addMenu("&Console")
        ip1 = QAction('Show console', self)
        ipythonMenu.addAction(ip1)

        # actions
        newAction.triggered.connect(self.newConfig)
        openAction.triggered.connect(self.openConfig)
        saveAction.triggered.connect(self.saveConfig)
        saveAsAction.triggered.connect(self.saveAsConfig)
        exitAction.triggered.connect(self.close)
        ip1.triggered.connect(lambda: self.dock.show())

        #============================================
        # Window settings
        #============================================
        # Window title and icon
        self.setWindowTitle('Sesame')
        icon = absolute_path('resources'+os.path.sep+'logo-icon_sesame.png')
        QApplication.setWindowIcon(QIcon(icon))
        # Create geomtry and center the window
        self.setGeometry(0,0,1525,775)
        windowFrame = self.frameGeometry()
        screenCenter = QDesktopWidget().availableGeometry().center()
        windowFrame.moveCenter(screenCenter)
        self.move(windowFrame.topLeft())

        # Set window tabs
        self.table = TableWidget(self)
        self.setCentralWidget(self.table)

        # Create and hide a dock for an IPython console
        self.dock = QDockWidget("  IPython console", self)
        self.ipython = IPythonWidget(self)
        self.dock.setWidget(self.ipython)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock)
        self.dock.hide()

        # Show the interface
        self.show()

    def setSystem(self, grid, materials, defects, gen, param, onesun, manual_generation, \
                  ill_monochromatic, ill_wavelength, ill_power, abs_usefile, abs_file, \
                           abs_useralpha, abs_alpha):
        """
        Fill out all fields of the interface system tab with the settings from
        the configuration file.  
        """
        
        # system tab instance 
        build = self.table.build
        
        # edit QLineEdit widgets
        build.g1.setText(grid[0])
        build.g2.setText(grid[1])
        build.g3.setText(grid[2])
        build.gen.setText(gen)
        build.paramName.setText(param)

        if onesun=='True':
            build.onesun.setChecked(True)
        else:
            build.onesun.setChecked(False)

        if manual_generation=='True':
            build.man_gen.setChecked(True)
        else:
            build.man_gen.setChecked(False)

        if abs_useralpha=='True':
            build.useralpha.setChecked(True)
        else:
            build.useralpha.setChecked(False)

        if abs_usefile=='True':
            build.absfile.setChecked(True)
        else:
            build.absfile.setChecked(False)

        if ill_monochromatic=='True':
            build.monochromatic.setChecked(True)
        else:
            build.monochromatic.setChecked(False)

        build.wavelength.setText(ill_wavelength)
        build.power.setText(ill_power)
        build.alpha.setText(abs_alpha)
        build.alphafile.setText(abs_file)



        # set materials
        build.materials_list = materials
        build.matNumber = -1
        build.box.clear()
        build.loc.clear()
        for mat in materials:
            # location
            build.loc.setText(mat['location'])
            # add "material number" to combo box
            build.matNumber += 1
            build.box.addItem("Material " + str(build.matNumber+1))
            build.box.setCurrentIndex(build.matNumber)
            # fill in table with material values
            values = [mat['N_D'], mat['N_A'],\
                      mat['Nc'], mat['Nv'], mat['Eg'], mat['epsilon'],\
                      mat['mass_e'], mat['mass_h'], mat['mu_e'], mat['mu_h'],\
                      mat['Et'], mat['tau_e'], mat['tau_h'], mat['affinity'],\
                      mat['B'], mat['Cn'], mat['Cp']]
            for idx, (val, unit) in enumerate(zip(values, build.units)):
                build.table.setItem(idx,0, QTableWidgetItem(str(val)))
                item = QTableWidgetItem(unit)
                item.setFlags(Qt.ItemIsEnabled)
                build.table.setItem(idx,1, item)
            build.table.show()
            build.loc.show()
            build.lbl.show()
        # Disable remove and new buttons, enable save button
        if len(build.materials_list) > 1:
            build.removeButton.setEnabled(True)
        build.newButton.setEnabled(True)
        build.saveButton.setEnabled(True)

        # set defects properties 
        build.defects_list = defects
        build.defectNumber = -1
        build.defectBox.clear()
        build.cloc.clear()
        for defect in defects:
            # location
            build.cloc.setText(defect['location'])
            # add "defect number" to combo box
            build.defectNumber += 1
            build.defectBox.addItem("Defect " + str(build.defectNumber+1))
            build.defectBox.setCurrentIndex(build.defectNumber)
            # fill in table with defect values
            defectValues = [defect['Energy'], defect['Density'],\
                            defect['sigma_e'], defect['sigma_h'],\
                            defect['Transition']]
            for idx, (val, unit) in enumerate(zip(defectValues, build.units2)):
                build.ctable.setItem(idx,0, QTableWidgetItem(str(val)))
                item = QTableWidgetItem(unit)
                item.setFlags(Qt.ItemIsEnabled)
                build.ctable.setItem(idx,1, item)
            build.ctable.show()
            build.cloc.show()
            build.clbl.show()
        if len(build.defects_list) > 0:
            # Enable save button
            build.saveButton2.setEnabled(True)
            build.removeButton2.setEnabled(True)

        # plot system
        if grid != ['', '', '']:
            settings = build.getSystemSettings()
            settings['periodicBCs'] = True
            system = parseSettings(settings)
            build.Fig.plotSystem(system, materials, defects)
        else:
            build.Fig.ax.clear()
            build.Fig.canvas.draw()



    def setSimulation(self, voltageLoop, loopValues, workDir, fileName, ext,\
                      BCs, L_contact, R_contact, L_WF, R_WF,\
                      ScnL, ScpL, ScnR, ScpR,\
                      precision, maxSteps, useMumps, iterative, ramp,\
                      iterPrec, htpy):
        """
        Fill out all fields of the interface simulation tab with the settings
        from the configuration file.  
        """
        if voltageLoop:
            self.table.simulation.voltage.setChecked(True)
        else:
            self.table.simulation.other.setChecked(True)
        self.table.simulation.loopValues.setText(loopValues)
        self.table.simulation.workDirName.setText(workDir)
        self.table.simulation.fileName.setText(fileName)
        if ext == '.npz':
            self.table.simulation.fbox.setCurrentIndex(0)
        elif ext == '.mat':
            self.table.simulation.fbox.setCurrentIndex(1)
        if BCs:
            self.table.simulation.periodic.setChecked(True)
        else:
            self.table.simulation.hardwall.setChecked(True)
        if L_contact == 'Ohmic':
            self.table.simulation.L_Ohmic.setChecked(True)
        if L_contact == 'Schottky':
            self.table.simulation.L_Schottky.setChecked(True)
        if L_contact == 'Neutral':
            self.table.simulation.L_Neutral.setChecked(True)
        if R_contact == 'Ohmic':
            self.table.simulation.R_Ohmic.setChecked(True)
        if R_contact == 'Schottky':
            self.table.simulation.R_Schottky.setChecked(True)
        if R_contact == 'Neutral':
            self.table.simulation.R_Neutral.setChecked(True)
        self.table.simulation.g4.setText(ScnL)
        self.table.simulation.g5.setText(ScpL)
        self.table.simulation.g6.setText(ScnR)
        self.table.simulation.g7.setText(ScpR)
        self.table.simulation.g8.setText(L_WF)
        self.table.simulation.g9.setText(R_WF)
        self.table.simulation.algoPrecision.setText(precision)
        self.table.simulation.algoSteps.setValue(int(maxSteps))
        if useMumps:
            self.table.simulation.yesMumps.setChecked(True)
        else:
            self.table.simulation.noMumps.setChecked(True)
        if iterative:
            self.table.simulation.yesIterative.setChecked(True)
        else:
            self.table.simulation.noIterative.setChecked(True)
        self.table.simulation.ramp.setValue(int(ramp))
        self.table.simulation.iterPrecision.setText(iterPrec)
        self.table.simulation.htpy.setValue(int(htpy))
        
    def newConfig(self):
        """
        Reset all the fields of the interface to their original values.
        """

        # system and simulation tabs
        grid = ['', '', '']
        materials = [{'Nc': 1e19, 'Nv': 1e19, 'Eg': 1., 'epsilon': 10., 'mass_e': 1., \
              'mass_h': 1., 'mu_e': 100., 'mu_h': 100., 'Et': 0., \
              'tau_e': 1e-6, 'tau_h': 1e-6, 'affinity': 0., \
              'B': 0., 'Cn': 0., 'Cp': 0., 'location': '', 'N_D':0., 'N_A':0.}]

        self.setSystem(grid, materials, [], '', '',\
                        'False', 'False', 'False', '', '', 'False', '', 'False', '')
        self.setSimulation(True, '', '', '',  '.npz', True, 'Ohmic', 'Ohmic',\
                           '', '', '1e5', '1e5', '1e5', '1e5', '1e-6',\
                           '100', False, False, '0', '1e-6', '1')

        # analysis tab
        self.table.simulation.logWidget.clear()
        self.table.analysis.dataList.clear()
        self.table.analysis.filesList = []
        self.table.analysis.radioPos.setChecked(False)
        self.table.analysis.radioLoop.setChecked(False)
        self.table.analysis.Xdata.setText('')

        self.table.analysis.linearFig.canvas.figure.clear()
        self.table.analysis.linearFig.figure.add_subplot(111)
        self.table.analysis.linearFig.canvas.draw()
        self.table.analysis.iterColors = iter(self.table.analysis.colors)
        self.table.analysis.surfaceFig.canvas.figure.clear()
        self.table.analysis.surfaceFig.figure.add_subplot(111)
        self.table.analysis.surfaceFig.canvas.draw()
        


    def openConfig(self):
        """
        Open and read the configuration of the interface system and simulation
        tabs. This file must end with extension .ini.
        """
        self.cfgFile = QFileDialog.getOpenFileName(self, 'Open File', '',\
                        "(*.ini)")[0]
        if self.cfgFile == '':
            return

        with open(self.cfgFile, 'r') as f:
            try:
                config.read(self.cfgFile)
            except:
                f.close()
                msg = QMessageBox()
                msg.setWindowTitle("Processing error")
                msg.setIcon(QMessageBox.Critical)
                msg.setText("The file could not be read.")
                msg.setEscapeButton(QMessageBox.Ok)
                msg.exec_()
                return

            grid = config.get('System', 'Grid')
            materials = config.get('System', 'Materials')
            defects = config.get('System', 'Defects')
            gen, param = config.get('System', 'Generation rate'),\
                         config.get('System', 'Generation parameter')
            ill_onesun = config.get('System', 'One sun illumination')
            man_gen = config.get('System', 'Use manual generation')

            ill_monochromatic = config.get('System', 'Monochromatic illumination')
            ill_wavelength = config.get('System', 'Illumination wavelength')
            ill_power = config.get('System', 'Illumination power')
            abs_usefile = config.get('System', 'Use absorption file')
            abs_file = config.get('System', 'Absorption file')
            abs_useralpha = config.get('System', 'Use user-defined alpha')
            abs_alpha = config.get('System', 'Alpha')

            self.setSystem(ev(grid), ev(materials), ev(defects), gen, param, ill_onesun, man_gen, \
                           ill_monochromatic, ill_wavelength, ill_power, abs_usefile, abs_file, \
                           abs_useralpha, abs_alpha)

            voltageLoop = config.getboolean('Simulation', 'Voltage loop')
            loopValues = config.get('Simulation', 'Loop values')
            workDir = config.get('Simulation', 'Working directory')
            fileName = config.get('Simulation', 'Simulation name')
            ext = config.get('Simulation', 'Extension')
            BCs = config.getboolean('Simulation', 'Transverse boundary conditions')
            ScnL = config.get('Simulation', 'Electron recombination velocity in 0')
            ScpL = config.get('Simulation', 'Hole recombination velocity in 0')
            ScnR = config.get('Simulation', 'Electron recombination velocity in L')
            ScpR = config.get('Simulation', 'Hole recombination velocity in L')
            L_contact = config.get('Simulation', 'Contact boundary condition in 0')
            R_contact = config.get('Simulation', 'Contact boundary condition in L')
            L_WF = config.get('Simulation', 'Contact work function in 0')
            R_WF = config.get('Simulation', 'Contact work function in L')
            precision = config.get('Simulation', 'Newton precision')
            maxSteps = config.get('Simulation', 'Maximum steps')
            useMumps = config.getboolean('Simulation', 'Use Mumps')
            iterative = config.getboolean('Simulation', 'Iterative solver')
            ramp = config.get('Simulation', 'Generation ramp')
            iterPrec = config.get('Simulation', 'Iterative solver precision')
            htpy = config.get('Simulation', 'Newton homotopy')
            self.setSimulation(voltageLoop, loopValues, workDir, fileName, \
                               ext, BCs, L_contact, R_contact, L_WF, R_WF,\
                               ScnL, ScpL, ScnR, ScpR, precision,\
                               maxSteps, useMumps, iterative, ramp,\
                               iterPrec, htpy)
            f.close()

    def saveAsConfig(self):
        self.cfgFile = QFileDialog.getSaveFileName(self, 'Save File', '.ini', \
                        "(*.ini)")[0]
        if self.cfgFile != '':
            # append extension if changed
            if self.cfgFile[-4:] != '.ini':
                self.cfgFile += '.ini'
            self.saveConfig()

    def saveConfig(self):
        """
        Save the configuration of the interface system and simulation
        tabs in a file with extension .ini.
        """

        if not hasattr(self, 'cfgFile'):
            self.saveAsConfig()
        elif self.cfgFile == '':
            return
        else:
            build = self.table.build
            simu = self.table.simulation

            grid = [build.g1.text(), build.g2.text(), build.g3.text()]
            mat = build.materials_list
            defects = build.defects_list
            gen, param = build.gen.text(), build.paramName.text()

            ill_onesun = build.onesun.isChecked()
            ill_monochromatic = build.monochromatic.isChecked()
            ill_wavelength = build.wavelength.text()
            ill_power = build.power.text()
            abs_usefile = build.absfile.isChecked()
            abs_useralpha = build.useralpha.isChecked()
            abs_alpha = build.alpha.text()
            abs_file = build.alphafile.text()
            manual_gen = build.man_gen.isChecked()

            #generation = self.gen.text().replace('exp', 'np.exp')
            #settings['gen'] = generation, self.paramName.text()


            L_WF, R_WF = '', ''
            if simu.L_Ohmic.isChecked():
                L_contact = "Ohmic"
            elif simu.L_Schottky.isChecked():
                L_contact = "Schottky"
                L_WF = simu.g8.text()
            elif simu.L_Neutral.isChecked():
                L_contact = "Neutral"

            if simu.R_Ohmic.isChecked():
                R_contact = "Ohmic"
            elif simu.R_Schottky.isChecked():
                R_contact = "Schottky"
                R_WF = simu.g9.text()
            elif simu.R_Neutral.isChecked():
                R_contact = "Neutral"

            with open(self.cfgFile, 'w') as f:
                config.set('System', 'Grid', str(grid))
                config.set('System', 'Materials', str(mat))
                config.set('System', 'Defects', str(defects))
                config.set('System', 'One sun illumination', str(ill_onesun))
                config.set('System', 'Monochromatic illumination', str(ill_monochromatic))
                config.set('System', 'Illumination Wavelength', ill_wavelength)
                config.set('System', 'Illumination Power', ill_power)
                config.set('System', 'Use absorption file', str(abs_usefile))
                config.set('System', 'Absorption file', abs_file)
                config.set('System', 'Use user-defined alpha', str(abs_useralpha))
                config.set('System', 'Alpha', abs_alpha)
                config.set('System', 'Use manual generation', str(manual_gen))
                config.set('System', 'Generation rate', gen)
                config.set('System', 'Generation parameter', param)

                # basic settings
                config.set('Simulation', 'Voltage loop',\
                                            str(simu.voltage.isChecked()))
                config.set('Simulation', 'Loop values', simu.loopValues.text())
                config.set('Simulation', 'Working directory', simu.workDirName.text())
                config.set('Simulation', 'Simulation name', simu.fileName.text())
                config.set('Simulation', 'Extension', simu.fbox.currentText())
                # boundary conditions
                config.set('Simulation', 'Transverse boundary conditions',\
                            str(simu.periodic.isChecked()))
                config.set('Simulation', 'Contact boundary condition in 0', L_contact)
                config.set('Simulation', 'Contact boundary condition in L', R_contact)
                config.set('Simulation', 'Contact work function in 0', L_WF)
                config.set('Simulation', 'Contact work function in L', R_WF)
                config.set('Simulation', 'Electron recombination velocity in 0',\
                                            simu.g4.text())
                config.set('Simulation', 'Hole recombination velocity in 0',\
                                            simu.g5.text())
                config.set('Simulation', 'Electron recombination velocity in L',\
                                            simu.g6.text())
                config.set('Simulation', 'Hole recombination velocity in L',\
                                            simu.g7.text())
                config.set('Simulation', 'Generation ramp',
                str(simu.ramp.value()))
                config.set('Simulation', 'Newton precision',\
                            simu.algoPrecision.text())
                config.set('Simulation', 'Maximum steps',\
                            str(simu.algoSteps.value()))
                config.set('Simulation', 'Use Mumps',\
                            str(simu.yesMumps.isChecked()))
                config.set('Simulation', 'Iterative solver',\
                            str(simu.yesIterative.isChecked()))
                config.set('Simulation', 'Iterative solver precision',\
                            simu.iterPrecision.text())
                config.set('Simulation', 'Newton homotopy',\
                            str(simu.htpy.value()))
                config.write(f)
                f.close()
        
class QIPythonWidget(RichJupyterWidget):
    """ 
    Convenience class for the definition of a live IPython console widget. We
    replace the standard banner using the sesameBanner argument.
    """ 
    
    def __init__(self, *args, **kwargs):
        super(QIPythonWidget, self).__init__(*args,**kwargs)
        # banners printed at the top of the shell
        self.banner = ''
        banner1 = 'Python ' + sys.version.replace('\n', '')
        banner2 = 'IPython ' + ".".join(map(str, version_info[:3]))
        # create qt console kernel
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.shell.banner1 = banner1
        kernel_manager.kernel.shell.banner2 = banner2
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt5().exit()            
        self.exit_requested.connect(stop)

    def pushVariables(self,variableDict):
        # Given a dictionary containing name / value pairs, push those
        # variables to the IPython console widget 
        self.kernel_manager.kernel.shell.push(variableDict)
    def clearTerminal(self):
        # Clears the terminal
        self._control.clear()    
    def printText(self,text):
        # Prints some plain text to the console
        self._append_plain_text(text)        
    def executeCommand(self,command):
        # Execute a command in the frame of the console widget
        self._execute(command,False)


class IPythonWidget(QWidget):
    """ 
    GUI widget including an IPython console inside a vertical layout. 
    """ 
    
    def __init__(self, parent=None):
        super(IPythonWidget, self).__init__(parent)
        console = QIPythonWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(console)        

class TableWidget(QWidget):
    """
    Definition of the three tabs that make the GUI: system, simulation,
    analysis.
    """
    def __init__(self, parent):
        super(TableWidget, self).__init__(parent)

        self.parent = parent

        self.layout = QHBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.resize(300,200) 

        # Add tabs
        self.tabs.addTab(self.tab1,"System")
        self.tabs.addTab(self.tab2,"Simulation")
        self.tabs.addTab(self.tab3,"Analysis")
        # Add tabs to widget        
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        #============================================
        #  tab1: system parameters
        #============================================
        self.tab1Layout = QHBoxLayout(self.tab1)
        self.build = BuilderBox(self)
        self.tab1Layout.addWidget(self.build)

        #============================================
        #  tab2: run the simulation
        #============================================
        self.tab2Layout = QHBoxLayout(self.tab2)
        self.simulation = Simulation(self)
        self.tab2Layout.addWidget(self.simulation)

        #============================================
        #  tab3: analyze simulation results
        #============================================
        self.tab3Layout = QHBoxLayout(self.tab3)
        self.analysis = Analysis(self)
        self.tab3Layout.addWidget(self.analysis)
