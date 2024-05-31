# Hierarchical Recurrent Neural Networks for Conditional Melody Generation with Long-term Structure

The rise of deep learning technologies has quickly advanced many fields, including that of generative music systems. There exist a number of systems that allow for the generation of good sounding short snippets, yet, these generated snippets often lack an overarching, longer-term structure. In this work, we propose CM-HRNN: a conditional melody generation model based on a hierarchical recurrent neural network. This model allows us to generate melodies with long-term structures based on given chord accompaniments. We also propose a novel, concise event-based representation to encode musical lead sheets while retaining the notes' relative position within the bar with respect to the musical meter. With this new data representation, the proposed architecture can simultaneously model the rhythmic, as well as the pitch structures in an effective way. Melodies generated by the proposed model were extensively evaluated in quantitative experiments as well as a user study to ensure the musical quality of the output as well as to evaluate if they contain repeating patterns. We also compared the system with the state-of-the-art AttentionRNN. This comparison shows that melodies generated by CM-HRNN contain more repeated patterns (i.e., higher compression ratio) and a lower tonal tension (i.e., more tonally concise). Results from our listening test indicate that CM-HRNN outperforms AttentionRNN in terms of long-term structure and overall rating.

## Reference

If you use this work, please cite accordingly: 

Guo Z, Makris D., Herremans D..  2021.  [Hierarchical Recurrent Neural Networks for Conditional Melody Generation with Long-term Structure](https://arxiv.org/abs/2102.09794). Proceedings of the International Joint Conference on Neural Networks (IJCNN). 



## Getting Started

### Results and data format
Kindly check the result demo folder for the generated results. For input data format check the npy files in the result demo folder. 

### Dependencies

* tensorflow 1.14
* midiutil
* numpy
* pandas

### Getting started

* Training script: run_xx.sh; Generation script: generate_xx.sh; Evaluation script: comp_successbar_ratio.py
* 2t_fc: 2 tier without acc. time info;
* 3t_fc: 3 tier without acc. time info;
* adrm2t_fc: 2 tier with acc. time info;
* adrm3t_fc: 3 tier with acc. time info;
* adrm3t_fc_rs: 3 tier with acc. time info with residual conn.;
* bln_attn_fc: baseline attentionrnn;
* bln_fc: baseline vanila rnn;

