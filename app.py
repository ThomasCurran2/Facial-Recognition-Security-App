import re
import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)


class SignUpWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Create account")
        self.setGeometry(100, 100, 500, 550)  # (x, y, width, height)

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

        login_button = QPushButton("Sign Up")
        login_button.clicked.connect(self.login)

        form_layout.addRow(username_label, self.username_field)
        form_layout.addRow(password_label, self.password_field)
        form_layout.addRow(login_button)

        central_widget.setLayout(form_layout)

    def login(self):
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
            QMessageBox.information(
                self, "Login Successful", "Welcome, " + username + "!"
            )


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        button = QPushButton("Press Me!")

        self.setFixedSize(QSize(400, 300))

        self.setCentralWidget(button)


app = QApplication(sys.argv)

window = SignUpWindow()
window.show()

app.exec()
