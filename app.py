import base64
import json
import numpy as np
import os
import re
import sys

from PyQt5.QtCore import QSize, Qt, pyqtSlot as Slot, Qt, QThread
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QVBoxLayout,
)
from face_id.face_verification import FaceVerifier, VideoThread


class SignUpWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Create account")
        self.setGeometry(100, 100, 500, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        form_layout = QFormLayout()

        # heading_label = QLabel("Create account", self)
        # heading_label.setGeometry(0, 0, 50, 50)
        # heading_label.setAlignment(Qt.AlignTop)

        username_label = QLabel("Username:")
        self.username_field = QLineEdit()

        password_label = QLabel("Password:")
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)

        confirm_button = QPushButton("Sign Up")
        confirm_button.clicked.connect(self.sign_up)

        form_layout.addRow(username_label, self.username_field)
        form_layout.addRow(password_label, self.password_field)
        form_layout.addRow(confirm_button)

        central_widget.setLayout(form_layout)

    def sign_up(self):
        username = self.username_field.text()
        password = self.password_field.text()

        # username is at least 12 chars long, can't have spaces, and can't have any special characters
        if (
            len(username) < 12
            or bool(re.search(r"\s", username)) == True
            or username.isalnum() == False
        ):
            QMessageBox.warning(self, "Account creation failed", "Invalid username!")

        # password is at least 12 chars long, can't have spaces, and has to have at least 1 number, capital and special character
        elif (
            len(password) < 12
            or bool(re.search(r"\s", password)) == True
            or bool(re.search(r"\d", password)) == False
            or bool(re.search(r"[A-Z]", password)) == False
            or password.isalnum() == True
        ):
            QMessageBox.warning(self, "Account creation failed", "Invalid password!")

        else:
            encpwd = base64.b64encode(password.encode("utf-8"))
            encpwd = encpwd.decode()
            dict = {username: encpwd}

            with open("data.json", "w", encoding="utf-8") as jsonfile:
                json.dump(dict, jsonfile, ensure_ascii=False)

            self.second_window = LoginWindow()
            self.second_window.show()
            self.close()


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 500, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        form_layout = QFormLayout()

        username_label = QLabel("Username:")
        self.username_field = QLineEdit()

        password_label = QLabel("Password:")
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)

        confirm_button = QPushButton("Login")
        confirm_button.clicked.connect(self.login)

        # Added for testing
        skip_button = QPushButton("Skip login")
        skip_button.clicked.connect(self.skip)

        form_layout.addRow(username_label, self.username_field)
        form_layout.addRow(password_label, self.password_field)
        form_layout.addRow(confirm_button)
        form_layout.addRow(skip_button)

        central_widget.setLayout(form_layout)

    def login(self):
        username = self.username_field.text()
        password = self.password_field.text()

        with open("data.json", "r") as openfile:
            saved_data = json.load(openfile)

        saved_username, saved_pwd = next(iter(saved_data.items()))

        encpwd = base64.b64encode(password.encode("utf-8"))
        encpwd = encpwd.decode()

        if username != saved_username or encpwd != saved_pwd:
            QMessageBox.warning(self, "Login failed", "Invalid username or password!")

        else:
            self.second_window = MainWindow()
            self.second_window.show()
            self.close()

    def skip(self):
        self.second_window = MainWindow()
        self.second_window.show()
        self.close()


class VerifyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Verification")
        self.setGeometry(100, 100, 500, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.image_label = QLabel(self)

        self.textLabel = QLabel("Awaiting verification")

        verify_button = QPushButton("Verify")
        self.verify_obj = FaceVerifier()
        self.current_image = np.ndarray((250, 250, 3))
        verify_button.clicked.connect(
            lambda: self.verify_obj.verify(self.current_image, self.textLabel)
        )

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label, alignment=Qt.AlignCenter)
        vbox.addWidget(self.textLabel, alignment=Qt.AlignCenter)
        vbox.addWidget(verify_button)
        central_widget.setLayout(vbox)

        self.thread = VideoThread()
        self.thread.image_signal.connect(self.save_cv_image)
        self.thread.pixmap_signal.connect(self.update_image)
        self.thread.start()

    # different naming convention so the thread automatically runs this when closed
    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @Slot(np.ndarray)
    def save_cv_image(self, cv_image):
        self.current_image = cv_image

    @Slot(QPixmap)
    def update_image(self, pix_map):
        self.image_label.setPixmap(pix_map)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setGeometry(100, 100, 500, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        form_layout = QFormLayout()

        verify_button = QPushButton("Test verification")
        verify_button.clicked.connect(self.open_verify_window)

        form_layout.addRow(verify_button)

        central_widget.setLayout(form_layout)

    def open_verify_window(self):
        self.second_window = VerifyWindow()
        self.second_window.show()
        self.close()


app = QApplication(sys.argv)

data_path = "data.json"

if not os.path.exists(data_path):
    with open(data_path, "w") as fp:
        pass
    window = SignUpWindow()

elif os.stat(data_path).st_size == 0:
    window = SignUpWindow()

else:
    window = LoginWindow()

window.show()

app.exec()
