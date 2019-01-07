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
import reccdi.src_py.run_scripts.run_34id_prepare as prep


def select_file(start_dir):
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec_() == QDialog.Accepted:
        return str(dialog.selectedFiles()[0])


def select_dir(start_dir):
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.DirectoryOnly)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec_() == QDialog.Accepted:
        return str(dialog.selectedFiles()[0])


def write_conf(conf_map, dir, file):
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
    shutil.move(temp_file, conf_file)


class cdi_conf(QWidget):
    def __init__(self, parent=None):
        super(cdi_conf, self).__init__(parent)
        uplayout = QFormLayout()

        self.set_work_dir_button = QPushButton()
        uplayout.addRow("Working Directory", self.set_work_dir_button)
        self.Id_widget = QLineEdit()
        uplayout.addRow("Reconstruction ID", self.Id_widget)
        self.scan_widget = QLineEdit()
        uplayout.addRow("scan(s)", self.scan_widget)
        self.run_button = QPushButton('run_everything', self)
        uplayout.addWidget(self.run_button)

        vbox = QVBoxLayout()
        vbox.addLayout(uplayout)

        self.t = cdi_conf_tab(self)
        vbox.addWidget(self.t)

        self.setLayout(vbox)
        self.setWindowTitle("CDI Reconstruction")
        self.set_init()

        self.set_work_dir_button.clicked.connect(self.set_working_dir)
        self.Id_widget.textChanged.connect(self.set_id)
        self.scan_widget.textChanged.connect(self.set_scan)
        self.run_button.clicked.connect(self.run_everything)


    def set_working_dir(self):
        self.working_dir = select_dir(self.working_dir)
        self.set_work_dir_button.setStyleSheet("Text-align:left")
        self.set_work_dir_button.setText(self.working_dir)


    def set_id(self):
        self.id = str(self.Id_widget.text())
        self.set_experiment_dir()


    def set_scan(self):
        self.scan = str(self.scan_widget.text())
        self.set_experiment_dir()


    def set_experiment_dir(self):
        if self.id is not None and self.scan is not None:
            self.exp_id = self.id + '_' + self.scan
            self.experiment_dir = os.path.join(self.working_dir, self.exp_id)


    def run_everything(self):
        self.t.prepare()
        self.t.model_data()
        self.t.reconstruction()
        self.t.display()


    def set_init(self):
        self.id = None
        self.scan = None
        # check for the "conf" directory in the running directory
        if os.path.isdir('conf/last'):
            self.set_from_conf('conf/last')
        elif os.path.isdir('conf/defaults'):
            self.set_from_conf('conf/defaults')


    def set_from_conf(self, dir):
        print ('dir', dir)
        main_conf = os.path.join(dir, 'config')
        conf_map = ut.read_config(main_conf)
        # initialize to the value from config file
        self.working_dir = conf_map.working_dir
        self.t.data_dir = conf_map.data_dir
        self.t.specfile = conf_map.specfile
        self.t.darkfile = conf_map.darkfile
        self.t.whitefile = conf_map.whitefile
        # set the text in the window
        self.set_work_dir_button.setStyleSheet("Text-align:left")
        self.set_work_dir_button.setText(self.working_dir)
        self.t.data_dir_button.setStyleSheet("Text-align:left")
        self.t.data_dir_button.setText(self.t.data_dir)
        self.t.spec_file_button.setStyleSheet("Text-align:left")
        self.t.spec_file_button.setText(self.t.specfile)
        self.t.dark_file_button.setStyleSheet("Text-align:left")
        self.t.dark_file_button.setText(self.t.darkfile)
        self.t.white_file_button.setStyleSheet("Text-align:left")
        self.t.white_file_button.setText(self.t.whitefile)

        # initialize "Data" tab
        data_conf = os.path.join(dir, 'config_data')
        conf_map = ut.read_config(data_conf)
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
        conf_map = ut.read_config(rec_conf)
        try:
            self.t.device.setText(str(conf_map.device).replace(" ", ""))
        except AttributeError:
            pass
        try:
            self.t.threads.setText(str(conf_map.threads).replace(" ", ""))
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
        conf_map = ut.read_config(disp_conf)
        try:
            self.t.crop.setText(str(conf_map.crop).replace(" ", ""))
        except AttributeError:
            pass


