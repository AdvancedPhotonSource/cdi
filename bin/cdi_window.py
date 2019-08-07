import sys
import os
import shutil
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import reccdi.src_py.run_scripts.run_data as run_dt
import reccdi.src_py.run_scripts.run_rec as run_rc
import reccdi.src_py.run_scripts.run_disp as run_dp
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.utilities.spec as spec
import importlib


def select_file(start_dir):
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec_() == QDialog.Accepted:
        return str(dialog.selectedFiles()[0])
    else:
        return None


def select_dir(start_dir):
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.DirectoryOnly)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec_() == QDialog.Accepted:
        return str(dialog.selectedFiles()[0])
    else:
        return None


class cdi_conf(QWidget):
    def __init__(self, parent=None):
        super(cdi_conf, self).__init__(parent)
        self.id = None
        self.scan = None
        self.experiment_dir = None
        uplayout = QFormLayout()

        self.set_work_dir_button = QPushButton()
        uplayout.addRow("Working Directory", self.set_work_dir_button)
        self.Id_widget = QLineEdit()
        uplayout.addRow("Reconstruction ID", self.Id_widget)
        self.scan_widget = QLineEdit()
        uplayout.addRow("scan(s)", self.scan_widget)
        self.set_conf_from_button = QPushButton()
        self.separate_scans = QCheckBox()
        uplayout.addRow("separate scans", self.separate_scans)
        self.separate_scans.setChecked(False)
        uplayout.addRow("Load conf from", self.set_conf_from_button)
        self.run_button = QPushButton('run_everything', self)
        uplayout.addWidget(self.run_button)

        vbox = QVBoxLayout()
        vbox.addLayout(uplayout)

        self.t = cdi_conf_tab(self)
        vbox.addWidget(self.t)

        self.setLayout(vbox)
        self.setWindowTitle("CDI Reconstruction")
        self.init_work_dir()

        self.set_conf_from_button.clicked.connect(self.load_conf_dir)
        self.set_work_dir_button.clicked.connect(self.set_working_dir)
        self.Id_widget.textChanged.connect(self.set_id)
        self.scan_widget.textChanged.connect(self.set_scan)
        self.run_button.clicked.connect(self.run_everything)


    def assure_experiment_dir(self):
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)
        experiment_conf_dir = os.path.join(self.experiment_dir, 'conf')
        if not os.path.exists(experiment_conf_dir):
            os.makedirs(experiment_conf_dir)


    def load_conf_dir(self):
        # select starting directory
        if self.experiment_dir is not None and \
            os.path.isfile(os.path.join(self.experiment_dir, 'conf', 'config')):
                load_dir = select_dir(os.path.join(self.experiment_dir, 'conf'))
        elif os.path.isfile(os.path.join(os.getcwd(), 'conf', 'config')):
            load_dir = select_dir(os.path.join(os.getcwd(), 'conf'))
        else:
            load_dir = select_dir(self.working_dir)
        if load_dir is not None:
            if not os.path.isfile(os.path.join(load_dir, 'config')):
                self.msg_window('missing config file in load directory')
                return
            elif not os.path.isfile(os.path.join(load_dir, 'config_data')):
                self.msg_window('missing config_p in load directory')
                return
            elif not os.path.isfile(os.path.join(load_dir, 'config_rec')):
                self.msg_window('missing config_rec file in load directory')
                return
            elif not os.path.isfile(os.path.join(load_dir, 'config_disp')):
                self.msg_window('missing config_disp file in load directory')
                return
            else:
                self.set_conf_from_button.setStyleSheet("Text-align:left")
                self.set_conf_from_button.setText('config loaded')
                self.init_from_conf(load_dir)
        else:
            self.msg_window('please select valid conf directory')


    def set_working_dir(self):
        self.working_dir = select_dir(self.working_dir)
        if self.working_dir is not None:
            self.set_work_dir_button.setStyleSheet("Text-align:left")
            self.set_work_dir_button.setText(self.working_dir)
            self.set_experiment_dir()
        else:
            self.set_work_dir_button.setText('')
            self.msg_window('please select valid working directory')
            return


    def set_id(self):
        self.id = str(self.Id_widget.text())
        self.set_experiment_dir()


    def set_scan(self):
        self.scan = str(self.scan_widget.text())
        try:
            numeric = self.scan.replace('-', '0')
            numeric_test = int(numeric)
        except:
            self.msg_window('enter numeric values for scan range')
            return
        self.set_experiment_dir()


    def set_experiment_dir(self):
        if self.id is not None and self.scan is not None:
            self.exp_id = self.id + '_' + self.scan
            self.experiment_dir = os.path.join(self.working_dir, self.exp_id)


    def run_everything(self):
        self.t.prepare()
        self.t.format_data()
        self.t.reconstruction()
        self.t.display()


    def init_work_dir(self):
        self.working_dir = os.getcwd()
        if os.path.isdir('conf'):
            main_conf = os.path.join('conf', 'config')
            try:
                conf_map = ut.read_config(main_conf)
                self.working_dir = conf_map.working_dir
            except:
                pass

        self.set_work_dir_button.setStyleSheet("Text-align:left")
        self.set_work_dir_button.setText(self.working_dir)


    def init_from_conf(self, dir):
        # if experiment not set, get it from the load_dir
        if self.experiment_dir is None:
            exp_name = dir.split('/')[-2]
            exp_name_parts = exp_name.split('_')
            self.scan = exp_name_parts[-1]
            self.scan_widget.setText(self.scan)
            self.id = exp_name[0:-len(self.scan)-1]
            self.Id_widget.setText(self.id)
            self.set_experiment_dir()

        main_conf = os.path.join(dir, 'config')
        if not os.path.isfile(main_conf):
            dir = os.path.join(dir, 'conf')
            main_conf = os.path.join(dir, 'config')
            if not os.path.isfile(main_conf):
                self.msg_window('the directory does not contain config file, or conf/config file')
                return
        # copy configuration files from chosen configuration directory
        self.assure_experiment_dir()
        dest = os.path.join(self.experiment_dir, 'conf')
        if dir != dest:
            shutil.copy(main_conf, dest)
            conf_data = os.path.join(dir, 'config_data')
            shutil.copy(conf_data, dest)
            conf_rec = os.path.join(dir, 'config_rec')
            shutil.copy(conf_rec, dest)
            conf_rec = os.path.join(dir, 'config_disp')
            shutil.copy(conf_rec, dest)

        try:
            conf_map = ut.read_config(main_conf)
        except Exception as e:
            self.msg_window('please check configuration file ' + main_conf + '. Cannot parse, ' + str(e))
            return
        try:
            separate_scans = conf_map.separate_scans
            if separate_scans:
                self.separate_scans.setChecked(True)
        except:
            pass
        try:
            self.t.data_dir = conf_map.data_dir
            self.t.data_dir_button.setStyleSheet("Text-align:left")
            self.t.data_dir_button.setText(self.t.data_dir)
        except:
            self.t.data_dir = None
            self.t.data_dir_button.setText('')
        try:
            self.t.specfile = conf_map.specfile
            self.t.spec_file_button.setStyleSheet("Text-align:left")
            self.t.spec_file_button.setText(self.t.specfile)
            # set specfile also in display tab
            self.t.spec_file_button1.setStyleSheet("Text-align:left")
            self.t.spec_file_button1.setText(self.t.specfile)
        except:
            self.t.specfile = None
            self.t.spec_file_button.setText('')
            self.t.spec_file_button1.setText('')
        try:
            self.t.darkfile = conf_map.darkfile
            self.t.dark_file_button.setStyleSheet("Text-align:left")
            self.t.dark_file_button.setText(self.t.darkfile)
        except:
            self.t.darkfile = None
            self.t.dark_file_button.setText('')
        try:
            self.t.whitefile = conf_map.whitefile
            self.t.white_file_button.setStyleSheet("Text-align:left")
            self.t.white_file_button.setText(self.t.whitefile)
        except:
            self.t.whitefile = None
            self.t.white_file_button.setText('')
        try:
            self.t.min_files.setText(str(conf_map.min_files).replace(" ", ""))
        except:
            pass
        try:
            self.t.exclude_scans.setText(str(conf_map.exclude_scans).replace(" ", ""))
        except:
            pass
        try:
            self.t.det_quad.setText(str(conf_map.det_quad).replace(" ", ""))
        except:
            pass

        # initialize "Data" tab
        data_conf = os.path.join(dir, 'config_data')
        if not os.path.isfile(data_conf):
            self.msg_window('missing configuration file ' + data_conf)
            return
        try:
            conf_map = ut.read_config(data_conf)
        except Exception as e:
            self.msg_window('please check configuration file ' + data_conf + '. Cannot parse, ' + str(e))
            return
        try:
            self.t.aliens.setText(str(conf_map.aliens).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.amp_threshold.setText(str(conf_map.amp_threshold).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.binning.setText(str(conf_map.binning).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.center_shift.setText(str(conf_map.center_shift).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.adjust_dimensions.setText(str(conf_map.adjust_dimensions).replace(" ", ""))
        except AttributeError:
            pass

        # initialize "Reconstruction" tab
        rec_conf = os.path.join(dir, 'config_rec')
        if not os.path.isfile(rec_conf):
            self.msg_window('missing configuration file ' + rec_conf)
            return
        try:
            conf_map = ut.read_config(rec_conf)
        except Exception as e:
            self.msg_window('please check configuration file ' + rec_conf + '. Cannot parse, ' + str(e))
            return
        try:
            self.t.device.setText(str(conf_map.device).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.samples.setText(str(conf_map.samples).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.gc.setText(str(conf_map.garbage_trigger).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.alg_seq.setText(str(conf_map.algorithm_sequence).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.beta.setText(str(conf_map.beta).replace(" ", ""))
        except AttributeError:
            pass

        for feat_id in self.t.features.feature_dir:
            self.t.features.feature_dir[feat_id].init_config(conf_map)

        # initialize "Display" tab
        disp_conf = os.path.join(dir, 'config_disp')
        if not os.path.isfile(disp_conf):
            self.msg_window('missing configuration file ' + disp_conf)
            return
        try:
            conf_map = ut.read_config(disp_conf)
        except Exception as e:
            self.msg_window('please check configuration file ' + disp_conf + '. Cannot parse, ' + str(e))
            return
        try:
            self.t.crop.setText(str(conf_map.crop).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.energy.setText(str(conf_map.energy).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.delta.setText(str(conf_map.delta).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.gamma.setText(str(conf_map.gamma).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.arm.setText(str(conf_map.arm).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.dth.setText(str(conf_map.dth).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.pixel.setText(str(conf_map.pixel).replace(" ", ""))
        except AttributeError:
            pass
        try:
            specfile = conf_map.specfile
            self.t.specfile = specfile
            self.t.spec_file_button1.setStyleSheet("Text-align:left")
            self.t.spec_file_button1.setText(self.t.specfile)
            if os.path.isfile(self.t.specfile):
                self.t.parse_spec()
        except AttributeError:
            pass


    def msg_window(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.setWindowTitle("Info")
        msg.exec_()


    def write_conf(self, conf_map, dir, file):
        # create "temp" file first and then overrite existing configuration file
        if not os.path.exists(dir):
            os.makedirs(dir)
        conf_file = os.path.join(dir, file)
        temp_file = os.path.join(dir, 'temp')
        with open(temp_file, 'a') as f:
            for key in conf_map:
                value = conf_map[key]
                if len(value) > 0:
                    f.write(key + ' = ' + conf_map[key] + '\n')
        f.close()
        # verify that the temporary file can be parsed
        try:
            ut.read_config(temp_file)
            shutil.move(temp_file, conf_file)
            return True
        except:
            if file == 'config':
                tab = 'Data Prep'
            elif file == 'config_data':
                tab = 'Data'
            elif file == 'config_rec':
                tab = 'Reconstruction'
            elif file == 'config_disp':
                tab = 'Display'
            self.msg_window('please check the entries in the ' + tab + ' tab. Cannot save this format')
            os.remove(temp_file)
            return False


class cdi_conf_tab(QTabWidget):
    def __init__(self, main_win, parent=None):
        super(cdi_conf_tab, self).__init__(parent)
        self.main_win = main_win
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        self.data_dir = None
        self.specfile = None
        self.darkfile = None
        self.whitefile = None
        self.addTab(self.tab1, "Data prep")
        self.addTab(self.tab2, "Data")
        self.addTab(self.tab3, "Reconstruction")
        self.addTab(self.tab4, "Display")
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()
        self.tab4UI()


    def tab1UI(self):
        self.script = None
        self.imported_script = False
        layout = QFormLayout()
        self.data_dir_button = QPushButton()
        layout.addRow("data directory", self.data_dir_button)
        self.spec_file_button = QPushButton()
        layout.addRow("spec file", self.spec_file_button)
        self.det_quad = QLineEdit()
        layout.addRow("detector quad", self.det_quad)
        self.dark_file_button = QPushButton()
        layout.addRow("darkfield file", self.dark_file_button)
        self.white_file_button = QPushButton()
        layout.addRow("whitefield file", self.white_file_button)
        self.min_files = QLineEdit()
        layout.addRow("min files in scan", self.min_files)
        self.exclude_scans = QLineEdit()
        layout.addRow("exclude scans", self.exclude_scans)
        self.prep = QComboBox()
        self.prep.addItem("34ID prep")
        self.prep.addItem("custom")
        self.prep.addItem("copy from")
        layout.addRow("choose data preparation ", self.prep)
        # add sub-layout with rows that apply to the choice form above
        sub_layout = QFormLayout()
        self.load_prep(sub_layout)
        layout.addRow(sub_layout)
        self.prep_button = QPushButton('prepare', self)
        layout.addWidget(self.prep_button)
        self.tab1.setLayout(layout)

        self.prep_button.clicked.connect(self.prepare)
        self.prep.currentIndexChanged.connect(lambda: self.load_prep(sub_layout))
        self.data_dir_button.clicked.connect(self.set_data_dir)
        self.spec_file_button.clicked.connect(self.set_spec_file)
        self.dark_file_button.clicked.connect(self.set_dark_file)
        self.white_file_button.clicked.connect(self.set_white_file)
        self.det_quad.textChanged.connect(lambda: self.set_overriden(self.det_quad))
        self.layout1 = layout


    def load_prep(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        if str(self.prep.currentText()) == "custom":
            self.script_button = QPushButton()
            layout.addRow("select script", self.script_button)
            self.prep_exec = QLineEdit()
            layout.addRow("prep function", self.prep_exec)
            self.args = QLineEdit()
            layout.addRow("arguments (str/num)", self.args)
            self.script_button.clicked.connect(self.set_prep_script)

        # elif str(self.prep.currentText()) == "34ID prep":
        elif str(self.prep.currentText()) == "copy from":
            self.ready_prep = QPushButton()
            layout.addRow("select file", self.ready_prep)
            self.ready_prep.clicked.connect(self.set_prep_file)


    def tab2UI(self):
        layout = QFormLayout()
        self.aliens = QLineEdit()
        layout.addRow("aliens", self.aliens)
        self.amp_threshold = QLineEdit()
        layout.addRow("amp_threshold", self.amp_threshold)
        self.center_shift = QLineEdit()
        layout.addRow("center_shift", self.center_shift)
        self.adjust_dimensions = QLineEdit()
        layout.addRow("pad, crop", self.adjust_dimensions)
        self.binning = QLineEdit()
        layout.addRow("binning", self.binning)
        self.config_data_button = QPushButton('format data', self)
        layout.addWidget(self.config_data_button)
        self.tab2.setLayout(layout)

        # this will create config_data file and run data script
        # to generate data ready for reconstruction
        self.config_data_button.clicked.connect(self.format_data)


    def tab3UI(self):
        layout = QVBoxLayout()
        ulayout = QFormLayout()
        llayout = QHBoxLayout()
        self.proc = QComboBox()
        self.proc.addItem("opencl")
        self.proc.addItem("cpu")
        self.proc.addItem("cuda")
        ulayout.addRow("processor type", self.proc)
        self.cont = QCheckBox()
        ulayout.addRow("continuation", self.cont)
        self.cont.setChecked(False)
        self.device = QLineEdit()
        ulayout.addRow("device(s)", self.device)
        self.samples = QLineEdit()
        ulayout.addRow("number of reconstructions", self.samples)
        self.gc = QLineEdit()
        ulayout.addRow("gc triggers", self.gc)
        self.alg_seq = QLineEdit()
        ulayout.addRow("algorithm sequence", self.alg_seq)
        # TODO add logic to show this only if HIO is in sequence
        self.beta = QLineEdit()
        ulayout.addRow("beta", self.beta)
        self.rec_default_button = QPushButton('set to defaults', self)
        ulayout.addWidget(self.rec_default_button)

        layout.addLayout(ulayout)
        layout.addLayout(llayout)
        self.features = Features(self, llayout)
        self.config_rec_button = QPushButton('run reconstruction', self)
        layout.addWidget(self.config_rec_button)
        self.tab3.setAutoFillBackground(True)
        self.tab3.setLayout(layout)

        self.config_rec_button.clicked.connect(self.reconstruction)
        self.cont.stateChanged.connect(lambda: self.toggle_cont(ulayout))
        self.rec_default_button.clicked.connect(self.rec_default)


    def toggle_cont(self, layout):
        cb_label = layout.labelForField(self.cont)
        if self.cont.isChecked():
            self.cont_dir = QLineEdit()
            layout.insertRow(2, "continue dir", self.cont_dir)
            cb_label.setStyleSheet('color: black')
        else:
            cb_label.setStyleSheet('color: grey')


    def tab4UI(self):
        layout = QFormLayout()
        self.crop = QLineEdit()
        layout.addRow("crop", self.crop)
        self.spec_file_button1 = QPushButton()
        layout.addRow("spec file", self.spec_file_button1)
        self.energy = QLineEdit()
        layout.addRow("energy", self.energy)
        self.delta = QLineEdit()
        layout.addRow("delta (deg)", self.delta)
        self.gamma = QLineEdit()
        layout.addRow("gamma (deg)", self.gamma)
        self.arm = QLineEdit()
        layout.addRow("arm (m)", self.arm)
        self.dth = QLineEdit()
        layout.addRow("dth (deg)", self.dth)
        self.pixel = QLineEdit()
        layout.addRow("pixel", self.pixel)
        self.config_disp = QPushButton('process display', self)
        layout.addWidget(self.config_disp)
        self.tab4.setLayout(layout)

        self.spec_file_button1.clicked.connect(self.set_spec_file)
        self.config_disp.clicked.connect(self.display)
        self.energy.textChanged.connect(lambda: self.set_overriden(self.energy))
        self.delta.textChanged.connect(lambda: self.set_overriden(self.delta))
        self.gamma.textChanged.connect(lambda: self.set_overriden(self.gamma))
        self.arm.textChanged.connect(lambda: self.set_overriden(self.arm))
        self.dth.textChanged.connect(lambda: self.set_overriden(self.dth))
        self.pixel.textChanged.connect(lambda: self.set_overriden(self.pixel))
        self.layout4 = layout


    def set_overriden(self, item):
        item.setStyleSheet('color: black')


    def set_spec_file(self):
        self.specfile = select_file(self.specfile)
        if self.specfile is not None:
            self.spec_file_button.setStyleSheet("Text-align:left")
            self.spec_file_button.setText(self.specfile)
            self.spec_file_button1.setStyleSheet("Text-align:left")
            self.spec_file_button1.setText(self.specfile)
            self.parse_spec()
        else:
            self.spec_file_button.setText('')
            self.spec_file_button.setText('')



    def parse_spec(self):
        last_scan = int(self.main_win.scan.split('-')[-1])
        det1, det2, det_quad = spec.get_det_from_spec(self.specfile, last_scan)
        if det_quad is not None:
            self.det_quad.setText(det_quad)
            self.det_quad.setStyleSheet('color: blue')
        energy, delta, gamma, dth, arm, pixel = spec.parse_spec(self.specfile, last_scan)
        self.energy.setText(str(energy))
        self.energy.setStyleSheet('color: blue')
        self.delta.setText(str(delta))
        self.delta.setStyleSheet('color: blue')
        self.gamma.setText(str(gamma))
        self.gamma.setStyleSheet('color: blue')
        self.dth.setText(str(dth))
        self.dth.setStyleSheet('color: blue')
        self.arm.setText(str(arm))
        self.arm.setStyleSheet('color: blue')
        self.pixel.setText(str(pixel))
        self.pixel.setStyleSheet('color: blue')


    def set_dark_file(self):
        self.darkfile = select_file(self.darkfile)
        if self.darkfile is not None:
            self.dark_file_button.setStyleSheet("Text-align:left")
            self.dark_file_button.setText(self.darkfile)
        else:
            self.dark_file_button.setText('')


    def set_white_file(self):
        self.whitefile = select_file(self.whitefile)
        if self.whitefile is not None:
            self.white_file_button.setStyleSheet("Text-align:left")
            self.white_file_button.setText(self.whitefile)
        else:
            self.white_file_button.setText('')

    def set_data_dir(self):
        self.data_dir = select_dir(self.data_dir)
        if self.data_dir is not None:
            self.data_dir_button.setStyleSheet("Text-align:left")
            self.data_dir_button.setText(self.data_dir)
        else:
            self.data_dir_button.setText('')


    def set_prep_file(self):
        prep_file = select_file(self.main_win.working_dir)
        if prep_file is not None:
            selected = str(prep_file)
            if not selected.endswith('tif') and not selected.endswith('tiff'):
                self.msg_window("the file extension must be tif or tiff")
                return
            self.ready_prep.setStyleSheet("Text-align:left")
            self.ready_prep.setText(prep_file)
            # save the file as experiment prep file
            prep_dir = os.path.join(self.main_win.experiment_dir, 'prep')
            if not os.path.exists(prep_dir):
                os.makedirs(prep_dir)
            exp_prep_file = os.path.join(prep_dir, 'prep_data.tif')
            shutil.copyfile(selected, exp_prep_file)
        else:
            self.ready_prep.setText('')


    def set_prep_script(self):
        self.script = select_file(self.main_win.working_dir)
        if self.script is not None:
            self.script_button.setStyleSheet("Text-align:left")
            self.script_button.setText(self.script)
            # fill the arguments with experiment_dir, scans, config file
            conf_file = os.path.join(self.main_win.experiment_dir, 'conf', 'config')
            self.args.setText(str(self.main_win.experiment_dir) + ',' + str(self.main_win.scan) + ',' + conf_file)
        else:
            self.script_button.setText('')



    def prepare(self):
        if self.main_win.id is None:
            self.msg_window('enter Reconstruction ID and scan')
        else:
            # prep_dir = os.path.join(self.main_win.experiment_dir, 'prep')
            # if not os.path.exists(prep_dir):
            #     os.makedirs(prep_dir)
            conf_map = {}
            if self.main_win.working_dir is not None:
                conf_map['working_dir'] = '"' + str(self.main_win.working_dir) + '"'
            else:
                self.msg_window("working_dir not defined")
                return
            if len(self.min_files.text()) > 0:
                min_files = str(self.min_files.text())
                conf_map['min_files'] = min_files
            if len(self.exclude_scans.text()) > 0:
                conf_map['exclude_scans'] = str(self.exclude_scans.text()).replace('\n','')
            if len(self.det_quad.text()) > 0:
                det_quad = str(self.det_quad.text())
                conf_map['det_quad'] = det_quad
            if self.main_win.separate_scans.isChecked():
                conf_map['separate_scans'] = 'true'
            if str(self.prep.currentText()) == "custom":
                self.prepare_custom(conf_map)
            elif str(self.prep.currentText()) == "34ID prep":
                self.prepare_34id(conf_map)


    def prepare_custom(self, conf_map):
        if self.data_dir is not None:
            conf_map['data_dir'] = '"' + str(self.data_dir) + '"'
        if self.specfile is not None:
            conf_map['specfile'] = '"' + str(self.specfile) + '"'
        if self.darkfile is not None:
            conf_map['darkfile'] = '"' + str(self.darkfile) + '"'
        if self.whitefile is not None:
            conf_map['whitefile'] = '"' + str(self.whitefile) + '"'

        # determine script directory and script name
        if self.script is None:
            self.msg_window("script not defined")
            return
        full_script = str(self.script)
        script_info = full_script.split('/')
        script = script_info[len(script_info)-1]
        script_dir = full_script[0 : -(len(script)+1)]
        script = script[0 : -3]
        func = str(self.prep_exec.text())
        if len(func) == 0:
            self.msg_window("function not defined")
            return

        current_dir = os.getcwd()
        args = str(self.args.text())
        if len(args) == 0:
            args = []
        else:
            args = args.split(',')
            for i in range(len(args)):
                try:
                    if args[i].find('.') == -1:
                        args[i] = int(args[i])
                    else:
                        args[i] = float(args[i])
                except:
                    pass
                try:
                    if args[i].find('-') > -1:
                        l = args[i].split('-')
                        nl = []
                        for n in l:
                            nl.append(int(n))
                        args[i] = nl
                except:
                    pass

        os.chdir(script_dir)
        sys.path.append(script_dir)
        if not self.imported_script:
            self.m = importlib.import_module(script)
            self.imported_script = True
        else:
            self.m = importlib.reload(self.m)
        os.chdir(current_dir)
        f = getattr(self.m, func)
        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
        if self.main_win.write_conf(conf_map, conf_dir, 'config'):
            try:
                prep_data = f(*args)
            except Exception as e:
                self.msg_window('custom script failed ' + str(e))
                return
            if prep_data is not None:
                tif_file = os.path.join(self.main_win.experiment_dir, 'prep', 'prep_data.tif')
                ut.save_tif(prep_data, tif_file)
                print ('done with prep')


    def prepare_34id(self, conf_map):
        mod = importlib.import_module('reccdi.src_py.run_scripts.run_34id_prepare')
        scan = str(self.main_win.scan_widget.text())
        try:
            # after checking that scan is entered convert it to list of int
            scan_range = scan.split('-')
            for i in range(len(scan_range)):
                scan_range[i] = int(scan_range[i])
        except:
            self.msg_window('enter numeric values for scan range')
            return

        if  self.main_win.working_dir is None or \
            self.main_win.id is None or\
            scan is None or \
            self.data_dir is None or \
            self.specfile is None and len(self.det_quad.text()) == 0 :
            self.msg_window('enter all parameters: working_dir, id, scan, data_dir, specfile or detector quad')
            return

        if self.data_dir is not None:
            conf_map['data_dir'] = '"' + str(self.data_dir) + '"'
        if self.specfile is not None:
            conf_map['specfile'] = '"' + str(self.specfile) + '"'
        if self.darkfile is not None:
            conf_map['darkfile'] = '"' + str(self.darkfile) + '"'
        if self.whitefile is not None:
            conf_map['whitefile'] = '"' + str(self.whitefile) + '"'

        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
        conf_file = os.path.join(conf_dir, 'config')
        if self.main_win.write_conf(conf_map, conf_dir, 'config'):
            f = getattr(mod, 'prepare')
            f(self.main_win.experiment_dir, scan_range, conf_file)

        #scripts.run_34id_prepare.prepare(self.main_win.working_dir, self.main_win.exp_id, scan_range, self.data_dir, self.specfile, self.darkfile, self.whitefile)


    def format_data(self):
        if os.path.isfile(os.path.join(self.main_win.experiment_dir, 'prep','prep_data.tif'))\
                or self.main_win.separate_scans.isChecked():
            conf_map = {}
            if len(self.aliens.text()) > 0:
                conf_map['aliens'] = str(self.aliens.text()).replace('\n','')
            if len(self.amp_threshold.text()) > 0:
                conf_map['amp_threshold'] = str(self.amp_threshold.text())
            else:
                self.msg_window('amplitude threshold not defined. Quiting operation.')
                return
            if len(self.binning.text()) > 0:
                conf_map['binning'] = str(self.binning.text()).replace('\n','')
            if len(self.center_shift.text()) > 0:
                conf_map['center_shift'] = str(self.center_shift.text()).replace('\n','')
            if len(self.adjust_dimensions.text()) > 0:
                conf_map['adjust_dimensions'] = str(self.adjust_dimensions.text()).replace('\n','')

            conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
            if self.main_win.write_conf(conf_map, conf_dir, 'config_data'):
                run_dt.data(self.main_win.experiment_dir)
        else:
            self.msg_window('Please, run data preparation in previous tab to activate this function')


    def msg_window(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.setWindowTitle("Info")
        msg.exec_()


    def reconstruction(self):
        if os.path.isfile(os.path.join(self.main_win.experiment_dir, 'data', 'data.tif'))\
                or self.main_win.separate_scans.isChecked():
            conf_map = {}
            conf_map['samples'] = str(self.samples.text())
            conf_map['device'] = str(self.device.text()).replace('\n','')
            conf_map['garbage_trigger'] = str(self.gc.text()).replace('\n','')
            conf_map['algorithm_sequence'] = str(self.alg_seq.text()).replace('\n','')
            conf_map['beta'] = str(self.beta.text())
            if self.cont.isChecked():
                conf_map['continue_dir'] = str(self.cont_dir.text())

            for feat_id in self.features.feature_dir:
                self.features.feature_dir[feat_id].add_config(conf_map)

            #self.create_config('config_rec', conf_map)
            conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
            if self.main_win.write_conf(conf_map, conf_dir, 'config_rec'):
                run_rc.reconstruction(str(self.proc.currentText()), self.main_win.experiment_dir)
        else:
            self.msg_window('Please, run format data in previous tab to activate this function')


    def display(self):
        if (self.specfile is None or not os.path.isfile(self.specfile)) and \
           (len(self.energy.text()) == 0 or \
            len(self.delta.text()) == 0 or \
            len(self.gamma.text()) == 0 or \
            len(self.arm.text()) == 0 or \
            len(self.dth.text()) == 0 or \
            len(self.pixel.text()) == 0):
                self.msg_window('Please, enter spec file or all detector parameters')
                return

        res_dir = os.path.join(self.main_win.experiment_dir, 'results')
        if os.path.isfile(os.path.join(res_dir, 'image.npy')) or \
        os.path.isfile(os.path.join(res_dir, '0', 'image.npy')) or \
        os.path.isfile(os.path.join(res_dir, 'g_0', '0', 'image.npy')) or \
        self.main_win.separate_scans.isChecked():
            conf_map = {}
            if self.specfile is not None:
                conf_map['specfile'] = '"' + str(self.specfile) + '"'
            if len(self.energy.text()) > 0:
                conf_map['energy'] = str(self.energy.text())
            if len(self.delta.text()) > 0:
                conf_map['delta'] = str(self.delta.text())
            if len(self.gamma.text()) > 0:
                conf_map['gamma'] = str(self.gamma.text())
            if len(self.arm.text()) > 0:
                conf_map['arm'] = str(self.arm.text())
            if len(self.dth.text()) > 0:
                conf_map['dth'] = str(self.dth.text())
            if len(self.pixel.text()) > 0:
                conf_map['pixel'] = str(self.pixel.text()).replace('\n','')
            if len(self.crop.text()) > 0:
                conf_map['crop'] = str(self.crop.text()).replace('\n','')

            conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
            if self.main_win.write_conf(conf_map, conf_dir, 'config_disp'):
                run_dp.to_vtk(self.main_win.experiment_dir)
        else:
            self.msg_window('Please, run reconstruction in previous tab to activate this function')


    def rec_default(self):
        if  self.main_win.working_dir is None or self.main_win.id is None or \
            len(self.main_win.working_dir) == 0 or len(self.main_win.id) == 0:
            self.msg_window('Working Directory or Reconstruction ID not configured')
        else:
            self.samples.setText('1')
            self.device.setText('(3)')
            self.gc.setText('(1000)')
            self.alg_seq.setText('((3,("ER",20),("HIO",180)),(1,("ER",20)))')
            self.beta.setText('.9')
            self.cont.setChecked(False)


class Feature(object):
    def __init__(self):
        self.stack = QWidget()


    def stackUI(self, item, feats):
        layout = QFormLayout()
        self.active = QCheckBox("active")
#        self.active.setChecked(True)
        layout.addWidget(self.active)
        self.toggle(layout, item, feats)
        self.stack.setLayout(layout)
        self.active.stateChanged.connect(lambda: self.toggle(layout, item, feats))


    def toggle(self, layout, item, feats):
        if self.active.isChecked():
            self.fill_active(layout)

            self.default_button = QPushButton('set to defaults', feats)
            layout.addWidget(self.default_button)
            self.default_button.clicked.connect(self.rec_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));

    def fill_active(self, layout):
        pass


    def rec_default(self):
        pass


    def add_config(self, conf_map):
        if self.active.isChecked():
            self.add_feat_conf(conf_map)

    def add_feat_conf(self, conf_map):
        pass


    def init_config(self, conf_map):
        pass


class GA(Feature):
    def __init__(self):
        super(GA, self).__init__()
        self.id = 'GA'

    # override setting the active to set it False
    def stackUI(self, item, feats):
        super(GA, self).stackUI(item, feats)


    def init_config(self, conf_map):
        try:
            gens = conf_map.generations
            self.active.setChecked(True)
            self.generations.setText(str(gens).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return
        try:
            self.metrics.setText(str(conf_map.ga_metrics).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.breed_modes.setText(str(conf_map.ga_breed_modes).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.removes.setText(str(conf_map.ga_cullings).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.ga_support_thresholds.setText(str(conf_map.ga_support_thresholds).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.ga_support_sigmas.setText(str(conf_map.ga_support_sigmas).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.lr_sigmas.setText(str(conf_map.ga_low_resolution_sigmas).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.generations = QLineEdit()
        layout.addRow("generations", self.generations)
        self.metrics = QLineEdit()
        layout.addRow("fitness metrics", self.metrics)
        self.breed_modes = QLineEdit()
        layout.addRow("breed modes", self.breed_modes)
        self.removes = QLineEdit()
        layout.addRow("cullings", self.removes)
        self.ga_support_thresholds = QLineEdit()
        layout.addRow("after breed support thresholds", self.ga_support_thresholds)
        self.ga_support_sigmas = QLineEdit()
        layout.addRow("after breed support sigmas", self.ga_support_sigmas)
        self.lr_sigmas = QLineEdit()
        layout.addRow("low resolution sigmas", self.lr_sigmas)


    def rec_default(self):
        self.generations.setText('5')
        self.metrics.setText('("chi","chi","area","chi","sharpness")')
        self.breed_modes.setText('("sqrt_ab","sqrt_ab","max_all","Dhalf","sqrt_ab")')
        self.removes.setText('(2,2,1)')
        self.ga_support_thresholds.setText('(.1,.1,.1,.1,.1)')
        self.ga_support_sigmas.setText('(1.0,1.0,1.0,1.0)')
        self.lr_sigmas.setText('(2.0,1.5)')
        self.active.setChecked(True)


    def add_feat_conf(self, conf_map):
        conf_map['generations'] = str(self.generations.text())
        conf_map['ga_metrics'] = str(self.metrics.text()).replace('\n','')
        conf_map['ga_breed_modes'] = str(self.breed_modes.text()).replace('\n','')
        conf_map['ga_cullings'] = str(self.removes.text()).replace('\n','')
        conf_map['ga_support_thresholds'] = str(self.ga_support_thresholds.text()).replace('\n','')
        conf_map['ga_support_sigmas'] = str(self.ga_support_sigmas.text()).replace('\n','')
        conf_map['ga_low_resolution_sigmas'] = str(self.lr_sigmas.text()).replace('\n','')


class low_resolution(Feature):
    def __init__(self):
        super(low_resolution, self).__init__()
        self.id = 'low resolution'


    def init_config(self, conf_map):
        try:
            triggers = conf_map.resolution_trigger
            self.active.setChecked(True)
            self.res_triggers.setText(str(triggers).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return
        try:
            self.sigma_range.setText(str(conf_map.iter_res_sigma_range).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.det_range.setText(str(conf_map.iter_res_det_range).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.res_triggers = QLineEdit()
        layout.addRow("low resolution triggers", self.res_triggers)
        self.sigma_range = QLineEdit()
        layout.addRow("sigma range", self.sigma_range)
        self.det_range = QLineEdit()
        layout.addRow("det range", self.det_range)


    def rec_default(self):
        #TODO add to accept fractions in trigger, so the default will be (.5,1)
        self.res_triggers.setText('(0, 1, 320)')
        self.sigma_range.setText('(2.0)')
        self.det_range.setText('(.7)')


    def add_feat_conf(self, conf_map):
        conf_map['resolution_trigger'] = str(self.res_triggers.text()).replace('\n','')
        conf_map['iter_res_sigma_range'] = str(self.sigma_range.text()).replace('\n','')
        conf_map['iter_res_det_range'] = str(self.det_range.text()).replace('\n','')


class amplitude_support(Feature):
    def __init__(self):
        super(amplitude_support, self).__init__()
        self.id = 'amplitude support'


    def init_config(self, conf_map):
        try:
            triggers = conf_map.amp_support_trigger
            self.active.setChecked(True)
            self.support_triggers.setText(str(triggers).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return
        try:
            self.support_type.setText(str(conf_map.support_type).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.support_area.setText(str(conf_map.support_area).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.threshold.setText(str(conf_map.support_threshold).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.sigma.setText(str(conf_map.support_sigma).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.support_triggers = QLineEdit()
        layout.addRow("support triggers", self.support_triggers)
        self.support_type = QLineEdit()
        layout.addRow("support algorithm", self.support_type)
        self.support_area = QLineEdit()
        layout.addRow("starting support area", self.support_area)
        self.threshold = QLineEdit()
        layout.addRow("threshold", self.threshold)
        self.sigma = QLineEdit()
        layout.addRow("sigma", self.sigma)


    def rec_default(self):
        self.support_triggers.setText('(1,1)')
        self.support_type.setText('GAUSS')
        self.support_area.setText('(.5,.5,.5)')
        self.sigma.setText('1.0')
        self.threshold.setText('0.1')


    def add_feat_conf(self, conf_map):
        conf_map['amp_support_trigger'] = str(self.support_triggers.text()).replace('\n','')
        conf_map['support_type'] = '"' + str(self.support_type.text()) + '"'
        conf_map['support_threshold'] = str(self.threshold.text())
        conf_map['support_sigma'] = str(self.sigma.text())
        conf_map['support_area'] = str(self.support_area.text()).replace('\n','')


class phase_support(Feature):
    def __init__(self):
        super(phase_support, self).__init__()
        self.id = 'phase support'


    def init_config(self, conf_map):
        try:
            triggers = conf_map.phase_support_trigger
            self.active.setChecked(True)
            self.phase_triggers.setText(str(triggers).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return
        try:
            self.phase_min.setText(str(conf_map.phase_min).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.phase_max.setText(str(conf_map.phase_max).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.phase_triggers = QLineEdit()
        layout.addRow("phase support triggers", self.phase_triggers)
        self.phase_min = QLineEdit()
        layout.addRow("phase minimum", self.phase_min)
        self.phase_max = QLineEdit()
        layout.addRow("phase maximum", self.phase_max)


    def rec_default(self):
        self.phase_triggers.setText('(0,1,20)')
        self.phase_min.setText('-1.57')
        self.phase_max.setText('1.57')


    def add_feat_conf(self, conf_map):
        conf_map['phase_support_trigger'] = str(self.phase_triggers.text()).replace('\n','')
        conf_map['phase_min'] = str(self.phase_min.text())
        conf_map['phase_max'] = str(self.phase_max.text())


class pcdi(Feature):
    def __init__(self):
        super(pcdi, self).__init__()
        self.id = 'pcdi'


    def init_config(self, conf_map):
        try:
            triggers = conf_map.pcdi_trigger
            self.active.setChecked(True)
            self.pcdi_triggers.setText(str(triggers).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return
        try:
            self.pcdi_type.setText(str(conf_map.partial_coherence_type).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.pcdi_iter.setText(str(conf_map.partial_coherence_iteration_num).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.pcdi_normalize.setText(str(conf_map.partial_coherence_normalize).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.pcdi_roi.setText(str(conf_map.partial_coherence_roi).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.pcdi_triggers = QLineEdit()
        layout.addRow("pcdi triggers", self.pcdi_triggers)
        self.pcdi_type = QLineEdit()
        layout.addRow("partial coherence algorithm", self.pcdi_type)
        self.pcdi_iter = QLineEdit()
        layout.addRow("pcdi iteration number", self.pcdi_iter)
        self.pcdi_normalize = QLineEdit()
        layout.addRow("normalize", self.pcdi_normalize)
        self.pcdi_roi = QLineEdit()
        layout.addRow("pcdi kernel area", self.pcdi_roi)


    def rec_default(self):
        self.pcdi_triggers.setText('(50,50)')
        self.pcdi_type.setText('LUCY')
        self.pcdi_iter.setText('20')
        self.pcdi_normalize.setText('true')
        self.pcdi_roi.setText('(32,32,32)')


    def add_feat_conf(self, conf_map):
        conf_map['pcdi_trigger'] = str(self.pcdi_triggers.text()).replace('\n','')
        conf_map['partial_coherence_type'] = '"' + str(self.pcdi_type.text()) + '"'
        conf_map['partial_coherence_iteration_num'] = str(self.pcdi_iter.text())
        conf_map['partial_coherence_normalize'] = str(self.pcdi_normalize.text())
        conf_map['partial_coherence_roi'] = str(self.pcdi_roi.text()).replace('\n','')


class twin(Feature):
    def __init__(self):
        super(twin, self).__init__()
        self.id = 'twin'


    def init_config(self, conf_map):
        try:
            triggers = conf_map.twin_trigger
            self.active.setChecked(True)
            self.twin_triggers.setText(str(triggers).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return
        try:
            self.twin_halves.setText(str(conf_map.twin_halves).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.twin_triggers = QLineEdit()
        layout.addRow("twin triggers", self.twin_triggers)
        self.twin_halves = QLineEdit()
        layout.addRow("twin halves", self.twin_halves)


    def rec_default(self):
        self.twin_triggers.setText('(2)')
        self.twin_halves.setText('(0,0)')


    def add_feat_conf(self, conf_map):
        conf_map['twin_trigger'] = str(self.twin_triggers.text()).replace('\n','')
        conf_map['twin_halves'] = str(self.twin_halves.text()).replace('\n','')


class average(Feature):
    def __init__(self):
        super(average, self).__init__()
        self.id = 'average'


    def init_config(self, conf_map):
        try:
            triggers = conf_map.average_trigger
            self.active.setChecked(True)
            self.average_triggers.setText(str(triggers).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return


    def fill_active(self, layout):
        self.average_triggers = QLineEdit()
        layout.addRow("average triggers", self.average_triggers)


    def rec_default(self):
        self.average_triggers.setText('(-400,1)')


    def add_feat_conf(self, conf_map):
        conf_map['average_trigger'] = str(self.average_triggers.text()).replace('\n','')


class progress(Feature):
    def __init__(self):
        super(progress, self).__init__()
        self.id = 'progress'


    def init_config(self, conf_map):
        try:
            triggers = conf_map.progress_trigger
            self.active.setChecked(True)
            self.progress_triggers.setText(str(triggers).replace(" ", ""))
        except AttributeError:
            self.active.setChecked(False)
            return


    def fill_active(self, layout):
        self.progress_triggers = QLineEdit()
        layout.addRow("progress triggers", self.progress_triggers)


    def rec_default(self):
        self.progress_triggers.setText('(0,20)')


    def add_feat_conf(self, conf_map):
        conf_map['progress_trigger'] = str(self.progress_triggers.text()).replace('\n','')



class Features(QWidget):
    def __init__(self, tab, layout):
        super(Features, self).__init__()
        feature_ids = ['GA', 'low resolution', 'amplitude support', 'phase support', 'pcdi', 'twin', 'average', 'progress']
        self.leftlist = QListWidget()
        self.feature_dir = {'GA' : GA(),
                            'low resolution' : low_resolution(),
                            'amplitude support' : amplitude_support(),
                            'phase support' : phase_support(),
                            'pcdi' : pcdi(),
                            'twin' : twin(),
                            'average' : average(),
                            'progress' : progress()}
        self.Stack = QStackedWidget(self)
        for i in range(len(feature_ids)):
            id = feature_ids[i]
            self.leftlist.insertItem(i, id)
            feature = self.feature_dir[id]
            feature.stackUI(self.leftlist.item(i), self)
            self.Stack.addWidget(feature.stack)

        layout.addWidget(self.leftlist)
        layout.addWidget(self.Stack)

        self.leftlist.currentRowChanged.connect(self.display)


    def display(self, i):
        self.Stack.setCurrentIndex(i)


def main():
    app = QApplication(sys.argv)
    ex = cdi_conf()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
