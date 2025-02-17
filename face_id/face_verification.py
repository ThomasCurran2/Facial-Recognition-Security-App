import cv2
import numpy as np
import psutil
import json
import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf

from face_id.layers import L1Dist
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal as Signal, Qt, QThread, QObject
from PyQt5.QtGui import QPixmap


class FaceVerifier(QObject):
    """
    Class used for facial verification with the use of a siamese neural network.

    Uses the siamese neural network to determine the distance, similarity, between the current
    webcam image and the user's face id images. If enough distances are considered verified
    then true is emited for other classes to perform operations.

    Attributes:
        verified_signal (pyqtSignal): signal that emits a bool if the image is verified or not.
    """

    verified_signal = Signal(bool)

    def __init__(self):
        """Initializes the FaceVerifier class."""

        super().__init__()

    def verify(self, current_image, verified_label, *args):
        """Preforms facial verification with a siamese neural network.

        Uses a siamese neural network to calculate the distance, similarity,
        between the user's webcam image and the saved face id images. Users are
        considered verified if thier distance values are higher than the detection
        threshold, and when the total number of detected images divided by the total amount of
        face id images is higher than the verification threshold.

        Args:
            current_image (ndarray): Current webcam image that is saved as the input image.
            verified_label (QLabel): Text label that displays if the verification failed.
            *args: Arbitrary non-keyword arguments with tuple values.
        """

        self.model = tf.keras.models.load_model(
            "face_id/siamesemodelv2.h5", custom_objects={"L1Dist": L1Dist}
        )

        detection_threshold = 0.5
        verification_threshold = 0.5

        file_path = os.path.join("face_id/image_data", "input_image", "input_image.jpg")
        cv2.imwrite(file_path, current_image)

        results = []
        for image in os.listdir(
            os.path.join("face_id/image_data", "verification_images")
        ):
            input_image = self.preprocess(
                os.path.join("face_id/image_data", "input_image", "input_image.jpg")
            )
            validation_image = self.preprocess(
                os.path.join("face_id/image_data", "verification_images", image)
            )
            result = self.model.predict(
                list(np.expand_dims([input_image, validation_image], axis=1))
            )
            results.append(result)

        detection = np.sum(np.array(results) > detection_threshold)

        verification = detection / len(
            os.listdir(os.path.join("face_id/image_data", "verification_images"))
        )
        verified = verification > verification_threshold

        if verified == True:
            self.verified_signal.emit(True)

        else:
            verified_label.setText("Unverified, please try again")
            self.verified_signal.emit(False)

    def preprocess(self, file_path):
        """Loads an image and alters its size/scale.

        Takes an image at a specific file path and resizes/scales
        it. Used to make sure that the input image and all of the
        verification images are the same size and scale before
        any calculations are done.

        Args:
            file_path (str): file path to a specific image.

        Returns:
            tensorflow.python.framework.ops.EagerTensor: image data used in verification calculations.
        """

        byte_image = tf.io.read_file(file_path)
        image = tf.io.decode_jpeg(byte_image)
        image = tf.image.resize(image, (100, 100))
        image = image / 255.0
        return image


class IDUpdater:
    """
    Deletes old face id images and saves the user's new ones to a folder.

    Updates the user's face id images by deleting any old images in the
    verification_images folder before saving their new ones into the
    same folder.
    """

    def update(self, image_array, *args):
        """Updates old face id images with new images.

        Takes a list of images that have been captured from the user's
        webcam and adds them to the "verification_images" folder. If
        this folder has images inside of it then the old images are
        deleted before adding the new images.

        Args:
            image_array (list): List containing images from the user's webcam.
            *args: Arbitrary non-keyword arguments with tuple values.
        """

        dir_path = os.path.join("face_id/image_data", "verification_images")

        if len(os.listdir(dir_path)) > 0:
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                os.remove(file_path)
                print(f"Deleted file: {filename}")

        for idx in range(len(image_array)):
            cv2.imwrite(
                os.path.join(
                    "face_id/image_data",
                    "verification_images",
                    "verfication_image_" + str(idx) + ".jpg",
                ),
                image_array[idx],
            )