class cdi_conf_tab(QTabWidget):
    def __init__(self, main_win, parent=None):
        super(cdi_conf_tab, self).__init__(parent)
        self.main_win = main_win
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        self.addTab(self.tab1, "34ID prep")
        self.addTab(self.tab2, "Data")
        self.addTab(self.tab3, "Reconstruction")
        self.addTab(self.tab4, "Display")
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()
        self.tab4UI()


    def tab1UI(self):
        layout = QFormLayout()
        self.data_dir_button = QPushButton()
        layout.addRow("data directory", self.data_dir_button)
        self.spec_file_button = QPushButton()
        layout.addRow("spec file", self.spec_file_button)
        self.dark_file_button = QPushButton()
        layout.addRow("darkfield file", self.dark_file_button)
        self.white_file_button = QPushButton()
        layout.addRow("whitefield file", self.white_file_button)
        self.prep_button = QPushButton('prepare', self)
        layout.addWidget(self.prep_button)
        self.tab1.setLayout(layout)

        self.prep_button.clicked.connect(self.prepare)
        self.data_dir_button.clicked.connect(self.set_data_dir)
        self.spec_file_button.clicked.connect(self.set_spec_file)
        self.dark_file_button.clicked.connect(self.set_dark_file)
        self.white_file_button.clicked.connect(self.set_white_file)


    def tab2UI(self):
        layout = QFormLayout()
        self.aliens = QLineEdit()
        layout.addRow("aliens", self.aliens)
        self.amp_threshold = QLineEdit()
        layout.addRow("amp_threshold", self.amp_threshold)
        self.binning = QLineEdit()
        layout.addRow("binning", self.binning)
        self.center_shift = QLineEdit()
        layout.addRow("center_shift", self.center_shift)
        self.adjust_dimensions = QLineEdit()
        layout.addRow("adjust_dimensions", self.adjust_dimensions)
        self.config_data_button = QPushButton('model data', self)
        layout.addWidget(self.config_data_button)
        self.tab2.setLayout(layout)

        # this will create config_data file and run data script
        # to generate data ready for recondtruction
        self.config_data_button.clicked.connect(self.model_data)


    def tab3UI(self):
        layout = QVBoxLayout()
        ulayout = QFormLayout()
        llayout = QHBoxLayout()
        self.cont = QCheckBox()
        ulayout.addRow("continuation", self.cont)
        self.cont.setChecked(False)
        self.device = QLineEdit()
        ulayout.addRow("device(s)", self.device)
        self.threads = QLineEdit()
        ulayout.addRow("number of threads", self.threads)
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
            label = layout.labelForField(self.cont_dir)
            self.cont_dir.setParent(None)
            label.setParent(None)
            cb_label.setStyleSheet('color: grey')


    def tab4UI(self):
        layout = QFormLayout()
        self.crop = QLineEdit()
        layout.addRow("crop", self.crop)
        self.config_disp_button = QPushButton('process display', self)
        layout.addWidget(self.config_disp_button)
        self.tab4.setLayout(layout)

        self.config_disp_button.clicked.connect(self.display)


    def set_spec_file(self):
        self.specfile = select_file(self.specfile)
        self.spec_file_button.setStyleSheet("Text-align:left")
        self.spec_file_button.setText(self.specfile)


    def set_dark_file(self):
        self.darkfile = select_file(self.darkfile)
        self.dark_file_button.setStyleSheet("Text-align:left")
        self.dark_file_button.setText(self.darkfile)


    def set_white_file(self):
        self.whitefile = select_file(self.whitefile)
        self.white_file_button.setStyleSheet("Text-align:left")
        self.white_file_button.setText(self.whitefile)


    def set_data_dir(self):
        self.data_dir = select_dir(self.data_dir)
        self.data_dir_button.setStyleSheet("Text-align:left")
        self.data_dir_button.setText(self.data_dir)


    def prepare(self):
        scan = str(self.main_win.scan_widget.text())
        if  self.main_win.working_dir is None or \
            self.main_win.id is None or\
            scan is None or \
            self.data_dir is None or \
            self.specfile is None:
            print ('enter all parameters: working_dir, id, scan, data_dir, specfile')
            return

        try:
            # after checking that scan is entered convert it to list of int
            scan_range = scan.split('-')
            for i in range(len(scan_range)):
                scan_range[i] = int(scan_range[i])
        except:
            print('enter numeric values for scan range')

        conf_map = {}
        if len(self.main_win.working_dir) > 0:
            conf_map['working_dir'] = '"' + str(self.main_win.working_dir) + '"'
        else:
            print ("working_dir not defined")
        if len(self.data_dir) > 0:
            conf_map['data_dir'] = '"' + str(self.data_dir) + '"'
        else:
            print ("data_dir not defined")
        if len(self.specfile) > 0:
            conf_map['specfile'] = '"' + str(self.specfile) + '"'
        else:
            print ("specfile not defined")
        if len(self.darkfile) > 0:
            conf_map['darkfile'] = '"' + str(self.darkfile) + '"'
        else:
            print ("darkfile not defined")
        if len(self.whitefile) > 0:
            conf_map['whitefile'] = '"' + str(self.whitefile) + '"'
        else:
            print ("whitefile not defined")

        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
        write_conf(conf_map, conf_dir, 'config')

        prep.prepare(self.main_win.working_dir, self.main_win.exp_id, scan_range, self.data_dir, self.specfile, self.darkfile, self.whitefile)


    def model_data(self):
        conf_map = {}
        if len(self.aliens.text()) > 0:
            conf_map['aliens'] = str(self.aliens.text()).replace('\n','')
        else:
            print ("aliens not defined")
        if len(self.amp_threshold.text()) > 0:
            conf_map['amp_threshold'] = str(self.amp_threshold.text())
        else:
            print ('amplitude threshold not defined. Quiting operation.')
            return
        if len(self.binning.text()) > 0:
            conf_map['binning'] = str(self.binning.text()).replace('\n','')
        else:
            print ("binning not defined")
        if len(self.center_shift.text()) > 0:
            conf_map['center_shift'] = str(self.center_shift.text()).replace('\n','')
        else:
            print ("center shift not defined")
        if len(self.adjust_dimensions.text()) > 0:
            conf_map['adjust_dimensions'] = str(self.adjust_dimensions.text()).replace('\n','')
        else:
            print ("adjust dimensions not defined")

        #self.create_config('config_data', conf_map)
        conf_dir = os.path.join(self.main_win.experiment_dir, 'conf')
        write_conf(conf_map, conf_dir, 'config_data')

        run_dt.data(self.main_win.experiment_dir)


    def reconstruction(self):
        conf_map = {}
        conf_map['threads'] = str(self.threads.text())
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
        write_conf(conf_map, conf_dir, 'config_rec')

        run_rc.reconstruction('cpu', self.main_win.experiment_dir)


    def display(self):
        if len(self.crop.text()) == 0:
            print ('crop not configured')

        disp_conf_file = os.path.join(self.main_win.experiment_dir, 'conf', 'config_disp')
        temp_file = os.path.join(self.main_win.experiment_dir, 'conf', 'temp')
        with open(temp_file, 'a') as temp:
            try:
                with open(disp_conf_file, 'r') as f:
                    for line in f:
                        if not line.startswith('crop') and not line.startswith('binning'):
                            temp.write(line)
                f.close()
            except:
                pass

            if len(self.crop.text()) != 0:
                temp.write('crop = ' + str(self.crop.text()) + '\n')

        temp.close()
        shutil.move(temp_file, disp_conf_file)

        run_dp.to_vtk(self.main_win.experiment_dir)


    def rec_default(self):
        if  self.main_win.working_dir is None or self.main_win.id is None or \
            len(self.main_win.working_dir) == 0 or len(self.main_win.id) == 0:
                print ('Working Directory or Reconstruction ID not configured')
        else:
            self.threads.setText('1')
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
        self.active.setChecked(True)
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
        self.active.setChecked(False)


    def fill_active(self, layout):
        self.generations = QLineEdit()
        layout.addRow("generations", self.generations)
        self.lr_generations = QLineEdit()
        layout.addRow("low resolution generations", self.lr_generations)
        self.lr_sigma_alg = QLineEdit()
        layout.addRow("low resolution sigma algorithm", self.lr_sigma_alg)
        self.lr_sigmas = QLineEdit()
        layout.addRow("low resolution sigmas", self.lr_sigmas)
        self.lr_sigma_min = QLineEdit()
        layout.addRow("low resolution sigma min", self.lr_sigma_min)
        self.lr_sigma_max = QLineEdit()
        layout.addRow("low resolution sigma max", self.lr_sigma_max)
        self.lr_scale_power = QLineEdit()
        layout.addRow("low resolution scale power", self.lr_scale_power)
        self.lr_algorithm = QLineEdit()
        layout.addRow("low resolution algorithm", self.lr_algorithm)


    def add_feat_conf(self, conf_map):
        conf_map['generations'] = str(self.generations.text())
        conf_map['low_resolution_generations'] = str(self.lr_generations.text())
        conf_map['low_resolution_sigma_alg'] = str(self.lr_sigma_alg.text())
        conf_map['low_resolution_sigmas'] = str(self.lr_sigmas.text())
        conf_map['low_resolution_sigma_min'] = str(self.lr_sigma_min.text())
        conf_map['low_resolution_sigma_max'] = str(self.lr_sigma_max.text())
        conf_map['low_resolution_scale_power'] = str(self.lr_scale_power.text())
        conf_map['low_resolution_alg'] = str(self.lr_algorithm.text())


