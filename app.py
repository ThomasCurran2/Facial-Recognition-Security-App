import base64
import json
import numpy as np
import os
import re
import sys

from threading import Timer
from PyQt5.QtCore import Qt, pyqtSignal as Signal, pyqtSlot as Slot, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QMessageBox,
    QVBoxLayout,
    QFileDialog,
)
from face_id.face_verification import (
    FaceVerifier,
    IDUpdater,
    VideoThread,
    MonitorThread,
)


class SignUpWindow(QMainWindow):
    """
    Creates a pyqt5 window for signing up, where the user can create/save their credentials.

    Creates widgets for a username and password form that the user can input text into and
    save into a json file to be used for signing in. This class is called when there is no
    "credentials.json" in the main directory and if the json file is empty.
    """

    def __init__(self):
        """Initalizes sign up window and creates widgets."""

        super().__init__()

        self.setWindowTitle("Create account")
        self.setFixedSize(700, 170)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        form_layout = QFormLayout()

        username_label = QLabel("Username:")
        self.username_field = QLineEdit()

        password_label = QLabel("Password:")
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)

        username_rules_label = QLabel(
            "*Usernames must be at least 12 characters long, and contain no spaces or special characters"
        )

        password_rules_label = QLabel(
            "*Passwords must be at least 12 characters long, contain no spaces, and have at least 1 number and special character"
        )

        confirm_button = QPushButton("Sign Up")
        confirm_button.clicked.connect(self.sign_up)

        form_layout.addRow(username_label, self.username_field)
        form_layout.addRow(password_label, self.password_field)
        form_layout.addRow(username_rules_label)
        form_layout.addRow(password_rules_label)
        form_layout.addRow(confirm_button)

        central_widget.setLayout(form_layout)

    def sign_up(self):
        """Checks the username/password and saves it to a file.

        Takes the username and password inputted by the user and checks
        if they are formatted correctly. If the formatting is allowed then the
        password is encrypted and both it and the username are saved to a file.
        """

        username = self.username_field.text()
        password = self.password_field.text()

        if (
            len(username) < 12
            or bool(re.search(r"\s", username)) == True
            or username.isalnum() == False
        ):
            QMessageBox.warning(self, "Account creation failed", "Invalid username!")

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

            with open("credentials.json", "w", encoding="utf-8") as jsonfile:
                json.dump(dict, jsonfile, ensure_ascii=False)

            self.second_window = LoginWindow()
            self.second_window.show()
            self.close()


class LoginWindow(QMainWindow):
    """
    Creates a pyqt5 window for logging in, where the user can use their credentials to sign in.

    Creates widgets for a username and password form that the user can input their
    credentials into, which opens the main window if their username and
    password match what's saved to the "credentials.json" file. This class is called
    after the user saves their credentials on the sign up window or when the app is
    run if they already have a saved username and password.
    """

    def __init__(self):
        """Initializes the login window and creates its widgets"""

        super().__init__()

        self.setWindowTitle("Login")
        self.setFixedSize(500, 125)

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

        form_layout.addRow(username_label, self.username_field)
        form_layout.addRow(password_label, self.password_field)
        form_layout.addRow(confirm_button)

        central_widget.setLayout(form_layout)

    def login(self):
        """Checks if the inputted information match saved credentials.

        Loads a file containing the user's saved credentials and checks
        if the inputted username and password match what was saved. If
        they do match then the update id window is opened if the user has no
        face id images saved, or the main window is opened if they do have
        id images.
        """

        username = self.username_field.text()
        password = self.password_field.text()

        with open("credentials.json", "r") as openfile:
            saved_data = json.load(openfile)

        saved_username, saved_pwd = next(iter(saved_data.items()))

        encpwd = base64.b64encode(password.encode("utf-8"))
        encpwd = encpwd.decode()

        if username != saved_username or encpwd != saved_pwd:
            QMessageBox.warning(self, "Login failed", "Invalid username or password!")

        elif not os.path.exists("face_id/image_data"):
            os.makedirs("face_id/image_data")
            os.makedirs("face_id/image_data/input_image")
            os.makedirs("face_id/image_data/verification_images")

            self.second_window = UpdateIDWindow()
            self.second_window.show()
            self.close()

        elif len(os.listdir("face_id/image_data/verification_images")) == 0:
            self.second_window = UpdateIDWindow()
            self.second_window.show()
            self.close()

        else:
            self.second_window = MainWindow()
            self.second_window.show()
            self.close()


