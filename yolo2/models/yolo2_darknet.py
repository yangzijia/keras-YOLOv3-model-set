#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO_v2 Model Defined in Keras."""

from tensorflow.keras.layers import MaxPooling2D, Lambda, Concatenate, GlobalAveragePooling2D, Softmax
from tensorflow.keras.models import Model

from yolo2.models.layers import compose, DarknetConv2D, DarknetConv2D_BN_Leaky, bottleneck_block, bottleneck_x2_block, space_to_depth_x2, space_to_depth_x2_output_shape


def darknet19_body():
    """Generate first 18 conv layers of Darknet-19."""
    return compose(
        DarknetConv2D_BN_Leaky(32, (3, 3)),
        MaxPooling2D(),
        DarknetConv2D_BN_Leaky(64, (3, 3)),
        MaxPooling2D(),
        bottleneck_block(128, 64),
        MaxPooling2D(),
        bottleneck_block(256, 128),
        MaxPooling2D(),
        bottleneck_x2_block(512, 256),
        MaxPooling2D(),
        bottleneck_x2_block(1024, 512))


def yolo2_body(inputs, num_anchors, num_classes, weights_path=None):
    """Create YOLO_V2 model CNN body in Keras."""
    darknet19 = Model(inputs, darknet19_body()(inputs))
    if weights_path is not None:
        darknet19.load_weights(weights_path, by_name=True)
        print('Load weights {}.'.format(weights_path))

    # input: 416 x 416 x 3
    # darknet19.output : 13 x 13 x 1024
    # conv13(layers[43]) : 26 x 26 x 512

    conv20 = compose(
        DarknetConv2D_BN_Leaky(1024, (3, 3)),
        DarknetConv2D_BN_Leaky(1024, (3, 3)))(darknet19.output)

    # conv13 output shape: 26 x 26 x 512
    conv13 = darknet19.layers[43].output
    conv21 = DarknetConv2D_BN_Leaky(64, (1, 1))(conv13)
    # TODO: Allow Keras Lambda to use func arguments for output_shape?
    conv21_reshaped = Lambda(
        space_to_depth_x2,
        output_shape=space_to_depth_x2_output_shape,
        name='space_to_depth')(conv21)

    x = Concatenate()([conv21_reshaped, conv20])
    x = DarknetConv2D_BN_Leaky(1024, (3, 3))(x)
    x = DarknetConv2D(num_anchors * (num_classes + 5), (1, 1))(x)
    return Model(inputs, x)


def darknet19(inputs):
    """Generate Darknet-19 model for Imagenet classification."""
    body = darknet19_body()(inputs)
    x = DarknetConv2D(1000, (1, 1))(body)
    x = GlobalAveragePooling2D()(x)
    logits = Softmax()(x)
    return Model(inputs, logits)

