# -*- coding: utf-8 -*-
"""SWATDec15_AD.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1D2cE2FIRdSmLp3XW_-aHRq5e87k8Ufp5
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from typing import Dict

import warnings
warnings.filterwarnings("ignore")

seed_value = 36

import os
os.environ['PYTHONHASHSEED'] = str(seed_value)

import random
random.seed(seed_value)

import numpy as np
np.random.seed(seed_value)

import tensorflow as tf
tf.random.set_seed(seed_value)
from scr.processing import prepare_data, get_traintest
from src.processing import Predictor
from src.visualization import plot_result
from src.models.simple_models import OCSVM, LOF, iForest
from src.models.ae_lstm import AE_LSTM
from src.models.som import SOM

model_store_path = './saved_models/'

#pd.set_option('display.max_rows', 150)

"""#Загрузка данных"""

data_test = pd.read_excel('./SWAT/SWaT.A1 _ A2_Dec 2015/Physical/SWaT_Dataset_Attack_v0.xlsx', 
                          skiprows=1, 
                          parse_dates=True,
                          index_col=[0])
data_test = data_test.rename(columns={'Normal/Attack':'anomaly'})

data_test['anomaly'].value_counts()

data_test['anomaly'] = data_test['anomaly'].apply(lambda x: 0 if x=='Normal' else 1)

# исправление некорректного времени надо как то красивее, но нет пока времени на красоту
data_test.reset_index(inplace=True)
replace_idx = data_test[data_test[' Timestamp'] >= pd.to_datetime('2016-02-01')].index
data_test.loc[replace_idx,' Timestamp'] = data_test.loc[replace_idx,' Timestamp'].apply(pd.Timestamp.replace, month=1, day=2) 
data_test.index = data_test.pop(' Timestamp')

data_test.tail()

data_train = pd.read_excel('./SWAT/SWaT.A1 _ A2_Dec 2015/Physical/SWaT_Dataset_Normal_v1.xlsx', 
                          skiprows=1, 
                          parse_dates=True,
                          index_col=[0])

data_train.drop('Normal/Attack', axis=1, inplace=True)
data_train

df_train, df_test = prepare_data(data_train, data_test)

summary = {}

"""# Подготовка train/test"""

_train, x_test, y_test = get_traintest(df_train.copy(), df_test.copy())

"""# OC SVM"""

description='SWATDec15_svm_default'

model = OCSVM()
predictor = Predictor(model, [x_train, x_test, y_test], descr=description)

y_pred = predictor.get_anomalies()
summary[description] = predictor.get_score()
plot_result(df_test, y_test, y_pred, descr=description)

description='SWATDec15_svm_minmax'

x_train, x_test, y_test = get_traintest(df_train.copy(), 
                                        df_test.copy(),
                                        scaler='MinMax')

predictor = Predictor(model, [x_train, x_test, y_test], descr=description)

y_pred = predictor.get_anomalies()
summary[description] = predictor.get_score()
plot_result(df_test, y_test, y_pred, descr=description)

"""# LOF"""

anomaly_idx = [i for i in range(len(y_test)) if y_test[i] == 1]

x_train, x_test, y_test = get_traintest(df_train.copy(), 
                                        df_test.copy())

from sklearn.decomposition import PCA
pca = PCA(n_components=2)
principalComponents = pca.fit(x_train)

x_train_2d = pd.DataFrame(data = principalComponents.transform(x_train))
x_test_2d = pd.DataFrame(data = principalComponents.transform(x_test))
x_test_2d.plot(figsize=(20,5))

fig, (ax, ax_test) = plt.subplots(1, 2)
x_train_2d.plot.scatter(x=[1], y=[0], title='train', ax=ax)
x_test_2d.plot.scatter(x=[1], y=[0], title='test', ax=ax_test)
x_test_2d.iloc[anomaly_idx].plot.scatter(x=[1], y=[0], title='test', c='r', ax=ax_test)
plt.show()

N_COMPONENTS = 5

pca = PCA(n_components=N_COMPONENTS)
principalComponents = pca.fit(x_train)

x_train_pca = pd.DataFrame(data = principalComponents.transform(x_train))
x_test_pca = pd.DataFrame(data = principalComponents.transform(x_test))
x_test_pca.plot(figsize=(20,5))
plt.show()

model = LOF()

description = f'SWATDec15_lof_n{N_COMPONENTS}'
predictor = Predictor(model, [x_train_pca, x_test_pca, y_test], descr=description, resave_model=False)

y_pred = predictor.get_anomalies()
summary[description] = predictor.get_score()
plot_result(df_test, y_test, y_pred, descr=description)

"""# iForest"""

description = f'SWATDec15_iF_default'

x_train, x_test, y_test = get_traintest(df_train.copy(), df_test.copy())

model = iForest()

predictor = Predictor(model, [x_train, x_test, y_test], descr=description, resave_model=False)
y_pred = predictor.get_anomalies()
summary[description] = predictor.get_score()
plot_result(df_test, y_test, y_pred, descr=description)

description = f'SWATDec15_iF_n_200_c_01'

x_train, x_test, y_test = get_traintest(df_train.copy(), 
                                        df_test.copy())

model = iForest(n_estimators=200, contamination=0.1)

predictor = Predictor(model, [x_train, x_test, y_test], descr=description, resave_model=True)
y_pred = predictor.get_anomalies()
summary[description] = predictor.get_score()
plot_result(df_test, y_test, y_pred, descr=description)

"""# Autoencoder"""

window_size = 30
resample_rate = None

description = f'SWATDec15_ae_lstm_window_{window_size}_resample_{resample_rate}'

x_train, x_test, y_test = get_traintest(df_train.copy(), 
                                        df_test.copy(), 
                                        window_size=window_size, 
                                        resample_rate=resample_rate)

model = AE_LSTM()

predictor = Predictor(model, 
                      [x_train, x_test, y_test], 
                      descr=description, 
                      window_size=window_size,
                      resave_model=False)

y_pred = predictor.get_anomalies()
summary[description] = predictor.get_score()
plot_result(df_test, y_test[:,0], y_pred, descr=description)

"""Scaling... (Standard)
Количество аномалий: 87.9%

Counter({1: 395298, 0: 54621})
Create sequences with window size 30...
Размеры выборок:
            x_train: (494971, 30, 46)
            x_test: (449890, 30, 46)
            y_test: (449890, 30)

# SOM
"""

x_train, x_test, y_test = get_traintest(df_train.copy(), 
                                        df_test.copy())

description = f'SWATDec15_som_default'

model = SOM(x_train)

predictor = Predictor(model, 
                      [x_train, x_test, y_test], 
                      descr=description,
                      resave_model=False)

y_pred = predictor.get_anomalies()
summary[description] = predictor.get_score()
plot_result(df_test, y_test, y_pred, descr=description)

"""# Сводная таблица"""

def highlight_max(s, props=''):
    return np.where(s == np.nanmax(s.values), props, '')

df_summary = pd.DataFrame(summary).T
df_summary.style.format(precision=2).background_gradient(cmap='Blues')