class VerifyWindow(QMainWindow):
    """
    Creates a pyqt5 window for face verification, with a video thread displaying a webcam image.

    Creates widgets to display the user's webcam and if the verification failed. Also creates a video
    thread, face verification object, and monitor window object to display/capture the webcam image,
    send those images to be tested with a siamese neural network, and send information to the monitor window
    if the image was verified. Both classes used for the video thread and face verification can be found
    at "face_id/face_verification".

    Attributes:
        pause_status (pyqtSignal): signal used emit a bool that determines if the video thread needs to stop
        verified_status (pyqtSignal): signal used to emit strings of the verified app's name and path
    """

    pause_status = Signal(bool)
    verified_status = Signal(str, str)

    def __init__(self):
        """Initializes the verify window and creates its widgets and video thread."""

        super().__init__()

        self.setWindowTitle("Verification")
        self.setFixedSize(500, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.monitor_window = MonitorWindow(False)

        self.image_label = QLabel(self)

        self.text_label = QLabel("Awaiting verification")

        verify_button = QPushButton("Verify")
        self.face_verifier = FaceVerifier()
        self.current_image = np.ndarray((250, 250, 3))
        verify_button.clicked.connect(self.call_verification)
        self.face_verifier.verified_signal.connect(self.close_window)

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label, alignment=Qt.AlignCenter)
        vbox.addWidget(self.text_label, alignment=Qt.AlignCenter)
        vbox.addWidget(verify_button)
        central_widget.setLayout(vbox)

        self.thread = VideoThread()
        self.thread.image_signal.connect(self.save_cv_image)
        self.thread.pixmap_signal.connect(self.update_image)
        self.thread.start()

    def closeEvent(self, event):
        """Modifies variables and threads when the window closes.

        When the verify window closes this function is ran, which emits strings
        used in the monitor window and stops the video thread. Naming conventions
        are different for this method so it can automatically be called when the
        window closes.

        Args:
            event (QCloseEvent): event that is created when the window is closed.
        """

        self.verified_status.emit("", "")
        self.thread.stop()
        event.accept()

    def call_verification(self):
        """Calls methods for face verification and stops the video thread.

        This function stops the video thread to prevent it from using reasources,
        emits a variable to the monitor thread window to pause the monitor thread,
        and calls the verify method while passing in the current webcam image and
        text label that shows if the verification failed.
        """

        self.thread.stop()
        self.pause_status.emit(True)
        self.face_verifier.verify(self.current_image, self.text_label)

    def save_app_data(self, name, path):
        """Saves app information to be used in the monitor window.

        Saves the app name and file path for the monitor window to
        use if the user is verified to use the app this verify window is
        open for.

        Args:
            name (str): name of an app
            path (str): file path of an app
        """

        self.saved_name = name
        self.saved_path = path

    @Slot(bool)
    def close_window(self, result):
        """Closes the window and updates values when the user is verified.

        If the verify method emits true this method emits data to re-create
        the monitor thread and update one of it's variables so that it
        doesn't monitor the app that the user was just verified for.

        Args:
            result (bool): Result of verification.
        """

        if result == True:
            self.pause_status.emit(False)
            self.verified_status.emit(self.saved_name, self.saved_path)
            self.close()

        else:
            self.pause_status.emit(False)
            self.thread = VideoThread()
            self.thread.image_signal.connect(self.save_cv_image)
            self.thread.pixmap_signal.connect(self.update_image)
            self.thread.start()

    @Slot(np.ndarray)
    def save_cv_image(self, cv_image):
        """Saves a opencv image to a variable.

        Saves the current webcam image to a variable that is used
        in the verify function as the input image.

        Args:
            cv_image (ndarray): Current OpenCV image of the user's webcam.
        """

        self.current_image = cv_image

    @Slot(QPixmap)
    def update_image(self, pix_map):
        """Updates the pixmap to display the user's webcam.

        Constantly updates the image label with a new pixmap to
        display the webcam image.

        Args:
            pix_map (QPixmap): Pixmap image of the user's webcam.
        """

        self.image_label.setPixmap(pix_map)


