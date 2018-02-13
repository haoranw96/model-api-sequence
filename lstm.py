import sys
import os
import shutil
import cPickle as pkl
import numpy as np
import math
from collections import Counter

from sklearn.model_selection import KFold
from sklearn.metrics import confusion_matrix,roc_auc_score

from keras.models import Sequential
from keras.layers import Dense, LSTM
from keras import callbacks as cb

# Creates multiple generators of the data to use on Keras
# We do this because we can have very large datasets we can't
# fit entirely into memory.
def sequence_generator(folder, sample, labels, labelMap, foldIDs, batchSize):
    xSet = list()
    ySet = list()

    for e,i in enumerate(foldIDs):
        x = list()
        y = list()

        # Read in sample's sequence and convert it a sequence integers
        path = os.path.join(folder,sample[i]+'.pkl')
        with open(path, 'rb') as fr:
            x = pkl.load(fr)

        # Here we put each api into its own array of size one.
        # This sounds silly, but it's how Keras works for a dataset like api call sequences
        # It's because for us, there's only one feature per line in the sequence.
        # In Keras, it is possible to have multiple features per line in a sequence.
        # https://machinelearningmastery.com/reshape-input-data-long-short-term-memory-networks-keras/
        xSet.append([list([seq]) for seq in x])

        # We convert labels to numbers (we could have used Keras' categorical
        # functionality to convert it to an appropriate hot encoding instead,
        # but I like this better because it looks cleaner)
        ySet.append(list([labelMap.index(labels[sample[i]])]))

        # Batch size reached, yield data
        if (e+1) % batchSize == 0:
            # Here we convert our lists into Numpy arrays because
            # Keras requires it as input for its fit_generator()
            x = np.array(xSet)
            y = np.array(ySet)

            xSet = list()
            ySet = list()

            yield (x, y)

    # Yield remaining set
    if len(xSet) > 0:
        yield (np.array(xSet), np.array(ySet))

# Builds LSTM model
def build_LSTM_model(trainData, trainBatches, testData, testBatches, maxLen, class_count):
    # Specify number of hidden layers
    hidden_layers = 100

    # https://keras.io/callbacks/#earlystopping
    early_stop = cb.EarlyStopping(monitor='sparse_categorical_accuracy', min_delta = 0.0001, patience = 3)

    model = Sequential()

    model.add(
        # https://keras.io/layers/recurrent/#lstm
        # https://machinelearningmastery.com/reshape-input-data-long-short-term-memory-networks-keras/
        LSTM(
            hidden_layers,
            # https://keras.io/getting-started/sequential-model-guide/#specifying-the-input-shape
            # maxLen is the length of each sample's sequence length, 1 is the dimension of the feature.
            # In our case the feature dimension is 1 because each api call is a single feature (explained more
            # in https://machinelearningmastery.com/reshape-input-data-long-short-term-memory-networks-keras/)
            input_shape=(maxLen, 1),
            return_sequences=False
            )
        )

    # https://keras.io/layers/core/#dense
    model.add(Dense(class_count, activation='softmax'))

    # https://keras.io/models/model/#compile
    model.compile(
        loss='sparse_categorical_crossentropy',
        # Which optimizer to use: https://keras.io/optimizers/
        optimizer='rmsprop',
        # Metrics to print
        # We use sparse_categorical_accuracy as opposed to categorical_accuracy
        # because: https://stackoverflow.com/questions/44477489/keras-difference-between-categorical-accuracy-and-sparse-categorical-accuracy
        metrics=['sparse_categorical_accuracy'])

    # https://keras.io/models/model/#fit_generator
    hist = model.fit_generator(
        # Data to train
        trainData,
        # Use multiprocessing because python Threading isn't really
        # threading: https://docs.python.org/2/glossary.html#term-global-interpreter-lock
        use_multiprocessing = True,
        # Number of steps per epoch (this is how we train our large
        # number of samples dataset without running out of memory)
        steps_per_epoch = trainBatches,
        #TODO - Why can't we do multiple epochs?
        # According to the error it seems like the generator cannot be looped multiple times?
        # https://github.com/keras-team/keras/issues/5818#issuecomment-288516239
        # According to the article ^ seems like epoch doesn't mean what we think it means.
        epochs = 1,
        # Validation data (will not be trained on)
        validation_data = testData,
        validation_steps = testBatches,
        # Shuffle order of batches at beginning of each epoch
        shuffle = True,
        # List of callbacks to be called while training.
        callbacks = [early_stop])

    return model, hist