class VideoThread(QThread):
    """
    Class used to capture/convert the webcam's image so it can be displayed.

    Captures the user's webcam using opencv and converts the image into a pixmap
    that can be displayed in the verify window and id updater window. The current
    opencv image is also returned for the id image updater.

    Attributes:
        pixmap_signal (pyqtSignal): signal that emits a pixmap used to update the verify window's image label.
        image_signal (pyqtSignal): signal that emits a opencv image used in the id image updater.
    """

    pixmap_signal = Signal(QPixmap)
    image_signal = Signal(np.ndarray)

    def __init__(self):
        """Initializes the video thread class."""

        super().__init__()
        self._run_flag = True

    def run(self):
        """Captures and resizes the user's webcam image.

        While the thread is running, the user's webcam is
        captured and resized to match to match the images
        used for verification. Also emits the current image
        to be used in verification and sends it to be converted
        to a pixmap.

        Raises:
            TypeError: If any wrong data types are passed through while trying to capture the webcam image.
        """

        try:
            cap = cv2.VideoCapture(0)

            while self._run_flag:
                ret, cv_image = cap.read()
                cv_image = cv_image[120 : 120 + 250, 200 : 200 + 250, :]

                if ret:
                    self.image_signal.emit(cv_image)
                    self.convert_cv_qt(cv_image)

            cap.release()

        except TypeError:
            print("Type error")

    def convert_cv_qt(self, cv_image):
        """Converts the current webcam image to a pixmap image.

        Changes the opencv image taken from the webcam and creates a
        pixmap image that can be displayed in a pyqt5 window.

        Args:
            cv_image (ndarray): Current webcam image to be converted.
        """

        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        pix_map = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888
        )
        scaled_pixmap = pix_map.scaled(
            400,
            400,
            aspectRatioMode=Qt.KeepAspectRatio,
            transformMode=Qt.SmoothTransformation,
        )
        self.pixmap_signal.emit(QPixmap.fromImage(scaled_pixmap))

    def stop(self):
        """Stops the thread when ran."""

        self._run_flag = False
        self.wait()


class MonitorThread(QThread):
    """
    Class used to capture/convert the webcam's image so it can be displayed.

    Captures the user's webcam using opencv and converts the image into a pixmap
    that can be displayed in the verify window and id updater window. The current
    opencv image is also returned for the id image updater.

    Attributes:
        file_opened (pyqtSignal): signal that emits an app's name and path.
        approved_array (list): list used to store if the user was verified to use a protected app.
    """

    file_opened = Signal(str, str)

    approved_array = []

    def __init__(self):
        """Initializes the monitor thread class.

        Initializes the class by calling the super's __init__
        function, loading the list of protected apps, and starting
        the thread.
        """

        super().__init__()
        self.get_process_list()
        self.run_flag = True

    def run(self):
        """Runs a function that searches for/stops specific apps on a list."""

        self.kill_processes(self.protected_processes)

    def kill_processes(self, process_names):
        """Searches for and stops protected apps if they are running.

        Looks through all running processes to see if any app in the
        process_names list is open, and closes the app if it's running.
        If the user has been verified to use the app, having "True" in the
        approved_array with the same index as an app's name in process_names, then
        that app will remain open. Also, the app's name and path are emitted to be
        used in the verification process.

        Args:
            process_names (list): List of processes that are protected by this app.

        Raises:
            psutil.NoSuchProcess: If a protected process is open but can't be properly closed.
        """

        while self.run_flag:
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                if proc.info["name"] in process_names:
                    if (
                        self.approved_array[
                            self.protected_processes.index(proc.info["name"])
                        ]
                        == False
                    ):
                        try:

                            if proc.is_running():
                                proc.terminate()

                            self.file_opened.emit(proc.info["name"], proc.info["exe"])
                            print(f"Killed process: {proc.info['name']}")

                        except psutil.NoSuchProcess:
                            print(f"Process not found: {proc.info['name']}")

    def get_process_list(self):
        """Gets a list of protected processes and sets a default approval status.

        Loads a list of protected processes from a file and sets it to a variable.
        Also, adds a "False" to the approval array for each process if the
        approval array is empty.
        """

        with open("face_id/protected_data.json", "r") as open_file:
            self.protected_processes = json.load(open_file)

        if len(self.approved_array) == 0:
            for idx in self.protected_processes:
                self.approved_array.append(False)

    def update_verified_status(self, app_name):
        """Updates the approved status for an app the user has been verified to use.

        Changes an index in the approved_array to "True",
        with the index being the same value as the index
        of app_name inside the protected_processes array.

        Args:
            app_name (str): Name of an app that the user is verified to use.
        """
        self.approved_array[self.protected_processes.index(app_name)] = True

    def stop(self):
        """Stops the monitor thread when called."""
        self.run_flag = False
        self.quit()
        self.wait()
