#!/bin/bash
python train_w_mode_switch_sgpu.py \
	--data_dir=data_inC_bar_pad_mged_split/train/merged\
	--val_data_dir=data_inC_bar_pad_mged_split/val/merged\
	--big_frame_size=16 \
	--frame_size=16 \
	--rnn_type=LSTM \
	--dim=256 \
	--n_rnn=2 \
	--batch_size=512 \
	--optimizer=adam \
	--num_gpus=1\
    --if_cond=cond\
    --mode_choice=2t_fc\
	--piano_dim=197\
	--note_channel=130\
	--rhythm_channel=16\
	--seq_len=128\
	--chord_channel=49\
	--drop_out=0.5\
	--alpha1=0.4\
	--alpha2=0.3\
	--birnndim=128