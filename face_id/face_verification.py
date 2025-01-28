import cv2
import tensorflow as tf
import os
import numpy as np

from face_id.layers import L1Dist
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal as Signal, Qt, QThread
from PyQt5.QtGui import QPixmap


class FaceVerifier:

    def verify(self, current_image, verified_label, *args):
        self.model = tf.keras.models.load_model(
            "face_id\siamesemodelv2.h5", custom_objects={"L1Dist": L1Dist}
        )

        # Add loading bar to show progress

        detection_threshold = 0.5
        verification_threshold = 0.5

        file_path = os.path.join("face_id/app_data", "input_image", "input_image.jpg")
        cv2.imwrite(file_path, current_image)

        results = []
        for image in os.listdir(
            os.path.join("face_id/app_data", "verification_images")
        ):
            input_image = self.preprocess(
                os.path.join("face_id/app_data", "input_image", "input_image.jpg")
            )
            validation_image = self.preprocess(
                os.path.join("face_id/app_data", "verification_images", image)
            )
            result = self.model.predict(
                list(np.expand_dims([input_image, validation_image], axis=1))
            )
            results.append(result)

        detection = np.sum(np.array(results) > detection_threshold)

        verification = detection / len(
            os.listdir(os.path.join("face_id/app_data", "verification_images"))
        )
        verified = verification > verification_threshold

        # Add code that opens files/prompts the user to try again
        if verified == True:
            verified_label.setText("Verified")
        else:
            verified_label.setText("Unverified, please try again")

    def preprocess(self, file_path):
        byte_image = tf.io.read_file(file_path)
        image = tf.io.decode_jpeg(byte_image)

        image = tf.image.resize(image, (100, 100))
        image = image / 255.0

        return image


class VideoThread(QThread):
    pixmap_signal = Signal(QPixmap)
    image_signal = Signal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_image = cap.read()
            cv_image = cv_image[120 : 120 + 250, 200 : 200 + 250, :]
            if ret:
                self.image_signal.emit(cv_image)
                self.convert_cv_qt(cv_image)
        cap.release()

    def convert_cv_qt(self, cv_image):
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
        self._run_flag = False
        self.wait()
