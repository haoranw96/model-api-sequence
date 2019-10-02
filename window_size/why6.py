#!/usr/bin/env python3

import sys
import os
import numpy as np

def build_feature_vector(win_list, benign):
    for filename in os.listdir(benign):
        with open(benign + '/' + filename) as f:
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
                     windowCount["foreign"] += 1
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
    global count
    count = 0

    sys.stdout.write('Usage: python3 why6.py train/ test/ train_label.txt test_label.txt [window size]\n')

    benign = sys.argv[1]
    malicious = sys.argv[2]
    #train_label_fn = sys.argv[3]
    #test_label_fn = sys.argv[4]
    windowSize = int(sys.argv[3])

    # Build feature vectors for api files
    sys.stdout.write('Reading in api.txt files...\n')
    win_list = list()
    build_feature_vector(win_list, benign)
    win_list.append("foreign")
    sys.stdout.write('Done\n')

    # Construct vector for each training files
    sys.stdout.write('Constructing window vector for train and test files...\n')
    #trainApiWindow = construct_window_vector(benign)
    #x_train = np.asarray(list(trainApiWindow.values()))
    testApiWindow = construct_window_vector(malicious)
    x_test = np.asarray(list(testApiWindow.values()))

    sys.stdout.write("Done\n")

    for k,v in testApiWindow:
        print(k, v["foreign"])

    # Construct label vector for training data
    #train_label = construct_label_vector(train_label_fn)
    #y_train = np.asarray(train_label)

    # Construct label vector for testing data
    #test_label = construct_label_vector(test_label_fn)
    #y_test = np.asarray(test_label)

    # print(x_train.shape)
    # print(y_train.shape)
    # print(x_test.shape)
    # print(y_test.shape)
    # fit svm with training data and label
   