
# coding: utf-8

# # Import Library
import matplotlib.pyplot as plt
#plt.style.use('ggplot')
import pandas as pd
import numpy as np
import seaborn as sns
import warnings
import os
import pickle

warnings.filterwarnings('ignore')
pd.options.display.float_format = '{:,.2f}'.format
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 200)

#from __future__ import print_function
from keras.models import Model, Sequential, load_model
from keras.layers import Dense, Input, Conv2D, MaxPooling2D, Flatten, Dropout,Lambda,ZeroPadding2D,concatenate,AveragePooling2D,add
from keras.datasets import mnist
from keras.optimizers import Adam
from keras.preprocessing import image
from keras import optimizers
from keras.applications import VGG16
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import EarlyStopping
from keras import backend as K
from keras import activations

from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
from keras.layers.normalization import BatchNormalization


# # Functions
def save_history(history, fn):
    with open(fn, 'wb') as fw:
        pickle.dump(history.history, fw, protocol=2)

def load_history(fn):
    class Temp():
        pass
    history = Temp()
    with open(fn, 'rb') as fr:
        history.history = pickle.load(fr)
    return history
def Inception(x,params):
    (branch1, branch2, branch3, branch4) = params
    branch1x1 = Conv2D(branch1[0],(1,1),padding='same', activation = 'relu')(x)
    branch1x1 = BatchNormalization(axis=1)(branch1x1)
    
    branch3x3 = Conv2D(branch2[0],(1,1),padding='same', activation = 'relu')(x)
    branch3x3 = Conv2D(branch2[1],(3,3),padding='same', activation = 'relu')(branch3x3)
    branch3x3 = BatchNormalization(axis=1)(branch3x3)
    
    branch5x5 = Conv2D(branch3[0],(1,1),padding='same', activation = 'relu')(x)
    branch5x5 = Conv2D(branch3[1],(5,5),padding='same', activation = 'relu')(branch5x5)
    branch5x5 = BatchNormalization(axis=1)(branch5x5)
    
    branchpool = MaxPooling2D(pool_size=(3,3),strides=1,padding='same')(x)
    branchpool = Conv2D(branch4[0],(1,1),padding='same', activation = 'relu')(branchpool)
    branchpool = BatchNormalization(axis=1)(branchpool)
 
    x = concatenate([branch1x1,branch3x3,branch5x5,branchpool],axis=3)
 
    return x
# # Reference

# dimensions of our images.
img_width, img_height = 224, 224

train_data_dir = './data/train'
validation_data_dir = './data/validation'

# # Data Generator

# #### Keras針對圖片數量不夠多的問題，也提供了解法：利用ImageDataGenerator，我們可以利用一張圖片，進行若干運算之後，得到不同的圖片。
# this is the augmentation configuration we will use for training
train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True)

# this is the augmentation configuration we will use for testing:
# only rescaling
test_datagen = ImageDataGenerator(rescale=1. / 255)

train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='binary')

validation_generator = test_datagen.flow_from_directory(
    validation_data_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='binary')


# # Building a Convolutional Neural Network

# ### GoogleNet
# 判斷RGB是在矩陣中的第幾個元素?
if K.image_data_format() == 'channels_first':
    input_shape = (3, img_width, img_height)
    bn_axis = 1
else:
    input_shape = (img_width, img_height, 3)
    bn_axis = 3
    
inpt = Input(input_shape)    
# Convolution Net Layer 1~2    
x = Conv2D(64,(7,7),strides=2,padding='same', activation = 'relu')(inpt)
x = BatchNormalization(axis=1)(x)
x = MaxPooling2D(pool_size=(3,3),strides=2,padding='same')(x)
x = Conv2D(64,(1,1),strides=1,padding='same', activation = 'relu')(x)
x = Conv2D(192,(3,3),strides=1,padding='same', activation = 'relu')(x)
x = BatchNormalization(axis=1)(x)
x = MaxPooling2D(pool_size=(3,3),strides=2,padding='same')(x)

x = Inception(x,params=[(64,),(96,128),(16,32),(32,)])
x = Inception(x,params=[(128,),(128,192),(32,96),(64,)])
x = MaxPooling2D(pool_size=(3,3),strides=2,padding='same')(x)

x = Inception(x,params=[(192,),(96,208),(16,48),(64,)])
x = Inception(x,params=[(160,),(112,224),(24,64),(64,)])
x = Inception(x,params=[(128,),(128,256),(24,64),(64,)])
x = Inception(x,params=[(112,),(144,288),(32,64),(64,)])
x = Inception(x,params=[(256,),(160,320),(32,128),(128,)])
x = MaxPooling2D(pool_size=(3,3),strides=2,padding='same')(x)


x = Inception(x,params=[(256,),(160,320),(32,128),(128,)])
x = Inception(x,params=[(384,),(192,384),(48,128),(128,)])
x = AveragePooling2D(pool_size=(7,7),strides=7,padding='same')(x)
                        
x = Flatten()(x)
x = Dropout(0.4)(x)
x = Dense(1,activation='linear')(x)
x = Dense(1,activation='sigmoid')(x)
model = Model(inpt,x,name='inception')

sgd = optimizers.SGD(lr=0.0001, momentum=0.9, nesterov=True)
model.compile(loss='binary_crossentropy',optimizer=sgd,metrics=['accuracy'])



# ## Training

history = model.fit_generator(train_generator, steps_per_epoch=120, epochs=50, 
                              validation_data=validation_generator, validation_steps=120, verbose=1)

model.save('model_GoogLeNet_v1.h5')
save_history(history, 'history_GoogLeNet_v1.bin')

model.summary()
