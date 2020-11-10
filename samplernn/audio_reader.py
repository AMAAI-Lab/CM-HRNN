import os
import re
import threading
import sys
import copy
import numpy as np
import tensorflow as tf
import glob
import argparse
from lookup_table import rhythm_to_index,decode_rhythm

class AudioReader(object):

    def __init__(self,coord, args, queue_size=16):
        self.audio_dir = args.data_dir
        self.validation_dir = args.val_data_dir
        self.piano_dim = args.bar_channel + args.chord_channel + args.rhythm_channel+ args.note_channel
        self.note_channel = args.note_channel
        self.rhythm_channel = args.rhythm_channel
        self.chord_channel = args.chord_channel
        self.bar_channel = args.bar_channel
        self.coord = coord
        self.seq_len = args.seq_len
        self.big_frame_size = args.big_frame_size
        self.frame_size = args.frame_size
        self.mode_choice = args.mode_choice
        self.if_cond = True if args.if_cond=="cond" else False
        self.threads = []
        self.X = tf.placeholder(dtype=tf.float32, shape=None)
        self.Y = tf.placeholder(dtype=tf.float32, shape=None)
        self.rm_tm = tf.placeholder(dtype=tf.float32, shape=None)
        if self.mode_choice!="ad_rm2t":
            if self.if_cond:
                self.queue = tf.PaddingFIFOQueue(
                        capacity = queue_size, dtypes=[tf.float32, tf.float32], shapes=[(None, self.piano_dim), (None, self.piano_dim-self.chord_channel)])
            else:
                self.queue = tf.PaddingFIFOQueue(
                    capacity = queue_size, dtypes=[tf.float32, tf.float32], shapes=[(None, self.piano_dim-self.chord_channel), (None, self.piano_dim-self.chord_channel)])  
            
            self.enqueue = self.queue.enqueue([self.X, self.Y])
        else:
            if self.if_cond:
                self.queue = tf.PaddingFIFOQueue(
                        capacity = queue_size, dtypes=[tf.float32, tf.float32, tf.float32], shapes=[(None, self.piano_dim), (None, self.piano_dim-self.chord_channel), (None, self.rhythm_channel)])
            else:
                self.queue = tf.PaddingFIFOQueue(
                    capacity = queue_size, dtypes=[tf.float32, tf.float32, tf.float32], shapes=[(None, self.piano_dim-self.chord_channel), (None, self.piano_dim-self.chord_channel), (None, self.rhythm_channel)])  
            
            self.enqueue = self.queue.enqueue([self.X, self.Y, self.rm_tm])
    def dequeue(self, num_elements):
        output = self.queue.dequeue_many(num_elements)
        return output

    def encode_npy(self, mid_files):
        npy_lst = []
        for mid_file in mid_files:
            mid = np.load(mid_file)
            npy_lst.append(mid)
            #print(mid_file, mid.shape)
        print("encoding........FINISHED!")
        return npy_lst

    def find_remaining_time(self,ipt,prev_len):
        #ipt [len, dim]
        #opt [len - prev_len, rhythm_channel]
        out_lst = []
        for t in range(prev_len, len(ipt)):
            #print("hey",t)
            current_time = t
            prev_time = t-1
            while np.argmax(ipt[prev_time][:self.bar_channel])!=1:
                prev_time -= 1
            duration_accumulated = 0
            for idx in range(prev_time,current_time):
                duration_raw = np.argmax(ipt[idx][self.bar_channel+self.chord_channel: self.bar_channel+self.chord_channel+self.rhythm_channel])
                duration = decode_rhythm(duration_raw,ignore_bar_event = True)
                duration_accumulated+=duration
            duration_left_raw = duration_accumulated
            rm_duration_idx = rhythm_to_index(duration_left_raw)
            duration_left = np.zeros((self.rhythm_channel,))
            duration_left[rm_duration_idx,] = 1

            out_lst.append(duration_left) #in the end will be [(1,16),(1,16) ]
        output = np.stack(out_lst, axis = 0)
        return output
        

    def prepare_each_data(self, audio, sess = None, if_train= True):
        if not self.if_cond:
            #audio = audio[:, self.chord_channel:]
            audio = np.delete(audio,np.s_[self.bar_channel:self.bar_channel+self.chord_channel],axis=1)
        ##prepare dataset based on mode choice, IF_COND, return X, Y

        if self.mode_choice == "nosamplernn": #x: (framesize, dim), y: (1, dim)

            num_iter = audio.shape[0]-self.frame_size 
            seq_list_tmp = [] 
            ground_truth_tmp = []
            for i in range(num_iter):
                seq = audio[ i:i+self.frame_size, :]
                seq_list_tmp.append(seq)  
                if self.if_cond:
                    gt = np.delete([audio[ i+self.frame_size, :]],np.s_[self.bar_channel:self.bar_channel+self.chord_channel],axis=1)
                else:
                    gt = [audio[ i+self.frame_size, :]]
                ground_truth_tmp.append(gt)
            X_y_lst = zip(seq_list_tmp, ground_truth_tmp)
            if if_train:
                for X_y in X_y_lst:
                    sess.run(self.enqueue,feed_dict={self.X: X_y[0], self.Y: X_y[1]})
            else:
                return X_y_lst
        elif self.mode_choice == "bar_note": #x: (len, dim), y: (len-frame-big_frame, dim)
            seq_list_tmp = [] 
            ground_truth_tmp = []
            while len(audio) >= self.seq_len:
                X = audio[:self.seq_len, :]
                #y = X[self.big_frame_size+self.frame_size:,:]
                y = X[self.big_frame_size:,:]
                if self.if_cond:
                    gt = np.delete(y,np.s_[self.bar_channel:self.bar_channel+self.chord_channel],axis=1)
                else:
                    gt = y
                seq_list_tmp.append(X)  
                ground_truth_tmp.append(gt)
                audio = audio[self.seq_len:, :]
            X_y_lst = zip(seq_list_tmp, ground_truth_tmp)
            if if_train:
                for X_y in X_y_lst:
                    sess.run(self.enqueue,feed_dict={self.X: X_y[0], self.Y: X_y[1]})
            else:
                return X_y_lst
        elif self.mode_choice == "note": #x: (len, dim), y: (len-frame, dim)
            seq_list_tmp = [] 
            ground_truth_tmp = []
            while len(audio) >= self.seq_len:
                X = audio[:self.seq_len, :]
                y = X[self.frame_size:,:]
                if self.if_cond:
                    gt = np.delete(y,np.s_[self.bar_channel:self.bar_channel+self.chord_channel],axis=1)
                else:
                    gt = y
                seq_list_tmp.append(X)  
                ground_truth_tmp.append(gt)
                audio = audio[self.seq_len:, :]
            X_y_lst = zip(seq_list_tmp, ground_truth_tmp) #[(X,y), (X,y) ]
            if if_train:
                for X_y in X_y_lst:
                    sess.run(self.enqueue,feed_dict={self.X: X_y[0], self.Y: X_y[1]})  
            else:
                return X_y_lst
        elif self.mode_choice=="ad_rm2t":
            #make sure data starts with a bar event
            for i in range(len(audio)):
                if np.argmax(audio[i][:self.bar_channel])==1:
                    #print("is bar",audio[i][:self.bar_channel])
                    trim_index = i
                    break
            audio = audio[trim_index:]

            seq_list_tmp = [] 
            ground_truth_tmp = []
            rm_tm_tmp = []
            while len(audio) >= self.seq_len:

                #make sure X starts with a bar event
                X = audio[:self.seq_len, :]

                #y is okay, no pre-process needed
                y = X[self.frame_size:,:]
                if self.if_cond:
                    gt = np.delete(y,np.s_[self.bar_channel:self.bar_channel+self.chord_channel],axis=1)
                else:
                    gt = y
                #process remaining time lst
                
                rm_time_output = self.find_remaining_time(X, prev_len = self.frame_size) #(len-framesize, rhythm_channel)
                seq_list_tmp.append(X)  
                ground_truth_tmp.append(gt)
                rm_tm_tmp.append(rm_time_output)
                audio = audio[self.seq_len:, :]
            X_y_lst = zip(seq_list_tmp, ground_truth_tmp, rm_tm_tmp) #[(X,y,z), (X,y,z) ]


            if if_train:
                for X_y in X_y_lst:
                    sess.run(self.enqueue,feed_dict={self.X: X_y[0], self.Y: X_y[1], self.rm_tm: X_y[2]})  
            else:
                return X_y_lst            
    
    def thread_main2(self, sess):
        stop = False
        mid_files = glob.glob(self.audio_dir+'/*.npy')
        npy_list = self.encode_npy(mid_files)
        while not stop:
            for i,npy_file in enumerate(npy_list):
                audio = npy_file
                if self.coord.should_stop():
                    stop = True
                    break
                
                self.prepare_each_data(audio, sess, if_train = True)
                


    def start_threads(self, sess, n_threads=1):
        for _ in range(n_threads):
            thread = threading.Thread(target=self.thread_main2, args=(sess,))
            thread.daemon = True  # Thread will close when parent quits.
            thread.start()
            self.threads.append(thread)
        return self.threads
    def get_validation_data(self):
        val_files = glob.glob(self.validation_dir+'/*.npy')
        val_list = self.encode_npy(val_files) 
        piece_lst = [] #[(x,y),(x, y), x(y)]
        for val_data in val_list:      
            X_y_lst = self.prepare_each_data(val_data, if_train = False) #[(x,y),(x, y), (x,y)]
            piece_lst += X_y_lst
        if self.mode_choice!="ad_rm2t":
            X_lst, y_lst = zip(*piece_lst)
            X = np.stack(X_lst, axis = 0)
            y = np.stack(y_lst, axis = 0)
            return X, y
        else:
            X_lst, y_lst,z_lst = zip(*piece_lst)
            X = np.stack(X_lst, axis = 0)
            y = np.stack(y_lst, axis = 0)
            z = np.stack(z_lst, axis = 0)
            return X, y, z        
        


