import sys
import os
import shutil
import prep
from PyQt4.QtCore import *
from PyQt4.QtGui import *


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


class cdi_conf(QWidget):
    def __init__(self, parent=None):
        super(cdi_conf, self).__init__(parent)
        uplayout = QFormLayout()

        self.set_work_dir_button = QPushButton()
        uplayout.addRow("Working Directory", self.set_work_dir_button)
        self.Id_widget = QLineEdit()
        uplayout.addRow("Reconstruction ID", self.Id_widget)

        vbox = QVBoxLayout()
        vbox.addLayout(uplayout)

        self.t = cdi_conf_tab(self)
        vbox.addWidget(self.t)

        self.setLayout(vbox)
        self.setWindowTitle("CDI Configuration")

        self.Id_widget.textChanged.connect(self.set_id)
        self.set_work_dir_button.clicked.connect(self.set_working_dir)


    def set_id(self):
        self.id = str(self.Id_widget.text())


    def set_working_dir(self):
        self.working_dir = select_dir('/local/bfrosik/cdi')
        self.set_work_dir_button.setStyleSheet("Text-align:left")
        self.set_work_dir_button.setText(self.working_dir)


class cdi_conf_tab(QTabWidget):
    def __init__(self, main_win, parent=None):
        super(cdi_conf_tab, self).__init__(parent)
        self.main_win = main_win
        self.tab1 = QWidget()
        self.prep_result_dir = self.id = self.detector = self.scan = self.data_dir = self.specfile = None
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
        # self.det_widget = QLineEdit()
        # layout.addRow("Detector", self.det_widget)
        self.data_dir_button = QPushButton()
        layout.addRow("data directory", self.data_dir_button)
        self.spec_file_button = QPushButton()
        layout.addRow("spec file", self.spec_file_button)
        self.scan_widget = QLineEdit()
        layout.addRow("scan(s)", self.scan_widget)
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
        self.config_data_button = QPushButton('create config_data', self)
        layout.addWidget(self.config_data_button)
        self.tab2.setLayout(layout)

        self.config_data_button.clicked.connect(self.config_data)


    def tab3UI(self):
        layout = QVBoxLayout()
        ulayout = QFormLayout()
        llayout = QHBoxLayout()
        self.save_dir = QLineEdit()
        ulayout.addRow("save results dir", self.save_dir)
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
        self.features = features(self, llayout)
        self.config_rec_button = QPushButton('create config_rec', self)
        layout.addWidget(self.config_rec_button)
        self.tab3.setAutoFillBackground(True)
        self.tab3.setLayout(layout)

        self.config_rec_button.clicked.connect(self.config_rec)
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
        self.save_disp_dir = QLineEdit()
        layout.addRow("save display dir", self.save_disp_dir)
        self.config_disp_button = QPushButton('update config_disp', self)
        layout.addWidget(self.config_disp_button)
        self.tab4.setLayout(layout)

        self.config_disp_button.clicked.connect(self.config_disp)


    def set_spec_file(self):
        self.specfile = select_file('/net/s34data/export/34idc-data/2018')
        self.spec_file_button.setStyleSheet("Text-align:left")
        self.spec_file_button.setText(self.specfile)


    def set_dark_file(self):
        self.darkfile = select_file('/net/s34data/export/34idc-work/2018')
        self.dark_file_button.setStyleSheet("Text-align:left")
        self.dark_file_button.setText(self.darkfile)


    def set_white_file(self):
        self.whitefile = select_file('/net/s34data/export/34idc-work/2018')
        self.white_file_button.setStyleSheet("Text-align:left")
        self.white_file_button.setText(self.whitefile)


    def set_data_dir(self):
        self.data_dir = select_dir('/net/s34data/export/34idc-data/2018')
        self.data_dir_button.setStyleSheet("Text-align:left")
        self.data_dir_button.setText(self.data_dir)


    def prepare(self):
        scan = str(self.scan_widget.text())
        if  self.main_win.working_dir is not None and \
            self.main_win.id is not None and\
            scan is not None and \
            self.data_dir is not None and \
            self.specfile is not None:
            try:
                # after checking that scan is entered convert it to list of int
                scan_range = scan.split('-')
                for i in range(len(scan_range)):
                    scan_range[i] = int(scan_range[i])
            except:
                print ('enter numeric values for scan range')
        else:
            print ('enter all fields')
        prep.prepare(self.main_win.working_dir, self.main_win.id, scan_range, self.data_dir, self.specfile, self.darkfile, self.whitefile)


    def config_data(self):
        conf_map = {}
        data_out_dir = '"' + self.main_win.working_dir + '/' + self.main_win.id + '/data' + '"'
        conf_map['data_dir'] = data_out_dir
        if len(self.aliens.text()) > 0:
            conf_map['aliens'] = str(self.aliens.text())
        else:
            print ("aliens not defined")
        if len(self.amp_threshold.text()) > 0:
            conf_map['amp_threshold'] = str(self.amp_threshold.text())
        else:
            print ('amplitude threshold not defined. Quiting operation.')
            return
        if len(self.binning.text()) > 0:
            conf_map['binning'] = str(self.binning.text())
        else:
            print ("binning not defined")
        if len(self.center_shift.text()) > 0:
            conf_map['center_shift'] = str(self.center_shift.text())
        else:
            print ("center shift not defined")
        if len(self.adjust_dimensions.text()) > 0:
            conf_map['adjust_dimensions'] = str(self.adjust_dimensions.text())
        else:
            print ("adjust dimensions not defined")

        self.create_config('config_data', conf_map)


    def config_rec(self):
        conf_map = {}
        conf_map['data_dir'] = '"' + self.main_win.working_dir + '/' + self.main_win.id + '/data' + '"'
        conf_map['save_dir'] = str(self.save_dir.text())
        conf_map['threads'] = str(self.threads.text())
        conf_map['device'] = str(self.device.text())
        conf_map['garbage_trigger'] = str(self.gc.text())
        conf_map['algorithm_sequence'] = str(self.alg_seq.text())
        conf_map['beta'] = str(self.beta.text())
        if self.cont.isChecked():
            conf_map['continue_dir'] = str(self.cont_dir.text())

        if self.features.active_0.isChecked():
            conf_map['generations'] = str(self.features.generations.text())
            conf_map['low_resolution_generations'] = str(self.features.lr_generations.text())
            conf_map['low_resolution_sigma_alg'] = str(self.features.lr_sigma_alg.text())
            conf_map['low_resolution_sigmas'] = str(self.features.lr_sigmas.text())
            conf_map['low_resolution_sigma_min'] = str(self.features.lr_sigma_min.text())
            conf_map['low_resolution_sigma_max'] = str(self.features.lr_sigma_max.text())
            conf_map['low_resolution_scale_power'] = str(self.features.lr_scale_power.text())
            conf_map['low_resolution_alg'] = str(self.features.lr_algorithm.text())
        if self.features.active_1.isChecked():
            conf_map['resolution_trigger'] = str(self.features.res_triggers.text())
            conf_map['iter_res_sigma_range'] = str(self.features.sigma_range.text())
            conf_map['iter_res_det_range'] = str(self.features.det_range.text())
        if self.features.active_2.isChecked():
            conf_map['amp_support_trigger'] = str(self.features.support_triggers.text())
            conf_map['support_type'] = str(self.features.support_type.text())
            conf_map['support_threshold'] = str(self.features.threshold.text())
            conf_map['support_sigma'] = str(self.features.sigma.text())
            conf_map['support_area'] = str(self.features.support_area.text())
        if self.features.active_3.isChecked():
            conf_map['phase_support_trigger'] = str(self.features.phase_triggers.text())
            conf_map['phase_min'] = str(self.features.phase_min.text())
            conf_map['phase_max'] = str(self.features.phase_max.text())
        if self.features.active_4.isChecked():
            conf_map['pcdi_trigger'] = str(self.features.pcdi_triggers.text())
            conf_map['partial_coherence_type'] = str(self.features.pcdi_type.text())
            conf_map['partial_coherence_iteration_num'] = str(self.features.pcdi_iter.text())
            conf_map['partial_coherence_normalize'] = str(self.features.pcdi_normalize.text())
            conf_map['partial_coherence_roi'] = str(self.features.pcdi_roi.text())
        if self.features.active_5.isChecked():
            conf_map['twin_trigger'] = str(self.features.twin_triggers.text())
        if self.features.active_6.isChecked():
            conf_map['avarage_trigger'] = str(self.features.average_triggers.text())

        self.create_config('config_rec', conf_map)


    def create_config(self, conf_file, conf_map):
        valid = True
        working_dir = os.path.join(self.main_win.working_dir, self.main_win.id)
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
        conf_dir = os.path.join(working_dir, 'conf')
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        conf_file = os.path.join(conf_dir, conf_file)
        temp_file = os.path.join(self.main_win.working_dir, self.main_win.id, 'conf', 'temp')
        with open(temp_file, 'a') as f:
            for key in conf_map:
                value = conf_map[key]
                if len(value) == 0:
                    print ('the ' + key + ' is not configured')
                    valid = False
                    break
                f.write(key + ' = ' + conf_map[key] + '\n')
        f.close()
        if valid:
            shutil.move(temp_file, conf_file)


    def config_disp(self):
        if len(self.crop.text()) == 0:
            print ('crop not configured')
            #return

        working_dir = os.path.join(self.main_win.working_dir, self.main_win.id)
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)
        conf_dir = os.path.join(working_dir, 'conf')

        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        disp_conf_file = os.path.join(self.main_win.working_dir, self.main_win.id, 'conf', 'config_disp')
        temp_file = os.path.join(self.main_win.working_dir, self.main_win.id, 'conf', 'temp')
        with open(temp_file, 'a') as temp:
            try:
                with open(disp_conf_file, 'r') as f:
                    for line in f:
                        if not line.startswith('crop')and not line.startswith('save_dir'):
                            temp.write(line)
                f.close()
            except:
                pass

            if len(self.crop.text()) != 0:
                temp.write('crop = ' + str(self.crop.text()) + '\n')
            if len(self.save_disp_dir.text()) == 0:
                temp.write('save_dir = ' + working_dir + '/results\n')
            else:
                temp.write('save_dir = ' + str(self.save_disp_dir.text()) + '\n')
        temp.close()
        shutil.move(temp_file, disp_conf_file)


    def rec_default(self):
        if  self.main_win.working_dir is None or self.main_win.id is None or \
            len(self.main_win.working_dir) == 0 or len(self.main_win.id) == 0:
                print ('Working Directory or Reconstruction ID not configured')
        else:
            self.save_dir.setText('"' + str(self.main_win.working_dir) + '/' + str(self.main_win.id) + '/results' + '"')
            self.threads.setText('1')
            self.device.setText('(3)')
            self.gc.setText('(1000)')
            self.alg_seq.setText('((5,("ER",20),("HIO",180)),(1,("ER",40),("HIO",160)),(4,("ER",20),("HIO",180)))')
            self.beta.setText('.9')
            self.cont.setChecked(False)


