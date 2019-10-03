#!/usr/bin/env python3

import sys
import os
import numpy as np

def build_feature_vector(win_list, benign):
    for filename in os.listdir(benign):
        with open(benign + '/' + filename, encoding='windows-1252') as f:
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
        with open(file + '/' + filename, encoding='windows-1252') as f:
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

    sys.stdout.write('Usage: python3 why6.py benign/ malicious/ \n')

    windowSize = 1
    fp = open("foreign_window.csv", "w+")
    fp.write("window size, average # of foreign window\n")
    fp.close()

    fp = open("foreign_window.csv", "a")
    while windowSize < 300:
        benign = sys.argv[1]
        malicious = sys.argv[2]

        # Build feature vectors for api files
        sys.stdout.write('Reading in api.txt files...\n')
        win_list = list()
        build_feature_vector(win_list, benign)
        win_list.append("foreign")
        sys.stdout.write('Done\n')

        # Construct vector for each training files
        sys.stdout.write('Constructing window vector for train and test files...\n')
        testApiWindow = construct_window_vector(malicious)
        x_test = np.asarray(list(testApiWindow.values()))

        sys.stdout.write("Done\n")

        sum = 0
        for (k,v) in testApiWindow.items():
            sum += v[-1]
            #print(k, v[-1])
        print ('window size: %d, average number of foreign window: %d' % (windowSize, sum/20))
        fp.writelines('%d, %f\n' % (windowSize, sum/20))

        windowSize+=1
    fp.close()