class low_resolution(Feature):
    def __init__(self):
        super(low_resolution, self).__init__()
        self.id = 'low resolution'


    def init_config(self, conf_map):
        try:
            self.res_triggers.setText(str(conf_map.resolution_trigger).replace(" ", ""))
        except AttributeError:
            pass
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
            self.support_triggers.setText(str(conf_map.amp_support_trigger).replace(" ", ""))
        except AttributeError:
            pass
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
        self.support_type.setText('"GAUSS"')
        self.support_area.setText('[.5,.5,.5]')
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
            self.phase_triggers.setText(str(conf_map.phase_support_trigger).replace(" ", ""))
        except AttributeError:
            pass
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
            self.pcdi_triggers.setText(str(conf_map.pcdi_trigger).replace(" ", ""))
        except AttributeError:
            pass
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
        self.pcdi_type.setText('"LUCY"')
        self.pcdi_iter.setText('20')
        self.pcdi_normalize.setText('true')
        self.pcdi_roi.setText('[32,32,16]')


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
            self.twin_triggers.setText(str(conf_map.twin_trigger).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.twin_triggers = QLineEdit()
        layout.addRow("twin triggers", self.twin_triggers)


    def rec_default(self):
        self.twin_triggers.setText('(2)')


    def add_feat_conf(self, conf_map):
        conf_map['twin_trigger'] = str(self.twin_triggers.text()).replace('\n','')


class average(Feature):
    def __init__(self):
        super(average, self).__init__()
        self.id = 'average'


    def init_config(self, conf_map):
        try:
            self.average_triggers.setText(str(conf_map.average_trigger).replace(" ", ""))
        except AttributeError:
            pass


    def fill_active(self, layout):
        self.average_triggers = QLineEdit()
        layout.addRow("average triggers", self.average_triggers)


    def rec_default(self):
        self.average_triggers.setText('(-400,1)')


    def add_feat_conf(self, conf_map):
        conf_map['avarage_trigger'] = str(self.average_triggers.text()).replace('\n','')



class Features(QWidget):
    def __init__(self, tab, layout):
        super(Features, self).__init__()
        feature_ids = ['GA', 'low resolution', 'amplitude support', 'phase support', 'pcdi', 'twin', 'average']
        self.leftlist = QListWidget()
        self.feature_dir = {'GA' : GA(),
                            'low resolution' : low_resolution(),
                            'amplitude support' : amplitude_support(),
                            'phase support' : phase_support(),
                            'pcdi' : pcdi(),
                            'twin' : twin(),
                            'average' : average()}
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