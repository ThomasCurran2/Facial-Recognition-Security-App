import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
from tensorflow.keras.layers import Layer


class L1Dist(Layer):
    """Creates a custom distance layer class and finds the distance between image embeddings.

    Creates a class to be used when loading the neural network model. Used to find
    the distance between 2 image embeddings and return the value, which is used
    to determine if those images are similar enough to be verified.


    """

    def __init__(self, **kwargs):
        """Initializes the L1Dist class.

        Uses the __init__ fucntion of the super class to initialize
        the custom distance layer.

        Args:
            **kwargs: Arbitrary keyword arguments with str values.
        """

        super(L1Dist, self).__init__(**kwargs)

    def call(self, input_embedding, validation_embedding):
        """Calculates and returns the similarity between 2 image embeddings.

        This function takes the embedding of the input image and the
        embedding of the validation image and calculates the distance,
        similarity, between them and returns that value as a float.

        Args:
            input_embedding (tensorflow.python.framework.ops.SymbolicTensor): Feature vector that represents the input image
            validation_embedding (tensorflow.python.framework.ops.SymbolicTensor): Feature vector that represents the validation image

        Returns:
            float: The distance value between the 2 embeddings
        """

        return tf.math.abs(input_embedding - validation_embedding)
