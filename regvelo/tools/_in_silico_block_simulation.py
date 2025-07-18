import torch
import pandas as pd
import numpy as np
from anndata import AnnData

from .._model import REGVELOVI

def in_silico_block_simulation(
        model: str,
        adata: AnnData,
        TF: str,
        effects: float = 0,
        cutoff: float = 1e-3,
        customized_GRN: torch.Tensor = None
        ) -> tuple[AnnData, REGVELOVI]:
    r"""Perform an in silico transcription factor (TF) regulon knock-out by modifying the gene regulatory network (GRN)
    in a trained RegVelo model.

    Parameters
    ----------
    model
        Path to the saved RegVelo model.
    adata
        Annotated data matrix.
    TF
        Transcription factor to be knocked out (its regulon will be silenced).
    effect
        Coefficient used to replace weights in GRN
    cutoff
        Threshold to determine which links in the GRN are considered active and should be muted.
    customized_GRN
        A custom perturbed GRN weight matrix to directly replace the original GRN.

    Returns
    -------
    
    - Perturbed annotated data object with RegVelo outputs.
    - RegVelo model with modified GRN.
    """

    reg_vae_perturb = REGVELOVI.load(model,adata)

    perturb_GRN = reg_vae_perturb.module.v_encoder.fc1.weight.detach().clone()

    if customized_GRN is None:
        perturb_GRN[(perturb_GRN[:,[i == TF for i in adata.var.index]].abs()>cutoff).cpu().numpy().reshape(-1),[i == TF for i in adata.var.index]] = effects
        reg_vae_perturb.module.v_encoder.fc1.weight.data = perturb_GRN
    else:
        device = perturb_GRN.device
        customized_GRN =  customized_GRN.to(device)
        reg_vae_perturb.module.v_encoder.fc1.weight.data = customized_GRN
    
    adata_target_perturb = reg_vae_perturb.add_regvelo_outputs_to_adata(adata = adata)
    
    return adata_target_perturb, reg_vae_perturb