# coding: utf-8
'''Model utils'''
import gensim
from gensim.models.keyedvectors import KeyedVectors

import keras
from keras import regularizers
from keras.layers import Dense, Dropout
from keras.layers import Input, Embedding
from keras.layers import Conv1D, GlobalMaxPooling1D, MaxPooling1D
from keras.layers.merge import Concatenate, Dot
from keras.models import Sequential, Model

import numpy as np

# embed_dim = 50
# max_ques_len = 20
# vocab_size = 1000
# max_ans_len = 40
# embedding = np.random.rand(1000, 50)


def load_embeddings(embedding_file, vocab):
    '''Load pre-learnt word embeddings.
    Return: embedding: embedding matrix with dim |vocab| x dim
            dim: dimension of the embeddings
            rand_count: number of words not in trained embedding
    '''
    word_vectors = KeyedVectors.load_word2vec_format(
        embedding_file, binary=True)
    # Need to use the word vectors to make embeddings matrix
    # Get dimension for any word embedding
    dim = word_vectors['apple'].shape[0]
    
    # Initialize an embedding of |vocab| x dim
    # word -> embedding
    embedding = np.zeroes((len(vocab, dim)))
    # Take random values
    rand_vec = np.random.uniform(-0.25, 0.25, dim)
    # Count of words not having representations in our embedding file
    rand_count = 0

    for key, value in vocab.iteritems():
        embedding[value] = word_vectors.get(key, rand_count)
        if key not in word_vectors:
            rand_count += 1

    print 'Number of words not in trained embedding: %d' %(rand_count)
    return embedding, dim, rand_count


def cnn_model(embed_dim, max_ques_len, max_ans_len, vocab_size, embedding):
    '''Neural architecture as mentioned in the original paper.'''
    # Prepare layers for Question
    input_q = Input(shape=(max_ques_len,))
    # print input_q.name
    # we will load embedding values from corpus here.
    embed_q = Embedding(input_dim=vocab_size, output_dim=embed_dim,
                        input_length=max_ques_len,
                        weights=[embedding], trainable=False)(input_q)
    # Padding means, if input size is 32x32, output will also be 32x32, i.e,
    # the dimensions will not reduce
    conv_q = Conv1D(filters=100, kernel_size=5, strides=1, padding='same',
                    activation='relu',
                    kernel_regularizer=regularizers.l2(1e-5))(embed_q)
    # also referenced as x(q) in paper
    pool_q = GlobalMaxPooling1D()(conv_q)



    # Prepare layers for Answer
    input_a = Input(shape=(max_ans_len,))
    # print input_a.name
    embed_a = Embedding(input_dim=vocab_size, output_dim=embed_dim,
                        input_length=max_ans_len,
                        weights=[embedding], trainable=False)(input_a)
    conv_a = Conv1D(filters=100, kernel_size=5, strides=1, padding='same',
                    activation='relu',
                    kernel_regularizer=regularizers.l2(1e-5))(embed_a)
    pool_a = GlobalMaxPooling1D()(conv_a)



    # M or the similarity layer here
    # Paper: x_d_dash = M.x_d
    x_a = Dense(100, use_bias=False,
                kernel_regularizer=regularizers.l2(1e-4))(pool_a)
    sim = Dot(axes=-1)([pool_q, x_a])



    # Combine Question, sim and Answer pooled outputs.
    join_layer = keras.layers.concatenate([pool_q, sim, pool_a])



    # Using relu here too? Not mentioned in the paper.
    hidden_layer = Dense(201,
                         kernel_regularizer=regularizers.l2(1e-4))(join_layer)
    hidden_layer = Dropout(0.5)(hidden_layer)

    # Final Softmax Layer, add regularizer here too?
    softmax = Dense(1, activation='softmax')(hidden_layer)



    model = Model(inputs=[input_q, input_a], outputs=softmax)
    print model.summary()

    model.compile(optimizer='Adadelta',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    return model
    # model.fit([data_a, data_b], labels, epochs=10)


def main():
    '''Main'''
    cnn_model(50, 33, 40, 5000, np.random.rand(5000, 50))


if __name__ == '__main__':
    main()