class UpdateIDWindow(QMainWindow):
    """
    Creates a pyqt5 window that captures and adds face id images to a folder used for verification.

    Creates widgets to display the user's webcam and to start/confirm if the user wants to take
    new id images. Class objects are used to create a video thread to display the user's webcam
    and add/replace the old id images with the user's new ones.The class used to update the face
    id images can be found at "face_id/face_verification" with the name "IDUpdater".

    """

    def __init__(self):
        """Initializes the update id window and it widgets."""
        super().__init__()

        self.setWindowTitle("ID images")
        self.setFixedSize(500, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.image_delay = 0

        self.image_label = QLabel(self)

        self.text_label = QLabel(
            "Please center your face in the image above before starting."
        )

        self.count_label = QLabel()

        update_button = QPushButton("Update ID images")
        self.id_updater = IDUpdater()
        self.image_array = []
        self.array_idx = 0
        update_button.clicked.connect(self.confirm_update)

        back_button = QPushButton("Go to main window")
        back_button.clicked.connect(self.open_main_window)

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label, alignment=Qt.AlignCenter)
        vbox.addWidget(self.text_label, alignment=Qt.AlignCenter)
        vbox.addWidget(self.count_label, alignment=Qt.AlignCenter)
        vbox.addWidget(update_button)
        vbox.addWidget(back_button)
        central_widget.setLayout(vbox)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.thread = VideoThread()
        self.thread.image_signal.connect(self.save_cv_array)
        self.thread.pixmap_signal.connect(self.update_image)
        self.thread.start()

    def closeEvent(self, event):
        """Modifies variables and threads when the window closes.

        When the update id window closes this function is ran, which stops the video thread.
        Naming conventions are different for this method so it can automatically be
        called when the window closes.

        Args:
            event (QCloseEvent): event that is created when the window is closed.
        """

        self.thread.stop()
        event.accept()

    def confirm_update(self):
        """Creates a warning message and calls update methods.

        If the user has face id images in the folder "face_id/image_data/verification_images"
        a warning message is created that calls methods to replace these images if the user
        selects "yes". If the user has no face id images then the methods are called without
        the warning message.
        """

        dir_path = os.path.join("face_id/image_data", "verification_images")
        self.seconds = 6

        if len(os.listdir(dir_path)) > 0:
            answer = QMessageBox.question(
                self,
                "Confirmation",
                "This will overwrite your current ID images. Are you sure you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if answer == QMessageBox.Yes:
                self.text_label.setText("Capturing pictures...")
                self.timer.start(1000)
                timer_thread = Timer(7, self.id_updater.update, args=[self.image_array])
                timer_thread.start()

        else:
            self.text_label.setText("Capturing pictures...")
            self.timer.start(1000)
            timer_thread = Timer(7, self.id_updater.update, args=[self.image_array])
            timer_thread.start()

    def update_timer(self):
        """Updates a timer that is displayed in the update id window.

        Changes a window label to display a countdown timer before any
        new face id images are saved.
        """

        self.seconds -= 1
        if self.seconds >= 0:
            self.count_label.setText(f"{self.seconds} seconds left")

        else:
            self.timer.stop()
            self.text_label.setText("Sucssesfully updated ID images!")
            self.count_label.setText("")

    def open_main_window(self):
        """Allows the user to return to the main window.

        Opens the main window and closes the update id window, but only
        if there are saved face id images.
        """

        dir_path = os.path.join("face_id/image_data", "verification_images")

        if len(os.listdir(dir_path)) == 0:
            QMessageBox.warning(
                self,
                "Warning",
                "No ID images found. You must save ID images before exiting!",
            )

        else:
            self.second_window = MainWindow()
            self.second_window.show()
            self.close()

    @Slot(np.ndarray)
    def save_cv_array(self, cv_image):
        """Saves an array of images to be saved as face id images.

        Constantly adds the current webcam image to an array, with it
        looping back to the beginning when the array is full. A delay was added so
        that the array has more varied images added to it.

        Args:
            cv_image (ndarray): Current OpenCV image of the user's webcam.
        """

        if self.image_delay < 2:
            self.image_delay = self.image_delay + 1

        elif self.image_delay == 2:
            if len(self.image_array) < 50:
                self.image_array.append(cv_image)

            else:
                if self.array_idx > 49:
                    self.array_idx = 0

                self.image_array[self.array_idx] = cv_image
                self.array_idx += 1

            self.image_delay = 0

    @Slot(QPixmap)
    def update_image(self, pix_map):
        """Updates the pixmap to display the user's webcam.

        Constantly updates the image label with a new pixmap to
        display the webcam image.

        Args:
            pix_map (QPixmap): Pixmap image of the user's webcam.
        """

        self.image_label.setPixmap(pix_map)


class ManagerWindow(QWidget):
    """
    Creates a pyqt5 window that browses apps to be added/removed from being protected by this app.

    Creates widgets to show the current list of protected apps and a button that allows the user
    to search through their files and select an app to add. Apps can also be removed from the
    list by pressing the "remove protection" button next to each app.

    """

    def __init__(self):
        """Initializes the manager window and its widgets"""
        super().__init__()

        self.setWindowTitle("Security manager")
        self.setFixedSize(500, 550)

        self.grid = QGridLayout()

        self.horizontal_grid_layout = QGridLayout()
        self.create_file_grid()

        self.vertical_layout = QVBoxLayout()

        browse_button = QPushButton("Search for a file to protect")
        browse_button.clicked.connect(self.browse_files)

        back_button = QPushButton("back")
        back_button.clicked.connect(self.open_main_window)

        self.vertical_layout.addWidget(browse_button)
        self.vertical_layout.addWidget(back_button)

        self.grid.addLayout(self.horizontal_grid_layout, 0, 0)
        self.grid.addLayout(self.vertical_layout, 1, 0)
        self.setLayout(self.grid)

    def browse_files(self):
        """Creates a file browser window.

        Opens a file browser window where user's can search for
        and select apps that they want to protect with this app.
        """

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        name = QFileDialog.getOpenFileName(
            self,
            "Select file",
            "",
            "Application Files (*.exe);;All Files (*)",
            options=options,
        )
        self.protected_name = os.path.basename(name[0])
        self.add_array_element(self.protected_name)

    def load_array(self):
        """Loads an array of apps that are protected."""

        with open("face_id/protected_data.json", "r") as open_file:
            self.protected_array = json.load(open_file)

    def save_array(self):
        """Saves a new array of protected apps to a file."""

        with open("face_id/protected_data.json", "w") as save_file:
            json.dump(self.protected_array, save_file)

    def add_array_element(self, file_name):
        """Adds a selected app to the protected apps array.

        If the selected app isn't the same as any other apps in the
        list, it is added to the list and methods are called to update the
        manager window.

        Args:
            file_name (str): Name of the selected app.
        """

        can_add = True
        for name in self.protected_array:
            if file_name == name:
                QMessageBox.warning(self, "Warning", "Application is already protected")
                can_add = False

        if file_name == "":
            can_add = False

        if can_add == True:
            print(len(self.protected_array))

            if len(self.protected_array) != 0:
                self.clear_file_grid()

            self.protected_array.append(file_name)
            self.save_array()
            self.create_file_grid()

    def remove_array_element(self, idx):
        """Removes an app from the protected apps array.

        Pops the selected app off the array and calls methods
        to update the manager window.

        Args:
            idx (int): Index of the app to be removed.
        """

        self.clear_file_grid()
        self.protected_array.pop(idx)
        self.save_array()
        self.create_file_grid()

    def clear_file_grid(self):
        """Removes all widgets in the grid displaying the protected apps.

        Loops through all rows and columbs of the grid layout used to
        display the protected apps and their "remove protection" buttons
        and removes all widgets.
        """

        for row in range(self.horizontal_grid_layout.rowCount()):
            for col in range(self.horizontal_grid_layout.columnCount()):
                item = self.horizontal_grid_layout.itemAtPosition(row, col)
                widget = item.widget()
                widget.deleteLater()

    def create_file_grid(self):
        """Adds widgets to a grid that displays the protected apps and their buttons.

        Creates labels and buttons for every element of the protected_array, and adds
        them to a grid that's displayed at the top of the manager window.
        """

        self.load_array()

        for idx in range(len(self.protected_array)):
            file_label = QLabel("" + self.protected_array[idx])

            file_button = QPushButton("Remove protection")
            file_button.clicked.connect(
                lambda checked, index=idx: self.remove_array_element(index)
            )

            self.horizontal_grid_layout.addWidget(file_label, idx, 0)
            self.horizontal_grid_layout.addWidget(file_button, idx, 1)

    def open_main_window(self):
        """Opens the main window and closes current window."""

        self.second_window = MainWindow()
        self.second_window.show()
        self.close()


class MonitorWindow(QMainWindow):
    """
    Creates a pyqt5 window that monitors if a protected app is open.

    Creates a window that monitors if any protected app is opened by using a
    thread that constantly looks if those apps are open. If a protected app is
    open it is closed and a verfiy window is created, which closes if the user's image is verified
    and re-opens the app. The thread used can be found in "face_id/face_verification" with the
    name "MonitorThread".


    """

    def __init__(self, create_thread):
        """Initializes the monitor window, its widgets and monitor thread.

        Creates the monitor window and starts the monitor thread if true is
        passed as an argument.

        Args:
            create_thread (bool): Value used to check if a monitor thread needs to be created or not.
        """

        super().__init__()

        self.setWindowTitle("Monitoring")
        self.setFixedSize(500, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.verifying = False

        self.app_name = ""

        self.monitor_thread = MonitorThread()

        self.text_label = QLabel("Monitoring files...")

        back_button = QPushButton("back")
        back_button.clicked.connect(self.open_main_window)

        vbox = QVBoxLayout()
        vbox.addWidget(self.text_label, alignment=Qt.AlignCenter)
        vbox.addWidget(back_button)
        central_widget.setLayout(vbox)

        if create_thread == True:
            self.thread = MonitorThread()
            self.thread.file_opened.connect(self.open_verify_window)
            self.thread.start()

    def closeEvent(self, event):
        """Modifies variables and threads when the window closes.

        When the monitor window closes this function is ran, which stops the monitor thread.
        Naming conventions are different for this method so it can automatically be
        called when the window closes.

        Args:
            event (QCloseEvent): event that is created when the window is closed.
        """

        self.thread.stop()
        event.accept()

    @Slot(bool)
    def pause_thread(self, paused):
        """Stops and creates the monitor thread.

        When passed "True" this method stops the monitor thread to save reasources.
        If passed "False" this method creates a monitor thread.

        Args:
            paused (bool): Value used to determine if a monitor thread needs to stop or be created.
        """

        if paused == True:
            self.thread.stop()

        else:
            self.thread = MonitorThread()
            self.thread.file_opened.connect(self.open_verify_window)
            self.thread.start()

    @Slot(str, str)
    def set_verified(self, name, path):
        """Updates thread value and opens an app that the user was verified for.

        Sets a value in the monitor thread to stop it from monitoring the app
        the user was just verified for and opens that app. Also sets "verifying"
        to False so that other verify windows can be opened.

        Args:
            name (str): Name of an app.
            path (str): File path of an app.
        """

        self.verifying = False

        if name != "":
            self.monitor_thread.update_verified_status(name)

            try:
                os.startfile(path)

            except FileNotFoundError:
                print("Application not found.")

    @Slot(str, str)
    def open_verify_window(self, process_name, path):
        """Opens a verify window and prevents multiple copies from being created.

        If "verifying" is set to false this method creates a verify window. If
        "verifiying" is set to True then no other verify windows can be created
        until it is closed.

        Args:
            process_name (str): Name of an app.
            path (str): File path of an app.
        """

        self.app_name = process_name
        self.app_path = path

        if self.verifying == True:
            print("second window already open")

        else:
            self.verifying = True
            self.second_window = VerifyWindow()
            self.second_window.pause_status.connect(self.pause_thread)
            self.second_window.verified_status.connect(self.set_verified)
            self.second_window.save_app_data(self.app_name, self.app_path)
            self.second_window.show()

    def open_main_window(self):
        """Opens the main window and closes current window."""

        self.second_window = MainWindow()
        self.second_window.show()
        self.close()


class MainWindow(QMainWindow):
    """
    Creates a pyqt5 window with navigation buttons to open other windows.

    Creates a window that displays buttons for the user to access the id image
    updater, app security manager, and security monitoring windows.


    """

    def __init__(self):
        """Initializes the main window and its widgets."""

        super().__init__()

        self.setWindowTitle("Face Security")
        self.setFixedSize(500, 250)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        vbox_layout = QVBoxLayout()

        update_button = QPushButton("Update ID images")
        update_button.clicked.connect(self.open_update_window)

        manager_button = QPushButton("Manage protected files")
        manager_button.clicked.connect(self.open_manager_window)

        monitor_button = QPushButton("Enable face verification")
        monitor_button.clicked.connect(self.open_monitor_window)

        vbox_layout.addWidget(update_button)
        vbox_layout.addWidget(manager_button)
        vbox_layout.addWidget(monitor_button)

        central_widget.setLayout(vbox_layout)

    def open_update_window(self):
        """Opens the update id window and closes this window."""

        self.second_window = UpdateIDWindow()
        self.second_window.show()
        self.close()

    def open_manager_window(self):
        """Opens the manager window, creates a file and closes this window."""

        data_path = "face_id/protected_data.json"

        if not os.path.exists(data_path):
            with open(data_path, "w") as fp:
                fp.write("[]")

        self.second_window = ManagerWindow()
        self.second_window.show()
        self.close()

    def open_monitor_window(self):
        """Opens the monitor window and closes this window."""

        self.second_window = MonitorWindow(True)
        self.second_window.show()
        self.close()


app = QApplication(sys.argv)

data_path = "credentials.json"

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
