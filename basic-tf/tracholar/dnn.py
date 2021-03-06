#coding:utf-8
import os
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets('./MNIST_data')


## 创建计算图中的关键节点
with tf.name_scope('input'):
    x = tf.placeholder(tf.float32, [None, 784])
    label = tf.placeholder(tf.int32, [None])
    y_ = tf.one_hot(label, 10)

def logistic_regression(x_):
    with tf.name_scope('logistic_regression'):
        W = tf.Variable(tf.zeros([784, 10]), name='weights')
        b = tf.Variable(0.0, name='bais')

        y = tf.matmul(x_, W) + b

    tf.summary.histogram('w', W)
    return y

def conv_net(x_):
    with tf.name_scope('conv'):
        h1 = tf.layers.conv2d(tf.reshape(x_, (-1, 28, 28, 1)), filters=32, kernel_size=(5,5), strides=(2,2), padding='same', activation=tf.nn.relu, name='conv-layer1', kernel_initializer=tf.contrib.layers.variance_scaling_initializer())

        h2 = tf.layers.conv2d(h1,
                              filters=32, kernel_size=(5,5), strides=(2,2), padding='same', activation=tf.nn.relu, name='conv-layer4', kernel_initializer=tf.contrib.layers.variance_scaling_initializer())

        z = tf.reduce_mean(h2, axis=[1,2])
        y = tf.layers.dense(z, 10)
    tf.summary.histogram('h1', h1)
    tf.summary.histogram('h2', h2)
    tf.summary.histogram('z', z)
    return y


y = conv_net(x)

## 定义损失函数
with tf.name_scope('loss'):
    cross_entropy = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y))

    ## 定义预测准确率
    acc = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(y, axis=1), tf.argmax(y_, axis=1)), dtype=tf.float32))

## 定义一个step全局变量和优化器,并指定 global_step
step = tf.Variable(0, trainable=False)
optimizer = tf.train.AdamOptimizer(1e-3)
train_op = optimizer.minimize(cross_entropy, global_step=step)
update_op = tf.get_collection(tf.GraphKeys.UPDATE_OPS)

## 添加summary: loss, acc, w的直方图
tf.summary.scalar('loss', cross_entropy)
tf.summary.scalar('acc', acc)
tf.summary.image('mnist', tf.reshape(x, (-1, 28, 28, 1)), 9)
merged = tf.summary.merge_all()





with tf.Session() as sess:
    ## 定义训练集和测试集日志writer
    logdir = './tmp/log'
    train_writer = tf.summary.FileWriter(logdir + '/train-conv', sess.graph)
    test_writer = tf.summary.FileWriter(logdir + '/test-conv')

    ## 初始化全局变量
    sess.run(tf.global_variables_initializer())

    ## 定义模型checkpoint保存对象, 检查路径是否存在, 如果存在就从checkpoint文件中恢复
    saver = tf.train.Saver(tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES))
    ckpt_path = './tmp/mnist/model.ckpt'
    if os.path.exists(os.path.dirname(ckpt_path)):
        saver.restore(sess, ckpt_path)
    else:
        os.mkdir(os.path.dirname(ckpt_path))

    ## 训练模型
    for _ in range(10000):
        xs, ys = mnist.train.next_batch(100)
        loss, i, _, _ = sess.run([cross_entropy, step, train_op, update_op], feed_dict={
            x: xs,
            label: ys
        })

        if i % 100 == 0:
            ## 评估模型在训练集和测试集上的效果,并将日志保存到日志文件中
            acc_train, summary = sess.run([acc, merged], feed_dict={x: mnist.train.images, label: mnist.train.labels})
            train_writer.add_summary(summary, global_step=i)

            acc_test, summary = sess.run([acc, merged], feed_dict={x: mnist.test.images, label: mnist.test.labels})
            test_writer.add_summary(summary, global_step=i)


            print i, 'loss', loss, \
                'train acc', acc_train, \
                'test acc', acc_test

            ## 保存模型
            saver.save(sess, ckpt_path)
