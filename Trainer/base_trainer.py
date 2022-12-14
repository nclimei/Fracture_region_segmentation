# from tqdm import tqdm
import random
import torch
import numpy as np
import logging
import torch.nn.functional as F
from sklearn.metrics import (
    precision_recall_fscore_support as prf,
    accuracy_score,
    roc_auc_score,
)
import os
import torch.nn as nn
import time
from Utils import utils

class Base_Trainer:
    
    def __init__(self, cfg_proj, cfg_m, name):
        self.name = name
        self.cfg_proj = cfg_proj
        self.cfg_m = cfg_m
        self.init_env(name)

    def init_env(self, name, log_folder = "Checkpoint"):
        #init device
        use_cuda = torch.cuda.is_available()
        self.device = torch.device("cuda" if use_cuda else "cpu")
        self.cfg_m.insert("device", self.device)
        print("Using device - ", self.device)
        torch.backends.cudnn.benchmark = True
        #init seed
        if self.cfg_proj.seed is not None:
            torch.manual_seed(self.cfg_proj.seed)
            if use_cuda: torch.cuda.manual_seed(self.cfg_proj.seed)
            np.random.seed(self.cfg_proj.seed)
            random.seed(self.cfg_proj.seed)
        #init log sys
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.log_sub_folder = "%s/log_%s_%s"%(log_folder, name, self.cfg_proj.flag_time)
        self.log_id = "log_%s_%s"%(name, self.cfg_proj.flag_time)
        os.makedirs(self.log_sub_folder, exist_ok=True)
        fh = logging.FileHandler('%s/%s.log'%(self.log_sub_folder, self.log_id))
        fh.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)
        self.logger.info("----Setting----")
        for n in self.cfg_m:
            self.logger.info("%s - %s"%(n, self.cfg_m[n]))
        for p in vars(self.cfg_proj):
            self.logger.info("%s - %s"%(p, getattr(self.cfg_proj, p)))
        self.logger.info("----log----")


    def load_ckp(self, model, optimizer, lr_scheduler, contain_t):

        model_to_load = self.cfg_proj.model_to_load if self.cfg_proj.model_to_load is not None else self.cfg_proj.flag_time
        file_ns = utils.getFilesInSubPath(model_to_load, folder = "Checkpoint", suffix = "pt", contain_t = contain_t)

        assert len(file_ns) == 1
        checkpoint = torch.load(file_ns[0])
        try:
            model.load_state_dict(checkpoint['net'])    #, strict=False)  #ignore the unmatched key
        except:
            model.load_state_dict({k.replace('module.',''):v for k,v in checkpoint['net'].items()})
        if optimizer is not None: optimizer.load_state_dict(checkpoint['optimizer'])
        if lr_scheduler is not None: lr_scheduler.load_state_dict(checkpoint['lr_scheduler'])
        epoch_start = checkpoint['epoch']
        str_record = "load ckp - %s, epoch_start = %d" % (file_ns[-1], epoch_start)
        print(str_record)
        self.logger.info(str_record)

        return model, optimizer, lr_scheduler, epoch_start

    def save_ckp(self, model, optimizer, lr_scheduler, epoch, stage):
        state_ckp = {'net':model.state_dict(), 'optimizer':optimizer.state_dict() if optimizer is not None else None, \
                    'lr_scheduler':lr_scheduler.state_dict() if lr_scheduler is not None else None, 'epoch':epoch}
        torch.save(state_ckp, '%s/%s_%s_%s_epoch_%04d.pt'%(self.log_sub_folder, self.cfg_proj.backbone, stage, self.cfg_proj.flag_time, epoch))
        time.sleep(1)
