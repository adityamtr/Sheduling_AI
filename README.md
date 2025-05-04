# Shceduling_AI

## Installation

user requirements file provided at root level to install python packages

cmd: pip install -r requirements.txt

### Note:
1. If you wish to use gpu then you will have to install cuda compiled torch
2. use cmd "nvidia-smi" to identify your gpu supported cuda version and then replace the same in following command at end<br><br>
    
    +-----------------------------------------------------------------------------------------+
    | NVIDIA-SMI 572.83                 Driver Version: 572.83         CUDA Version: 12.8     |
    |-----------------------------------------+------------------------+----------------------+
    | GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
    | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
    |                                         |                        |               MIG M. |
    |=========================================+========================+======================|
    
    <br>for CUDA Version 12.8<br>
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128<br><br>
    
    If you have different version replace that at last of link "/cu<version without .>"

## Setup

Run setup.py (this wll load required LLM from huggingface to local dir models)