class features(QWidget):
    def __init__(self, tab, layout):
        super(features, self).__init__()
        self.leftlist = QListWidget()
        self.leftlist.insertItem(0, 'GA')
        self.leftlist.insertItem(1, 'low resolution')
        self.leftlist.insertItem(2, 'amplitude support')
        self.leftlist.insertItem(3, 'phase support')
        self.leftlist.insertItem(4, 'pcdi')
        self.leftlist.insertItem(5, 'twin')
        self.leftlist.insertItem(6, 'average')

        item = self.leftlist.item(2)
        item.setForeground(QColor('black'));

        self.stack0 = QWidget()
        self.stack1 = QWidget()
        self.stack2 = QWidget()
        self.stack3 = QWidget()
        self.stack4 = QWidget()
        self.stack5 = QWidget()
        self.stack6 = QWidget()

        self.stack0UI(self.leftlist.item(0))
        self.stack1UI(self.leftlist.item(1))
        self.stack2UI(self.leftlist.item(2))
        self.stack3UI(self.leftlist.item(3))
        self.stack4UI(self.leftlist.item(4))
        self.stack5UI(self.leftlist.item(5))
        self.stack6UI(self.leftlist.item(6))

        self.Stack = QStackedWidget(self)
        self.Stack.addWidget(self.stack0)
        self.Stack.addWidget(self.stack1)
        self.Stack.addWidget(self.stack2)
        self.Stack.addWidget(self.stack3)
        self.Stack.addWidget(self.stack4)
        self.Stack.addWidget(self.stack5)
        self.Stack.addWidget(self.stack6)

        layout.addWidget(self.leftlist)
        layout.addWidget(self.Stack)

        self.leftlist.currentRowChanged.connect(self.display)


    def stack0UI(self, item):
        layout = QFormLayout()
        self.active_0 = QCheckBox("active")
        self.active_0.setChecked(False)
        layout.addWidget(self.active_0)
        self.toggle_0(layout, item)
        self.stack0.setLayout(layout)
        self.active_0.stateChanged.connect(lambda: self.toggle_0(layout, item))

    def toggle_0(self, layout, item):
        if self.active_0.isChecked():
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
            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));


    def stack1UI(self, item):
        layout = QFormLayout()
        self.active_1 = QCheckBox("active")
        self.active_1.setChecked(True)
        layout.addWidget(self.active_1)
        self.toggle_1(layout, item)
        self.stack1.setLayout(layout)
        self.active_1.stateChanged.connect(lambda:self.toggle_1(layout, item))


    def toggle_1(self, layout, item):
        if self.active_1.isChecked():
            self.res_triggers = QLineEdit()
            layout.addRow("low resolution triggers", self.res_triggers)
            self.sigma_range = QLineEdit()
            layout.addRow("sigma range", self.sigma_range)
            self.det_range = QLineEdit()
            layout.addRow("det range", self.det_range)

            self.default_1_button = QPushButton('set to defaults', self)
            layout.addWidget(self.default_1_button)
            self.default_1_button.clicked.connect(self.rec_1_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));


    def stack2UI(self, item):
        layout = QFormLayout()
        self.active_2 = QCheckBox("active")
        self.active_2.setChecked(True)
        layout.addWidget(self.active_2)
        self.toggle_2(layout, item)
        self.stack2.setLayout(layout)
        self.active_2.stateChanged.connect(lambda: self.toggle_2(layout, item))


    def toggle_2(self, layout, item):
        if self.active_2.isChecked():
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

            self.default_2_button = QPushButton('set to defaults', self)
            layout.addWidget(self.default_2_button)
            self.default_2_button.clicked.connect(self.rec_2_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));


    def stack3UI(self, item):
        layout = QFormLayout()
        self.active_3 = QCheckBox("active")
        self.active_3.setChecked(True)
        layout.addWidget(self.active_3)
        self.toggle_3(layout, item)
        self.stack3.setLayout(layout)
        self.active_3.stateChanged.connect(lambda: self.toggle_3(layout, item))

    def toggle_3(self, layout, item):
        if self.active_3.isChecked():
            self.phase_triggers = QLineEdit()
            layout.addRow("phase support triggers", self.phase_triggers)
            self.phase_min = QLineEdit()
            layout.addRow("phase minimum", self.phase_min)
            self.phase_max = QLineEdit()
            layout.addRow("phase maximum", self.phase_max)

            self.default_3_button = QPushButton('set to defaults', self)
            layout.addWidget(self.default_3_button)
            self.default_3_button.clicked.connect(self.rec_3_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));


    def stack4UI(self, item):
        layout = QFormLayout()
        self.active_4 = QCheckBox("active")
        self.active_4.setChecked(True)
        layout.addWidget(self.active_4)
        self.toggle_4(layout, item)
        self.stack4.setLayout(layout)
        self.active_4.stateChanged.connect(lambda: self.toggle_4(layout, item))

    def toggle_4(self, layout, item):
        if self.active_4.isChecked():
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

            self.default_4_button = QPushButton('set to defaults', self)
            layout.addWidget(self.default_4_button)
            self.default_4_button.clicked.connect(self.rec_4_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));

    def stack5UI(self, item):
        layout = QFormLayout()
        self.active_5 = QCheckBox("active")
        self.active_5.setChecked(True)
        layout.addWidget(self.active_5)
        self.toggle_5(layout, item)
        self.stack5.setLayout(layout)
        self.active_5.stateChanged.connect(lambda: self.toggle_5(layout, item))

    def toggle_5(self, layout, item):
        if self.active_5.isChecked():
            self.twin_triggers = QLineEdit()
            layout.addRow("twin triggers", self.twin_triggers)

            self.default_5_button = QPushButton('set to defaults', self)
            layout.addWidget(self.default_5_button)
            self.default_5_button.clicked.connect(self.rec_5_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));


    def stack6UI(self, item):
        layout = QFormLayout()
        self.active_6 = QCheckBox("active")
        self.active_6.setChecked(True)
        layout.addWidget(self.active_6)
        self.toggle_6(layout, item)
        self.stack6.setLayout(layout)
        self.active_6.stateChanged.connect(lambda: self.toggle_6(layout, item))

    def toggle_6(self, layout, item):
        if self.active_6.isChecked():
            self.average_triggers = QLineEdit()
            layout.addRow("average triggers", self.average_triggers)

            self.default_6_button = QPushButton('set to defaults', self)
            layout.addWidget(self.default_6_button)
            self.default_6_button.clicked.connect(self.rec_6_default)

            item.setForeground(QColor('black'));
        else:
            for i in reversed(range(1, layout.count())):
                layout.itemAt(i).widget().setParent(None)
            item.setForeground(QColor('grey'));

    def display(self, i):
        self.Stack.setCurrentIndex(i)


    def rec_1_default(self):
        #TODO add to accept fractions in trigger, so the default will be (.5,1)
        self.res_triggers.setText('(0, 1, 500)')
        self.sigma_range.setText('(2.0)')
        self.det_range.setText('(.7)')


    def rec_2_default(self):
        self.support_triggers.setText('(1,1)')
        self.support_type.setText('"GAUSS"')
        self.support_area.setText('[.5,.5,.5]')
        self.sigma.setText('1.0')
        self.threshold.setText('0.1')


    def rec_3_default(self):
        self.phase_triggers.setText('(0,1,20)')
        self.phase_min.setText('-1.57')
        self.phase_max.setText('1.57')


    def rec_4_default(self):
        self.pcdi_triggers.setText('(50,50)')
        self.pcdi_type.setText('"LUCY"')
        self.pcdi_iter.setText('20')
        self.pcdi_normalize.setText('true')
        self.pcdi_roi.setText('[32,32,16]')


    def rec_5_default(self):
        self.twin_triggers.setText('(2)')


    def rec_6_default(self):
        self.average_triggers.setText('(-400,1)')


def main():
    app = QApplication(sys.argv)
    ex = cdi_conf()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()