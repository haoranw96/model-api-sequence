#!/usr/bin/env python3

import sys
import os
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
from multiprocessing import Pool
import pickle as pkl
import numpy as np
import math 

def build_feature_vector(win_list, train):
    for filename in os.listdir(train):
        with open(train + '/' + filename) as f:
            first = f.readline()
            first = first[first.find(' ')+1: first.find('\n')]
            while first:
                win = list()
                win.append(first)
                i = 1
                while i < windowSize:
                    nxt = f.readline()
                    nxt = nxt[nxt.find(' ') + 1: nxt.find('\n')]
                    win.append(nxt)
                    i += 1
                window = ' '.join(win)
                if window not in win_list:
                    win_list.append(window)
                first = f.readline()
                first = first[first.find(' ') + 1: first.find('\n')]

def construct_window_vector(file):
    apiWindow = dict()
    for filename in os.listdir(file):
        with open(file + '/' + filename) as f:
            windowCount = {i: 0 for i in win_list}
            first = f.readline()
            first = first[first.find(' ') + 1: first.find('\n')]
            while first:
                win = list()
                win.append(first)
                i = 1
                while i < windowSize:
                    nxt = f.readline()
                    nxt = nxt[nxt.find(' ') + 1: nxt.find('\n')]
                    win.append(nxt)
                    i += 1
                window = ' '.join(win)
                if window in windowCount.keys():
                    windowCount[window] += 1
                else:
                     windowCount["foreign"] = 1
                first = f.readline()
                first = first[first.find(' ') + 1: first.find('\n')]
            # print(windowCount.values())
            apiWindow.update({filename: list(windowCount.values())})
    return apiWindow

def construct_label_vector(file):
    labels = list()
    with open(file) as f:
        line = f.readline()
        while line:
            label = line.split()[1]
            #print(label)
            if label == "benign":
                labels.append(1)
            else:
                labels.append(0)
            line = f.readline()
    return labels

if __name__ == '__main__':
    global apiWindowMap
    global labelMap

    train = sys.argv[1]
    test = sys.argv[2]
    train_label_fn = sys.argv[3]
    test_label_fn = sys.argv[4]
    windowSize = int(sys.argv[5])

    # Build feature vectors for api files
    sys.stdout.write('Reading in api.txt files...\n')
    win_list = list()
    build_feature_vector(win_list, train)
    win_list.append("foreign")
    sys.stdout.write('Done\n')

    # Construct vector for each training files
    sys.stdout.write('Constructing window vector for train and test files...\n')
    trainApiWindow = construct_window_vector(train)
    x_train = np.asarray(list(trainApiWindow.values()))
    testApiWindow = construct_window_vector(test)
    x_test = np.asarray(list(testApiWindow.values()))

    sys.stdout.write("Done\n")
    #print(list(trainApiWindow.values()))

    # Construct label vector for training data
    train_label = construct_label_vector(train_label_fn)
    y_train = np.asarray(train_label)

    # Construct label vector for testing data
    test_label = construct_label_vector(test_label_fn)
    y_test = np.asarray(test_label)

    # print(x_train.shape)
    # print(y_train.shape)
    # print(x_test.shape)
    # print(y_test.shape)
    # fit svm with training data and label
    svclassifier = SVC(kernel='poly', gamma="auto")
    svclassifier.fit(x_train, y_train)

    # predict testing label
    y_pred = svclassifier.predict(x_test)

    # print confusion matrix
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))