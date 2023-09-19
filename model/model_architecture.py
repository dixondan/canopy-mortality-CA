
from keras.models import Model
from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate, Conv2DTranspose, BatchNormalization, Dropout, Lambda
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
import os
import numpy as np
from tensorflow.keras.layers import *
from tensorflow.keras.activations import swish


def sep_conv_2d(x: tf.Tensor, filters: int) -> tf.Tensor: # two convolutional chunks / operations
    x = Conv2D(filters, 1, use_bias=False)(x)
    x = BatchNormalization()(x)
    x = swish(x)
    x = DepthwiseConv2D(3, use_bias=False, padding='same')(x)
    x = BatchNormalization()(x)
    return tf.keras.activations.swish(x)

def create_st_model_1(channels: int) -> tf.keras.Model:
    x_input = tf.keras.layers.Input((None, None, None, channels), dtype=tf.float32)
    input_shape = tf.shape(x_input)
    batch_dim = input_shape[0]
    time_dim = input_shape[1]
    height_dim = input_shape[2]
    width_dim = input_shape[3]
    # N*T, H, W, C
    x_input_space = tf.reshape(x_input, (batch_dim * time_dim, height_dim, width_dim, channels))
    x = Conv2D(32, 3, use_bias=False, padding='same')(x_input_space)
    x = BatchNormalization()(x)
    x = swish(x)
    x = Conv2D(64, 3, use_bias=False, padding='same')(x)
    x = BatchNormalization()(x)
    x = swish(x)
    x = sep_conv_2d(x, 128)
    x = sep_conv_2d(x, 128)
    x = sep_conv_2d(x, 128)
    x = sep_conv_2d(x, 128)
    # N, T, H, W, C
    x_input_time = tf.reshape(x, (batch_dim, time_dim, height_dim, width_dim, 128))
    x = Conv3D(128, (3, 1, 1), activation='relu', use_bias=True, padding='same')(x_input_time)
    # N, T/2, H, W, C
    x = MaxPooling3D((2, 1, 1))(x)
    x = Conv3D(128, (3, 1, 1), activation='relu', use_bias=True, padding='same')(x)
    # N, T/4, H, W, C
    x = MaxPooling3D((2, 1, 1))(x)
    x = Conv3D(128, (3, 1, 1), activation='relu', use_bias=True, padding='same')(x)
    # N, T=1, H, W, C
    x = MaxPooling3D((3, 1, 1))(x)
    x = tf.reshape(x, (batch_dim, height_dim, width_dim, 128))
    x = Dense(256, activation='relu')(x)
    x = Dense(nclasses, activation='softmax')(x)
    x = tf.reshape(x, (batch_dim, height_dim, width_dim, nclasses))
    return tf.keras.Model(inputs=x_input, outputs=x)


def run_model():

    model_name = "topo0_nclasses5"
    n_classes = 5
    n_channels = 5

    loc = 'Xy_data'

    X_train = np.load(os.path.join(loc, 'X_train_topo0.npy'), allow_pickle=True, fix_imports=True)
    X_train = X_train * 0.0001
    X_train = X_train.astype('float32')
    y_train = np.load(os.path.join(loc, 'y_train-nclasses5.npy'), allow_pickle=True, fix_imports=True)

    X_valid = np.load(os.path.join(loc, 'X_valid_topo0.npy'), allow_pickle=True, fix_imports=True)
    X_valid = X_valid * 0.0001
    X_valid = X_valid.astype('float32')
    y_valid = np.load(os.path.join(loc, 'y_valid-nclasses5.npy'), allow_pickle=True, fix_imports=True)

    y_train_cat = to_categorical(y_train, num_classes=n_classes)
    y_valid_cat = to_categorical(y_valid, num_classes=n_classes)

    model = create_st_model_1(channels=n_channels, nclasses=n_classes)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['acc'])

    model.summary()
    model.fit(X_train, y_train_cat,
                    batch_size=16,
                    epochs=50,
                    validation_data=(X_valid, y_valid_cat),
                    shuffle=True)

    outname = '{}'.format(model_name)
    model.save(outname)


if __name__ == "__main__":
    run_model()