# Trains and tests LSTM over samples
def train_lstm(folder, sample, labels, labelMap, model_folder):
    # Number of folds in cross validation
    nFolds = 10

    # Batch size (# of samples to have LSTM train at a time)
    # It's okay if this does not evenly divide your entire sample set
    batchSize = 400

    # Sequence lengths (should be all the same. they should be padded)
    maxLen = 0
    path = os.path.join(folder,sample[0]+'.pkl')
    with open(path, 'rb') as fr:
        x = pkl.load(fr)
        maxLen = len(x)

    print 'Sequence length of each sample: {0}'.format(maxLen)

    # Get folds for cross validation
    folds = KFold(n_splits=nFolds, shuffle=True)
    foldCount = 0

    # Train and test LSTM over each fold
    for trainFold, testFold in folds.split(sample):
        foldCount += 1
        print '==========================================================='
        print 'Training Fold {0}/{1}'.format(foldCount,nFolds)

        # Put features into format LSTM can ingest
        trainData = sequence_generator(folder, sample, labels, labelMap, trainFold, batchSize)
        testData = sequence_generator(folder, sample, labels, labelMap, testFold, batchSize)

        # Calculate number of batches
        train_num_batches = math.ceil(float(len(trainFold))/batchSize)
        test_num_batches = math.ceil(float(len(testFold))/batchSize)

        # Train LSTM model
        lstm,hist = build_LSTM_model(trainData, train_num_batches, testData, test_num_batches, maxLen, len(labelMap))
        # Print accuracies
        print ''
        print hist.history

        # https://machinelearningmastery.com/save-load-keras-deep-learning-models/
        # Convert model to JSON format to be stored
        modelJSON = lstm.to_json()
        # Store model in model_folder
        fn = os.path.join(model_folder,'fold{0}-model.json'.format(foldCount))
        with open(fn,'w') as fw:
            fw.write(modelJSON)
        # Store weights for model
        fn = os.path.join(model_folder,'fold{0}-weight.h5'.format(foldCount))
        lstm.save_weights(fn)

        # Run predictions over test data one last time to get final results
        # https://keras.io/models/model/#predict_generator
        p = lstm.predict_generator(testData, steps=test_num_batches, use_multiprocessing=True)
        # Extract predicted classes for each sample in testData
        # https://stackoverflow.com/questions/38971293/get-class-labels-from-keras-functional-model
        predictClasses = p.argmax(axis=-1)
        trueClasses = list()
        for x,y in testData:
            for l in y:
                trueClasses.append(l[0])

        # Print AUC
        # NOTE: there are issues with doing this currently:
        # https://stackoverflow.com/questions/39685740/calculate-sklearn-roc-auc-score-for-multi-class#39703870
        # http://scikit-learn.org/stable/auto_examples/model_selection/plot_roc.html#multiclass-settings
        # https://github.com/scikit-learn/scikit-learn/issues/3298
#       auc = roc_auc_score(trueClasses,predictClasses)
#       print 'AUC: {0}'.format(auc)

        # Print counts of each label for fold (combination of labels from train and test since
        # it's no guaranteed they'll have the same labels)
        c = Counter(trueClasses) + Counter(predictClasses)
        foldLabelMap = sorted(c.keys())
        print ''
        print 'Fold Indices/Counts (fold dataset):'
        for e,l in enumerate(foldLabelMap):
            sys.stdout.write('Index: {0: <10} Class: {1: <20} Count: {2: <10} ({3:.4f}% of fold dataset)\n'.format(e,l,c[l],100*float(c[l])/sum(c.values())))

        # Print confusion matrix
        # http://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html
        cf = confusion_matrix(trueClasses,predictClasses)
        print ''
        print 'Confusion Matrix (fold dataset): (x-axis: Actual, y-axis: Predicted)'
        for x in cf:
            for y in x:
                sys.stdout.write('{0} '.format(y))
            sys.stdout.write('\n')
        print ''

        # Print TP/FP/FN/TN rates
        # A nice visual for determining these for the multi-class case:
        # https://stackoverflow.com/questions/31324218/scikit-learn-how-to-obtain-true-positive-true-negative-false-positive-and-fal
        # https://stackoverflow.com/a/43331484
        # Convert confusion matrix to floats so we can have decimals
        cf = cf.astype(np.float32)
        FP = cf.sum(axis=0) - np.diag(cf)
        FN = cf.sum(axis=1) - np.diag(cf)
        TP = np.diag(cf)
        TN = cf.sum() - (FP + FN + TP)
        TPR = TP/(TP+FN)
        TNR = TN/(TN+FP)
        FNR = FN/(FN+TP)
        FPR = FP/(FP+TN)
        ACC = (TP+TN)/(TP+TN+FP+FN)
        print 'Stats for each class (class is index in these arrays)'
        print 'TPR: {0}\nFPR: {1}\nFNR: {2}\nTNR: {3}\n'.format(list(TPR),list(FPR),list(FNR),list(TNR))
        print 'ACC: {0}\n'.format(list(ACC))

def usage():
    print 'usage: python lstm.py features/labels features/ models/'
    sys.exit(2)

def _main():
    if len(sys.argv) != 4:
        usage()

    label_fn = sys.argv[1]
    folder = sys.argv[2]
    model_folder = sys.argv[3]

    # Remove model folder if it already exists
    if os.path.exists(model_folder):
        shutil.rmtree(model_folder)
        os.mkdir(model_folder)
    else:
        os.mkdir(model_folder)

    # Get all samples in features folder
    sample = list()

    labels = dict()
    labelMap = set()
    # Extract labels for samples
    with open(label_fn, 'r') as fr:
        for line in fr:
            line = line.strip('\n')
            s = line.split(' ')[0]
            l = line.split(' ')[1]

            sample.append(s)
            labels[s] = l
            labelMap.add(l)

    # Get label counts
    c = Counter([l for s,l in labels.iteritems()])

    # Lock in label ordering (and sort by popularity)
    labelMap = sorted(labelMap, key=lambda l: c[l], reverse=True)

    # Print class labels and counts
    print 'Total Dataset:'
    for e,l in enumerate(labelMap):
        sys.stdout.write('Class: {0: <10} Label: {1: <20} Count: {2: <10} ({3:.2f}% of dataset)\n'.format(e,l,c[l],100*float(c[l])/sum(c.values())))
    print ''

    # Train LSTM
    train_lstm(folder, sample, labels, labelMap, model_folder)

if __name__ == '__main__':
    _main()
