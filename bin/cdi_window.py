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
import reccdi.src_py.utilities.parse_ver as ver
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


def msg_window(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(text)
    msg.setWindowTitle("Info")
    msg.exec_()


class cdi_gui(QWidget):
    def __init__(self, parent=None):
        super(cdi_gui, self).__init__(parent)
        self.exp_id = None
        self.experiment_dir = None
        self.working_dir = None
        uplayout = QFormLayout()

        self.set_work_dir_button = QPushButton()
        uplayout.addRow("Working Directory", self.set_work_dir_button)
        self.Id_widget = QLineEdit()
        uplayout.addRow("Experiment ID", self.Id_widget)
        self.scan_widget = QLineEdit()
        uplayout.addRow("scan(s)", self.scan_widget)
        # self.set_conf_from_button = QPushButton("Load conf from")
        # self.set_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        # uplayout.addRow(self.set_conf_from_button)
        # self.create_exp_button = QPushButton('create experiment')
        # self.create_exp_button.setStyleSheet("background-color:rgb(120,180,220)")
        # uplayout.addRow(self.create_exp_button)

        vbox = QVBoxLayout()
        vbox.addLayout(uplayout)

        self.t = cdi_conf_tab(self)
        vbox.addWidget(self.t)

        downlayout = QFormLayout()
        self.set_conf_from_button = QPushButton("Load conf from")
        self.set_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        downlayout.addWidget(self.set_conf_from_button)
        self.create_exp_button = QPushButton('set experiment')
        self.create_exp_button.setStyleSheet("background-color:rgb(120,180,220)")
        downlayout.addWidget(self.create_exp_button)
        self.run_button = QPushButton('run everything', self)
        self.run_button.setStyleSheet("background-color:rgb(175,208,156)")
        downlayout.addWidget(self.run_button)
        vbox.addLayout(downlayout)

        self.setLayout(vbox)
        self.setWindowTitle("CDI Reconstruction")
#        self.init_work_dir()

        self.set_conf_from_button.clicked.connect(self.load_conf_dir)
        self.set_work_dir_button.clicked.connect(self.set_working_dir)
        self.run_button.clicked.connect(self.run_everything)
        self.create_exp_button.clicked.connect(self.set_experiment)


    def run_everything(self):
        if not self.is_exp_exists():
            msg_window('the experiment has not been created yet')
        elif not self.is_exp_set():
            msg_window('the experiment has changed, pres "set experiment" button')
        else:
            self.t.prepare()
            self.t.format_data()
            self.t.reconstruction()
            self.t.display()


    def is_exp_exists(self):
        if self.exp_id is None:
            return False
        if self.working_dir is None:
            return False
        exp_id = str(self.Id_widget.text()).strip()
        scan = str(self.scan_widget.text()).strip()
        if scan != '':
            exp_id = exp_id + '_' + scan
        if not os.path.exists(os.path.join(self.working_dir, exp_id)):
            return False
        return True


    def is_exp_set(self):
        if self.exp_id is None:
            return False
        if self.working_dir is None:
            return False
        if self.scan != str(self.scan_widget.text()).strip():
            return False
        return True


    def load_conf_dir(self):
        load_dir = select_dir(os.getcwd())
        missing = 0
        if load_dir is not None:
            # load the experiment info only if no id is entered
            if os.path.isfile(os.path.join(load_dir, 'config')) and str(self.Id_widget.text()).strip() == '':
                self.load_main(load_dir)
            else:
                missing += 1
            conf_prep_file = os.path.join(load_dir, 'config_prep')
            if os.path.isfile(conf_prep_file):
                self.t.load_prep_tab(conf_prep_file)
            else:
                missing += 1
            conf_data_file = os.path.join(load_dir, 'config_data')
            if os.path.isfile(conf_data_file):
                self.t.load_data_tab(conf_data_file)
            else:
                missing += 1
            conf_rec_file = os.path.join(load_dir, 'config_rec')
            if os.path.isfile(conf_rec_file):
                self.t.load_rec_tab(conf_rec_file)
            else:
                missing += 1
            conf_disp_file = os.path.join(load_dir, 'config_disp')
            if os.path.isfile(conf_disp_file):
                self.t.load_disp_tab(conf_disp_file)
            else:
                missing += 1
            if missing == 5:
                msg_window('info: no configuration file found in load directory')
            else:
                self.set_conf_from_button.setStyleSheet("Text-align:left")
                self.set_conf_from_button.setText('config loaded')
                self.set_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        else:
            msg_window('please select valid conf directory')


    def set_working_dir(self):
        self.working_dir = select_dir(self.working_dir)
        if self.working_dir is not None:
            self.set_work_dir_button.setStyleSheet("Text-align:left")
            self.set_work_dir_button.setText(self.working_dir)
        else:
            self.set_work_dir_button.setText('')
            msg_window('please select valid working directory')
            return


    def load_main(self, load_dir):
        conf = os.path.join(load_dir, 'config')
        if not ver.ver_config(conf):
            msg_window('please check configuration file ' + conf + '. Cannot parse, ')
            return
        try:
            conf_map = ut.read_config(conf)
        except Exception:
            msg_window('please check configuration file ' + conf + '. Cannot parse, ')
            return

        try:
            self.working_dir = conf_map.working_dir
            self.set_work_dir_button.setStyleSheet("Text-align:left")
            self.set_work_dir_button.setText(self.working_dir)
        except:
            pass
        try:
            self.scan = conf_map.scan
            self.scan_widget.setText(self.scan)
        except:
            self.scan = None
        try:
            self.id = conf_map.experiment_id
            self.Id_widget.setText(self.id)
            if self.scan != None:
                self.exp_id = self.id + '_' + self.scan
            else:
                self.exp_id = self.id
            self.experiment_dir = os.path.join(self.working_dir, self.exp_id)
        except:
            pass

        if self.experiment_dir is not None:
            # this shows default results directory in display tab
            self.t.results_dir = os.path.join(self.experiment_dir, 'results')
            self.t.result_dir_button.setStyleSheet("Text-align:left")
            self.t.result_dir_button.setText(self.t.results_dir)
            self.update_rec_confis_choice()


    def update_rec_confis_choice(self):
            # this will update the configuration choices in reconstruction tab
            # fill out the config_id choice bar by reading configuration files names
            rec_ids = []
            for file in os.listdir(os.path.join(self.experiment_dir, 'conf')):
                if file.endswith('_config_rec'):
                    rec_ids.append(file[0:len(file)-len('_config_rec')])
            if len(rec_ids) > 0:
                self.t.rec_id.addItems(rec_ids)
                self.t.rec_id.show()


    def assure_experiment_dir(self):
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)
        experiment_conf_dir = os.path.join(self.experiment_dir, 'conf')
        if not os.path.exists(experiment_conf_dir):
            os.makedirs(experiment_conf_dir)
        else:
            self.update_rec_confis_choice()


    def set_experiment(self):
        self.id = str(self.Id_widget.text()).strip()
        if self.id == '' or self.working_dir is None:
            msg_window('id and working directory must be entered')
            return
        conf_map = {}

        self.scan = str(self.scan_widget.text()).strip()
        if self.scan is not '':
            scans = self.scan.split('-')
            if len(scans) > 2:
                msg_window('if entering scan or scan range, please enter numeric values, separated with "-" if range')
                return
            for sc in scans:
                try:
                    numeric = int(sc)
                except:
                    msg_window('if entering scan or scan range, please enter numeric values, separated with "-" if range')
                    return
            conf_map['scan'] = '"' + self.scan + '"'
            self.exp_id = self.id + '_' + self.scan
        else:
            self.exp_id = self.id
        self.experiment_dir = os.path.join(self.working_dir, self.exp_id)
        self.assure_experiment_dir()

        # read the configurations from GUI and write to experiment config files
        # save the main config
        conf_map['working_dir'] = '"' + str(self.working_dir).strip() + '"'
        conf_map['experiment_id'] = '"' + self.id + '"'
        self.write_conf(conf_map, os.path.join(self.experiment_dir, 'conf'), 'config')

        # save prep config
        conf_map = self.t.get_prep_config()
        if bool(conf_map):
            self.write_conf(conf_map, os.path.join(self.experiment_dir, 'conf'), 'config_prep')

        # save data config
        conf_map = self.t.get_data_config()
        if bool(conf_map):
            self.write_conf(conf_map, os.path.join(self.experiment_dir, 'conf'), 'config_data')

        # save rec config
        conf_map = self.t.get_rec_config()
        if bool(conf_map):
            self.write_conf(conf_map, os.path.join(self.experiment_dir, 'conf'), 'config_rec')

        # save disp config
        conf_map = self.t.get_disp_config()
        if bool(conf_map):
            self.write_conf(conf_map, os.path.join(self.experiment_dir, 'conf'), 'config_disp')

        # this shows default results directory in display window
        self.t.results_dir = os.path.join(self.experiment_dir, 'results')
        self.t.result_dir_button.setStyleSheet("Text-align:left")
        self.t.result_dir_button.setText(self.t.results_dir)


    def write_conf(self, conf_map, dir, file):
        # create "temp" file first, verify it, and if ok, copy to a configuration file
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

        if file == 'config':
            if not ver.ver_config(temp_file):
                os.remove(temp_file)
                msg_window('please check the entries in the main window. Cannot save this format')
                return False
        elif file == 'config_prep':
            if not ver.ver_config_prep(temp_file):
                os.remove(temp_file)
                msg_window('please check the entries in the Data prep tab. Cannot save this format')
                return False
        elif file == 'config_data':
            if not ver.ver_config_data(temp_file):
                os.remove(temp_file)
                msg_window('please check the entries in the Data tab. Cannot save this format')
                return False
        elif file.endswith('config_rec'):
            if not ver.ver_config_rec(temp_file):
                os.remove(temp_file)
                msg_window('please check the entries in the Reconstruction tab. Cannot save this format')
                return False
        elif file == 'config_disp':
            if not ver.ver_config_disp(temp_file):
                os.remove(temp_file)
                msg_window('please check the entries in the Display tab. Cannot save this format')
                return False
        # copy if verified
        shutil.move(temp_file, conf_file)
        return True

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
        self.results_dir = None
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
        self.separate_scans = QCheckBox()
        layout.addRow("separate scans", self.separate_scans)
        self.separate_scans.setChecked(False)
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
        self.set_prep_conf_from_button = QPushButton("Load prep conf from")
        self.set_prep_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        #layout.addWidget(self.set_prep_conf_from_button)
        self.prep_button = QPushButton('prepare', self)
        self.prep_button.setStyleSheet("background-color:rgb(175,208,156)")
        #layout.addWidget(self.prep_button)
        layout.addRow(self.set_prep_conf_from_button, self.prep_button)
        self.tab1.setLayout(layout)

        self.prep_button.clicked.connect(self.prepare)
        self.prep.currentIndexChanged.connect(lambda: self.load_prep(sub_layout))
        self.data_dir_button.clicked.connect(self.set_data_dir)
        self.spec_file_button.clicked.connect(self.set_spec_file)
        self.dark_file_button.clicked.connect(self.set_dark_file)
        self.white_file_button.clicked.connect(self.set_white_file)
        self.det_quad.textChanged.connect(lambda: self.set_overriden(self.det_quad))
        self.set_prep_conf_from_button.clicked.connect(self.load_prep_conf)


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

        elif str(self.prep.currentText()) == "copy from":
            self.ready_prep = QPushButton()
            layout.addRow("prep file", self.ready_prep)
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
        self.set_data_conf_from_button = QPushButton("Load data conf from")
        self.set_data_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        #layout.addRow(self.set_data_conf_from_button)
        self.config_data_button = QPushButton('format data', self)
        self.config_data_button.setStyleSheet("background-color:rgb(175,208,156)")
        #layout.addRow(self.config_data_button)
        layout.addRow(self.set_data_conf_from_button, self.config_data_button)
        self.tab2.setLayout(layout)

        # this will create config_data file and run data script
        # to generate data ready for reconstruction
        self.config_data_button.clicked.connect(self.format_data)
        self.set_data_conf_from_button.clicked.connect(self.load_data_conf)


    def tab3UI(self):
        self.mult_rec_conf = False
        self.old_conf_id = ''
        layout = QVBoxLayout()
        ulayout = QFormLayout()
        mlayout = QHBoxLayout()
        self.add_conf_button = QPushButton('add configuration', self)
        ulayout.addWidget(self.add_conf_button)
        self.rec_id = QComboBox()
        self.rec_id.InsertAtBottom
        self.rec_id.addItem("")
        ulayout.addWidget(self.rec_id)
        self.rec_id.hide()
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
        self.reconstructions = QLineEdit()
        ulayout.addRow("number of reconstructions", self.reconstructions)
        self.gc = QLineEdit()
        ulayout.addRow("gc triggers", self.gc)
        self.alg_seq = QLineEdit()
        ulayout.addRow("algorithm sequence", self.alg_seq)
        # TODO add logic to show this only if HIO is in sequence
        self.beta = QLineEdit()
        ulayout.addRow("beta", self.beta)
        self.rec_default_button = QPushButton('set to defaults', self)
        ulayout.addWidget(self.rec_default_button)

        llayout = QFormLayout()
        self.set_rec_conf_from_button = QPushButton("Load rec conf from")
        self.set_rec_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        #layout.addWidget(self.set_rec_conf_from_button)
        self.features = Features(self, mlayout)
        self.config_rec_button = QPushButton('run reconstruction', self)
        self.config_rec_button.setStyleSheet("background-color:rgb(175,208,156)")
        #layout.addWidget(self.config_rec_button)
        llayout.addRow(self.set_rec_conf_from_button, self.config_rec_button)
        spacer = QSpacerItem(0,3)
        llayout.addItem(spacer)

        layout.addLayout(ulayout)
        layout.addLayout(mlayout)
        layout.addLayout(llayout)

        self.tab3.setAutoFillBackground(True)
        self.tab3.setLayout(layout)

        self.config_rec_button.clicked.connect(self.reconstruction)
        self.cont.stateChanged.connect(lambda: self.toggle_cont(ulayout))
        self.rec_default_button.clicked.connect(self.rec_default)
        self.add_conf_button.clicked.connect(self.add_rec_conf)
        self.rec_id.currentIndexChanged.connect(self.toggle_conf)
        self.set_rec_conf_from_button.clicked.connect(self.load_rec_conf_dir)


    def toggle_cont(self, layout):
        cb_label = layout.labelForField(self.cont)
        if self.cont.isChecked():
            self.cont_dir = QLineEdit()
            layout.insertRow(2, "continue dir", self.cont_dir)
            cb_label.setStyleSheet('color: black')
        else:
            cb_label.setStyleSheet('color: grey')


    def add_rec_conf(self):
        id, ok = QInputDialog.getText(self, '',"enter configuration id")
        if ok and len(id) > 0:
            if self.mult_rec_conf:
                self.rec_id.addItem(id)
            else:
                self.mult_rec_conf = True
                self.rec_id.show()
                self.rec_id.addItem(id)
            #self.rec_id.setCurrentIndex(self.rec_id.count()-1)

        # copy the config_rec into <id>_config_rec and show the
        conf_file = os.path.join(self.main_win.experiment_dir, 'conf', 'config_rec')
        new_conf_file = os.path.join(self.main_win.experiment_dir, 'conf', id + '_config_rec')
        shutil.copyfile(conf_file, new_conf_file)
        self.rec_id.setCurrentIndex(self.rec_id.count()-1)


    def toggle_conf(self):
        # save the configuration file before updating the incoming config
        if self.old_conf_id == '':
            conf_file = 'config_rec'
        else:
            conf_file = self.old_conf_id + '_config_rec'

        conf_map = self.get_rec_config()
        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')

        if self.main_win.write_conf(conf_map, conf_dir, conf_file):
            self.old_conf_id = str(self.rec_id.currentText())
        else:
            msg_window('configuration  ' + conf_file + ' was not saved')
        # if a config file corresponding to the rec id exists, load it
        # otherwise read from base configuration and load
        if self.old_conf_id == '':
            conf_file = os.path.join(conf_dir, 'config_rec')
        else:
            conf_file = os.path.join(conf_dir, self.old_conf_id + '_config_rec')

        if os.path.isfile(conf_file):
            self.load_rec_tab(conf_file)
        else:
            self.load_rec_tab(os.path.join(conf_dir, 'config_rec'))


    def tab4UI(self):
        layout = QFormLayout()
        self.result_dir_button = QPushButton()
        layout.addRow("results directory", self.result_dir_button)
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
        layout.addRow("arm (mm)", self.arm)
        self.dth = QLineEdit()
        layout.addRow("dth (deg)", self.dth)
        self.pixel = QLineEdit()
        layout.addRow("pixel", self.pixel)
        self.set_disp_conf_from_button = QPushButton("Load disp conf from")
        self.set_disp_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        #layout.addRow(self.set_disp_conf_from_button)
        self.config_disp = QPushButton('process display', self)
        self.config_disp.setStyleSheet("background-color:rgb(175,208,156)")
        #layout.addRow(self.config_disp)
        layout.addRow(self.set_disp_conf_from_button, self.config_disp)
        self.tab4.setLayout(layout)

        self.result_dir_button.clicked.connect(self.set_results_dir)
        self.spec_file_button1.clicked.connect(self.set_spec_file)
        self.config_disp.clicked.connect(self.display)
        self.energy.textChanged.connect(lambda: self.set_overriden(self.energy))
        self.delta.textChanged.connect(lambda: self.set_overriden(self.delta))
        self.gamma.textChanged.connect(lambda: self.set_overriden(self.gamma))
        self.arm.textChanged.connect(lambda: self.set_overriden(self.arm))
        self.dth.textChanged.connect(lambda: self.set_overriden(self.dth))
        self.pixel.textChanged.connect(lambda: self.set_overriden(self.pixel))
        self.set_disp_conf_from_button.clicked.connect(self.load_disp_conf)
        self.layout4 = layout


    def load_prep_tab(self, conf):
        if not os.path.isfile(conf):
            msg_window('info: the load directory does not contain config_prep file')
            return
        if not ver.ver_config_prep(conf):
            msg_window('please check configuration file ' + conf + '. Cannot parse, ')
            return
        try:
            conf_map = ut.read_config(conf)
        except Exception as e:
            msg_window('please check configuration file ' + conf + '. Cannot parse, ' + str(e))
            return

        try:
            separate_scans = conf_map.separate_scans
            if separate_scans:
                self.separate_scans.setChecked(True)
        except:
            pass
        try:
            self.data_dir = conf_map.data_dir
            self.data_dir_button.setStyleSheet("Text-align:left")
            self.data_dir_button.setText(self.data_dir)
        except:
            self.data_dir = None
            self.data_dir_button.setText('')
        try:
            self.specfile = conf_map.specfile
            self.spec_file_button.setStyleSheet("Text-align:left")
            self.spec_file_button.setText(self.specfile)
            # set specfile also in display tab
            self.spec_file_button1.setStyleSheet("Text-align:left")
            self.spec_file_button1.setText(self.specfile)
        except:
            self.specfile = None
            self.spec_file_button.setText('')
            self.spec_file_button1.setText('')
        try:
            self.darkfile = conf_map.darkfile
            self.dark_file_button.setStyleSheet("Text-align:left")
            self.dark_file_button.setText(self.darkfile)
        except:
            self.darkfile = None
            self.dark_file_button.setText('')
        try:
            self.whitefile = conf_map.whitefile
            self.white_file_button.setStyleSheet("Text-align:left")
            self.white_file_button.setText(self.whitefile)
        except:
            self.whitefile = None
            self.white_file_button.setText('')
        try:
            self.min_files.setText(str(conf_map.min_files).replace(" ", ""))
        except:
            pass
        try:
            self.exclude_scans.setText(str(conf_map.exclude_scans).replace(" ", ""))
        except:
            pass
        try:
            self.det_quad.setText(str(conf_map.det_quad).replace(" ", ""))
        except:
            pass
        prep_file = None
        try:
            prep_file = conf_map.prep_file
        except:
            pass
        if prep_file is not None:
            self.prep.setCurrentIndex(2)
            self.ready_prep.setStyleSheet("Text-align:left")
            self.ready_prep.setText(prep_file)


    def load_data_tab(self, conf):
        if not os.path.isfile(conf):
            msg_window('info: the load directory does not contain config_data file')
            return
        if not ver.ver_config_data(conf):
            msg_window('please check configuration file ' + conf + '. Cannot parse, ')
            return
        try:
            conf_map = ut.read_config(conf)
        except Exception as e:
            msg_window('please check configuration file ' + conf + '. Cannot parse, ' + str(e))
            return

        try:
            self.aliens.setText(str(conf_map.aliens).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.amp_threshold.setText(str(conf_map.amp_threshold).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.binning.setText(str(conf_map.binning).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.center_shift.setText(str(conf_map.center_shift).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.adjust_dimensions.setText(str(conf_map.adjust_dimensions).replace(" ", ""))
        except AttributeError:
            pass


    def load_rec_tab(self, conf):
        if not os.path.isfile(conf):
            msg_window('info: the load directory does not contain config_rec file')
            return
        if not ver.ver_config_rec(conf):
            msg_window('please check configuration file ' + conf + '. Cannot parse, ')
            return
        try:
            conf_map = ut.read_config(conf)
        except Exception as e:
            msg_window('please check configuration file ' + conf + '. Cannot parse, ' + str(e))
            return

        try:
            self.device.setText(str(conf_map.device).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.reconstructions.setText(str(conf_map.reconstructions).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.gc.setText(str(conf_map.garbage_trigger).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.alg_seq.setText(str(conf_map.algorithm_sequence).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.beta.setText(str(conf_map.beta).replace(" ", ""))
        except AttributeError:
            pass

        for feat_id in self.features.feature_dir:
            self.features.feature_dir[feat_id].init_config(conf_map)


    def load_disp_tab(self, conf):
        if not os.path.isfile(conf):
            msg_window('info: the load directory does not contain config_disp file')
            return
        if not ver.ver_config_data(conf):
            msg_window('please check configuration file ' + conf + '. Cannot parse, ')
            return
        try:
            conf_map = ut.read_config(conf)
        except Exception as e:
            msg_window('please check configuration file ' + conf + '. Cannot parse, ' + str(e))
            return

        try:
            specfile = conf_map.specfile
            self.specfile = specfile
            self.spec_file_button1.setStyleSheet("Text-align:left")
            self.spec_file_button1.setText(self.specfile)
            if os.path.isfile(self.specfile):
                self.parse_spec()
        except AttributeError:
            pass
        # if parameters are configured, override the readingsfrom spec file
        try:
            self.crop.setText(str(conf_map.crop).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.energy.setText(str(conf_map.energy).replace(" ", ""))
            self.energy.setStyleSheet('color: black')
        except AttributeError:
            pass
        try:
            self.delta.setText(str(conf_map.delta).replace(" ", ""))
            self.delta.setStyleSheet('color: black')
        except AttributeError:
            pass
        try:
            self.gamma.setText(str(conf_map.gamma).replace(" ", ""))
            self.gamma.setStyleSheet('color: black')
        except AttributeError:
            pass
        try:
            self.arm.setText(str(conf_map.arm).replace(" ", ""))
            self.arm.setStyleSheet('color: black')
        except AttributeError:
            pass
        try:
            self.dth.setText(str(conf_map.dth).replace(" ", ""))
            self.dth.setStyleSheet('color: black')
        except AttributeError:
            pass
        try:
            self.pixel.setText(str(conf_map.pixel).replace(" ", ""))
            self.pixel.setStyleSheet('color: black')
        except AttributeError:
            pass


    def get_prep_config(self):
        conf_map = {}
        if self.data_dir is not None:
            conf_map['data_dir'] = '"' + str(self.data_dir).strip() + '"'
        if self.specfile is not None:
            conf_map['specfile'] = '"' + str(self.specfile).strip() + '"'
        if self.darkfile is not None:
            conf_map['darkfile'] = '"' + str(self.darkfile).strip() + '"'
        if self.whitefile is not None:
            conf_map['whitefile'] = '"' + str(self.whitefile).strip() + '"'
        if self.separate_scans.isChecked():
            conf_map['separate_scans'] = 'true'
        if len(self.min_files.text()) > 0:
            min_files = str(self.min_files.text())
            conf_map['min_files'] = min_files
        if len(self.exclude_scans.text()) > 0:
            conf_map['exclude_scans'] = str(self.exclude_scans.text()).replace('\n','')
        if len(self.det_quad.text()) > 0:
            det_quad = str(self.det_quad.text())
            conf_map['det_quad'] = det_quad
        try:
            if str(self.ready_prep.text()) != '':
                conf_map['prep_file'] = '"' + str(self.prep_file) + '"'
        except:
            pass

        return conf_map


    def get_data_config(self):
        conf_map = {}
        if len(self.aliens.text()) > 0:
            conf_map['aliens'] = str(self.aliens.text()).replace('\n', '')
        if len(self.amp_threshold.text()) > 0:
            conf_map['amp_threshold'] = str(self.amp_threshold.text())
        else:
            msg_window('amplitude threshold not defined. Quiting operation.')
            return
        if len(self.binning.text()) > 0:
            conf_map['binning'] = str(self.binning.text()).replace('\n', '')
        if len(self.center_shift.text()) > 0:
            conf_map['center_shift'] = str(self.center_shift.text()).replace('\n', '')
        if len(self.adjust_dimensions.text()) > 0:
            conf_map['adjust_dimensions'] = str(self.adjust_dimensions.text()).replace('\n', '')

        return conf_map


    def get_rec_config(self):
        conf_map = {}
        if len(self.reconstructions.text()) > 0:
            conf_map['reconstructions'] = str(self.reconstructions.text())
        if len(self.device.text()) > 0:
            conf_map['device'] = str(self.device.text()).replace('\n','')
        if len(self.gc.text()) > 0:
            conf_map['garbage_trigger'] = str(self.gc.text()).replace('\n','')
        if len(self.alg_seq.text()) > 0:
            conf_map['algorithm_sequence'] = str(self.alg_seq.text()).replace('\n','')
        if len(self.beta.text()) > 0:
            conf_map['beta'] = str(self.beta.text())
        if self.cont.isChecked():
            conf_map['continue_dir'] = str(self.cont_dir.text())

        for feat_id in self.features.feature_dir:
            self.features.feature_dir[feat_id].add_config(conf_map)

        return conf_map


    def get_disp_config(self):
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
            conf_map['pixel'] = str(self.pixel.text()).replace('\n', '')
        if len(self.crop.text()) > 0:
            conf_map['crop'] = str(self.crop.text()).replace('\n', '')

        return conf_map


    def load_prep_conf(self):
        prep_file = select_file(os.getcwd())
        if prep_file is not None:
            self.load_prep_tab(prep_file)
            self.set_prep_conf_from_button.setStyleSheet("Text-align:left")
            self.set_prep_conf_from_button.setText('config loaded')
            self.set_prep_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        else:
            msg_window('please select valid prep config file')


    def load_data_conf(self):
        data_file = select_file(os.getcwd())
        if data_file is not None:
            self.load_data_tab(data_file)
            self.set_data_conf_from_button.setStyleSheet("Text-align:left")
            self.set_data_conf_from_button.setText('config loaded')
            self.set_data_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
            # # save data config
            # conf_map = self.get_data_config()
            # self.main_win.write_conf(conf_map, os.path.join(self.main_win.experiment_dir, 'conf'), 'config_data')
        else:
            msg_window('please select valid data config file')

    def load_rec_conf_dir(self):
        rec_file = select_file(os.getcwd())
        if rec_file is not None:
            self.load_rec_tab(rec_file)
            self.set_rec_conf_from_button.setStyleSheet("Text-align:left")
            self.set_rec_conf_from_button.setText('config loaded')
            self.set_rec_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
            # # save rec config
            # conf_map = self.get_rec_config()
            # self.main_win.write_conf(conf_map, os.path.join(self.main_win.experiment_dir, 'conf'), 'config_rec')
        else:
            msg_window('please select valid rec config file')


    def load_disp_conf(self):
        disp_file = select_file(os.getcwd())
        if disp_file is not None:
            self.load_disp_tab(disp_file)
            self.set_disp_conf_from_button.setStyleSheet("Text-align:left")
            self.set_disp_conf_from_button.setText('config loaded')
            self.set_disp_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
            self.parse_spec()
            # # save disp config
            # conf_map = self.get_disp_config()
            # self.main_win.write_conf(conf_map, os.path.join(self.main_win.experiment_dir, 'conf'), 'config_disp')
        else:
            msg_window('please select valid disp config file')


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
            self.spec_file_button1.setText('')


    def parse_spec(self):
        try:
            last_scan = int(self.main_win.scan.split('-')[-1])
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
        except:
            print ('scan not available, cannot parse spec')


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
        self.prep_file = select_file(self.main_win.working_dir)
        if self.prep_file is not None:
            selected = str(self.prep_file)
            if not selected.endswith('tif') and not selected.endswith('tiff'):
                msg_window("the file extension must be tif or tiff")
                return
            self.ready_prep.setStyleSheet("Text-align:left")
            self.ready_prep.setText(self.prep_file)
        else:
            self.ready_prep.setText('')


    def set_prep_script(self):
        self.script = select_file(self.main_win.working_dir)
        if self.script is not None:
            self.script_button.setStyleSheet("Text-align:left")
            self.script_button.setText(self.script)
            # fill the arguments with experiment_dir, scans, config file
            conf_file = os.path.join(self.main_win.experiment_dir, 'conf', 'config_prep')
            self.args.setText(str(self.main_win.experiment_dir) + ',' + str(self.main_win.scan) + ',' + conf_file)
        else:
            self.script_button.setText('')


    def prepare(self):
        if not self.main_win.is_exp_exists():
            msg_window('the experiment has not been created yet')
        elif not self.main_win.is_exp_set():
            msg_window('the experiment has changed, pres "set experiment" button')
        else:
            conf_map = self.get_prep_config()
            if str(self.prep.currentText()) == "custom":
                self.prepare_custom(conf_map)
            elif str(self.prep.currentText()) == "34ID prep":
                self.prepare_34id(conf_map)
            elif str(self.prep.currentText()) == "copy from":
                self.prepare_copy(conf_map)


    def prepare_custom(self, conf_map):
        # determine script directory and script name
        if self.script is None:
            msg_window("script not defined")
            return
        full_script = str(self.script)
        script_info = full_script.split('/')
        script = script_info[len(script_info)-1]
        script_dir = full_script[0 : -(len(script)+1)]
        script = script[0 : -3]
        func = str(self.prep_exec.text())
        if len(func) == 0:
            msg_window("function not defined")
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
        if self.main_win.write_conf(conf_map, conf_dir, 'config_prep'):
            try:
                prep_data = f(*args)
            except Exception as e:
                msg_window('custom script failed ' + str(e))
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
            pass

        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
        conf_file = os.path.join(conf_dir, 'config_prep')
        if self.main_win.write_conf(conf_map, conf_dir, 'config_prep'):
            f = getattr(mod, 'prepare')
            f(self.main_win.experiment_dir, scan_range, conf_file)


    def prepare_copy(self, conf_map):
        # save the file as experiment prep file
        prep_dir = os.path.join(self.main_win.experiment_dir, 'prep')
        if not os.path.exists(prep_dir):
            os.makedirs(prep_dir)
        exp_prep_file = os.path.join(prep_dir, 'prep_data.tif')
        shutil.copyfile(self.prep_file, exp_prep_file)
        # save config_prep
        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
        self.main_win.write_conf(conf_map, conf_dir, 'config_prep')


    def format_data(self):
        if not self.main_win.is_exp_exists():
            msg_window('the experiment has not been created yet')
        elif not self.main_win.is_exp_set():
            msg_window('the experiment has changed, pres "set experiment" button')
        else:
            if os.path.isfile(os.path.join(self.main_win.experiment_dir, 'prep','prep_data.tif'))\
                    or self.separate_scans.isChecked():
                conf_map = self.get_data_config()
                conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
                if self.main_win.write_conf(conf_map, conf_dir, 'config_data'):
                    run_dt.data(self.main_win.experiment_dir)
            else:
                msg_window('Please, run data preparation in previous tab to activate this function')


    def reconstruction(self):
        if not self.main_win.is_exp_exists():
            msg_window('the experiment has not been created yet')
        elif not self.main_win.is_exp_set():
            msg_window('the experiment has changed, pres "set experiment" button')
        else:
            if os.path.isfile(os.path.join(self.main_win.experiment_dir, 'data', 'data.tif'))\
                    or self.separate_scans.isChecked():
                # find out which configuration should be saved
                if self.old_conf_id == '':
                    conf_file = 'config_rec'
                    conf_id = None
                else:
                    conf_file = self.old_conf_id + '_config_rec'
                    conf_id = self.old_conf_id

                conf_map = self.get_rec_config()
                conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')

                if self.main_win.write_conf(conf_map, conf_dir, conf_file):
                    run_rc.reconstruction(str(self.proc.currentText()), self.main_win.experiment_dir, conf_id)
            else:
                msg_window('Please, run format data in previous tab to activate this function')


    def set_results_dir(self):
        if self.main_win.is_exp_exists():
            self.results_dir = os.path.join(self.main_win.experiment_dir, 'results')
            self.results_dir = select_dir(self.results_dir)
            if self.results_dir is not None:
                if self.results_dir.endswith('results'):
                    self.result_dir_button.setStyleSheet("Text-align:left")
                    self.result_dir_button.setText(self.results_dir)
                else:
                    msg_window('Please, select directory ending with "results"')
                    self.results_dir = None
            else:
                self.result_dir_button.setText('')
        else:
            msg_window('the experiment has not been created yet')


    def display(self):
        if not self.main_win.is_exp_exists():
            msg_window('the experiment has not been created yet')
            return
        if not self.main_win.is_exp_set():
            msg_window('the experiment has changed, pres "set experiment" button')
            return
        # check if the results directory exists
        res_dir = os.path.join(self.main_win.experiment_dir, 'results')
        if not (os.path.isfile(os.path.join(res_dir, 'image.npy')) or self.separate_scans.isChecked()):
            msg_window('Please, run reconstruction in previous tab to activate this function')
            return
        if (self.specfile is None or not os.path.isfile(self.specfile)) and \
           (len(self.energy.text()) == 0 or \
            len(self.delta.text()) == 0 or \
            len(self.gamma.text()) == 0 or \
            len(self.arm.text()) == 0 or \
            len(self.dth.text()) == 0 or \
            len(self.pixel.text()) == 0):
                msg_window('Please, enter spec file or all detector parameters')
                return

        conf_map = self.get_disp_config()

        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
        if self.main_win.write_conf(conf_map, conf_dir, 'config_disp'):
            if self.results_dir is None:
                run_dp.to_vtk(self.main_win.experiment_dir)
            else:
                dir = str(self.results_dir).split('/')[-1]
                if dir == 'results':
                    run_dp.to_vtk(self.main_win.experiment_dir)
                else:
                    run_dp.to_vtk(self.main_win.experiment_dir, dir[0:-len('_results')])


    def rec_default(self):
        if  self.main_win.working_dir is None or self.main_win.id is None or \
            len(self.main_win.working_dir) == 0 or len(self.main_win.id) == 0:
            msg_window('Working Directory or Reconstruction ID not configured')
        else:
            self.reconstructions.setText('1')
            self.device.setText('(0,1)')
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
    ex = cdi_gui()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
