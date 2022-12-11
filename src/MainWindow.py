#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import subprocess

from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
import rosbag

from FileWindow import FileWindow


class MainWindow(QMainWindow):
    def __init__(self, title="Select", msg="",app=None):
        super().__init__()

        self.msg = msg
        self._app = app

        self._files = []
        self._topic_list = []
        self._checkboxs=[]

        self.convert_btn=QPushButton("Convert")
        self.convert_btn.clicked.connect(self.on_convert)

        self.all_check_btn=QPushButton("All Check")
        self.all_check_btn.clicked.connect(self.on_all_check)

        self.all_uncheck_btn=QPushButton("All Uncheck")
        self.all_uncheck_btn.clicked.connect(self.on_all_uncheck)

        # when start up, user select file
        self.set_rosbag_topic()

        # window size and init position setting
        self.setGeometry(300, 300, 900, 600)

        # create menu
        self.create_menu_bar()

        self.setWindowTitle(title)
        self.show()
        
    def on_convert(self):
        """filter selecting topic
        """
        keeping_topics = {}
        select_topic_count = False

        for (checkbox, select) in zip(self._checkboxs, self._topic_list):
            keeping_topics[select]=checkbox.isChecked()
            if checkbox.isChecked():
                select_topic_count = True

        if select_topic_count is False:
            # not check topic
            QtWidgets.QMessageBox.critical(self, "Error", "Please select at least one topic")
            return

        # Construct commandline
        output_path = FileWindow.save_file(isApp=True, caption="Convert bag file", filefilter="*.bag")
        if output_path[0] == "":
            return
        
        output_path = output_path[0]
        if output_path.endswith('.bag') is False:
            output_path += '.bag'

        cmd=f'rosbag filter {self._files[0]} {output_path} "'
        for k,v in keeping_topics.items():
            if v:
                cmd+="topic=='"
                cmd+=k
                cmd+="' or "
        cmd=cmd[:-3]
        cmd+='"'

        print("Converting....")
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = p.communicate()
        QtWidgets.QMessageBox.information(self, "Message", "Finish Convert!!")

    def on_all_check(self):
        for checkbox in self._checkboxs:
            checkbox.setChecked(True)

    def on_all_uncheck(self):
        for checkbox in self._checkboxs:
            checkbox.setChecked(False)

    def create_menu_bar(self):
        """create menu bar
        """
        
        load_action = self._create_menu('&Load rosbag', self.set_rosbag_topic, 'Ctrl+O', 'Load rosbag file')
        save_config_action = self._create_menu("&Save config", self.save_config, 'Ctrl+S', 'Save checkbox config')
        load_config_action = self._create_menu("&Load config", self.load_config, 'Ctrl+A', 'Load checkbox config')
        convert_action = self._create_menu('&Convert', self.on_convert, None, 'Convert rosbag')
        exit_action = self._create_menu('&Exit', self.quit, 'Ctrl+Q', 'Exit application')
        menubar = self.menuBar()

        file_menu = menubar.addMenu('&File')
        file_menu.addAction(load_action)
        file_menu.addAction(convert_action)
        file_menu.addAction(exit_action)

        config_menu = menubar.addMenu('&Config')
        config_menu.addAction(save_config_action)
        config_menu.addAction(load_config_action)

    def set_rosbag_topic(self):
        """load rosbag and set rosbag topic information on window
        """
        # save prev config
        prev_check_topic = []
        for (checkbox, select) in zip(self._checkboxs, self._topic_list):
            if checkbox.isChecked():
                prev_check_topic.append(select)

        # load file
        file_paths = FileWindow.get_file_path(isApp=True,caption="Select bag file",filefilter="*bag")
        if file_paths[0] == "":
            return

        self._files = file_paths
        topic_list = self._get_topicList(self._files[0])
        if len(topic_list) < 1:
            print("Please select a bag file")
            QtWidgets.QMessageBox.critical(self, "Error", "Please select a bag file")
            return

        # set ui component
        self._topic_list = topic_list
        self._checkboxs.clear()
        scroll_area = QScrollArea()
        inner = QWidget()
        box_layout = QVBoxLayout()
        
        # label
        msg_label = QLabel(self.msg)
        file_path_label = QLabel(f'rosbag path:{self._files[0]}')
        file_path_label.setToolTip(self._files[0])

        # set btn layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.all_check_btn)
        btn_layout.addWidget(self.all_uncheck_btn)
        btn_layout.addWidget(self.convert_btn)
        
        # set grid layout
        grid_layout = QGridLayout()
        layoutIndex=0
        for select in self._topic_list:
            checkbox=QCheckBox(select)
            if select in prev_check_topic:
                checkbox.setChecked(True)
            grid_layout.addWidget(checkbox,layoutIndex,0)
            layoutIndex=layoutIndex+1
            self._checkboxs.append(checkbox)

        box_layout.addWidget(msg_label)
        box_layout.addWidget(file_path_label)
        box_layout.addLayout(btn_layout)
        box_layout.addLayout(grid_layout)

        inner.setLayout(box_layout)
        scroll_area.setWidget(inner)
        self.setCentralWidget(scroll_area)

    def save_config(self):
        """save checkbox config
        """
        output_path = FileWindow.save_file(isApp=True, caption='Save config file', filefilter='')
        if output_path[0] == "":
            return

        with open(output_path[0], 'w') as f:
            for (checkbox, select) in zip(self._checkboxs, self._topic_list):
                if checkbox.isChecked():
                    f.write(f'{select}\n')

    def load_config(self):
        """load checkbox config
        """
        file_paths = FileWindow.get_file_path(isApp=True,caption='Select config file',filefilter='')
        if file_paths[0] == "":
            return

        checked_list = []
        with open(file_paths[0], 'r') as f:
            checked_list = f.readlines()

        if len(checked_list) == 0:
            return

        checked_list = [i.rstrip('\n') for i in checked_list]
        for (checkbox, select) in zip(self._checkboxs, self._topic_list):
            if  select in checked_list:
                checkbox.setChecked(True)
        

    def _get_topicList(self, path):
        bag = rosbag.Bag(path)
        topics = bag.get_type_and_topic_info()[1].keys()

        return topics

    def _create_menu(self, name, connect, short_cut=None, tooltip=None):
        action = QAction(name, self)
        action.triggered.connect(connect)

        if short_cut is not None:
            action.setShortcut(short_cut) 

        if tooltip is not None:
            action.setStatusTip(tooltip)

        return action

    def quit(self):
        self._app.quit()


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window=MainWindow(app=app,msg="Select topics which you want to keep", title="rosbag filter")
    app.exec_()


if __name__ == '__main__':
    print("rosbag_filter_gui start!!")
    main()
    print("rosbag_filter_gui end!!")
