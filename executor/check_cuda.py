import torch

def check_cuda():
    if torch.cuda.is_available():
        print("CUDA is available!")
        print("CUDA device count: ", torch.cuda.device_count())
        print("Current CUDA device: ", torch.cuda.current_device())
        print("CUDA device name: ", torch.cuda.get_device_name(torch.cuda.current_device()))
    else:
        print("CUDA is not available.")

check_cuda()