from model import Model
from dataLoader import dataLoader
import tensorflow as tf
import os
from config import Config

os.environ["CUDA_DEVICE_ORDER"] = 'PCI_BUS_ID'
os.environ["CUDA_VISIBLE_DEVICES"] = '0,1'
config = tf.ConfigProto(allow_soft_placement=True)
config.gpu_options.allow_growth = True

dnnModel = Model()
dataloader = dataLoader(dataFileBatchSize=Config.batchSize)

batch = tf.placeholder(tf.float32,shape = (None,40*(Config.leftFrames+Config.rightFrames+1)),name = 'batch_input')
label = tf.placeholder(tf.float32,shape = (None,3),name="label")

def lossFunc(model,inputs,targets):
    modelOutput = model(tf.convert_to_tensor(inputs,dtype=tf.float32))
    outputs0 = tf.nn.softmax(modelOutput)
    output1 = tf.nn.softmax_cross_entropy_with_logits(logits=outputs0,labels = targets)
    output = tf.reduce_sum(output1)
    return output,modelOutput

def modelTest(model,inputs,targets):
    testLoss,modelOutput = lossFunc(model, inputs, targets)
    outputLabel=  tf.argmax(modelOutput,axis=1)
    desiredLabel = tf.argmax(targets,axis=1)
    return outputLabel,desiredLabel,testLoss

def calculateAccuracy(output,desired):
    assert (output.shape == desired.shape)
    length = output.shape[0]
    same = 0
    for i,j in zip(output,desired):
        if(i == j):
            same += 1
    return same/length



Loss,_ = lossFunc(dnnModel.model, batch, label)

trainStep = tf.train.GradientDescentOptimizer(learning_rate=Config.learningRate).minimize(Loss)

testBatch,testLabel = dataloader.getTestPositiveNextBatch()

testAcc = []
testloss = []

with tf.Session(config=config) as sess:
    sess.run(tf.global_variables_initializer())
    for epoch in range(Config.numEpochs):
        outputLabel, desiredLabel,loss = modelTest(dnnModel.model,testBatch,testLabel)
        acc = calculateAccuracy(sess.run(outputLabel), sess.run(desiredLabel))
        loss = sess.run(loss)
        testAcc.append(acc)
        testloss.append(loss)
        print(acc,loss)
        while(True):
            batchTrain,labelTrain = dataloader.getTrainPositiveNextBatch() # Get a batch of data
            if(batchTrain.shape == (0,) and labelTrain.shape == (0,)):
                break
            sess.run(trainStep,feed_dict={batch:batchTrain,label:labelTrain})

dataloader.util.savePkl("testAcc.pkl",testAcc)
dataloader.util.savePkl("testLoss.pkl",testloss)