if __name__=='__main__':

    parser = argparse.ArgumentParser(description='SampleRnn example network')
    parser.add_argument('--data_dir', type=str,default="../data_inC_bar_pad/test_folder")
    parser.add_argument('--val_data_dir',type=str,default = "../data_inC_bar_pad/test_folder")                  

    parser.add_argument('--seq_len',          type=int, default = 64)
    parser.add_argument('--big_frame_size',   type=int, default = 32)
    parser.add_argument('--frame_size',       type=int, default = 16)

    parser.add_argument('--mode_choice', choices=['bar_note', 'nosamplernn','note',"ad_rm2t", "ad_rm3t"], type = str,default="ad_rm2t")
    parser.add_argument('--if_cond',type=str, choices=['cond','no_cond'], default = "cond")
    parser.add_argument('--note_channel',type=int, default = 130)
    parser.add_argument('--rhythm_channel',type=int, default = 16)
    parser.add_argument('--chord_channel',type=int, default = 49)
    parser.add_argument('--bar_channel',type=int, default = 2)
    args =  parser.parse_args()




    tf_config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False)
    tf_config.gpu_options.allow_growth = True
    coorder = tf.train.Coordinator()
    sess = tf.Session(config=tf_config)
    init = tf.global_variables_initializer()
    sess.run(init)
    threads = tf.train.start_queue_runners(sess=sess, coord=coorder)
    reader = AudioReader(coord = coorder, args = args)
    print('init finish')
    reader.start_threads(sess)
    print('threads started')
    audio_batch = reader.dequeue(4)
    print('deququed')
    if args.mode_choice!="ad_rm2t":
        X_train, y_train = sess.run(audio_batch)
        X, y = reader.get_validation_data()
        print("dadasdas",X_train.shape, y_train.shape)
        print("asdasdsa", X.shape,y.shape)
    else:
        X_train, y_train,rm_time = sess.run(audio_batch)
        X, y,rm_time_val = reader.get_validation_data()
        np.save("X.npy",X_train)
        np.save("y.npy",y_train)
        np.save("rm.npy",rm_time)      
