'''
SuperdropNet code for evaluation only

Adapated from Shivani Sharma and Caroline Arnold: https://github.com/Hereon-KSN/dkrz-hereon-icon-superdropnet

Release tag: https://github.com/Hereon-KSN/dkrz-hereon-icon-superdropnet/releases/tag/v0.1.0

Background information:

https://arxiv.org/pdf/2402.18354
'''

import os
import numpy as np
import torch
import torch.nn as nn

class plNetwork(torch.nn.Module):
    """SuperdropNet network."""
    def __init__(
        self,
        act,
        n_layers=5,
        ns=200,
        out_features=4,
        depth=9,
        p=0.25,
        use_batch_norm=False,
        use_dropout=False,
    ):
        """Initialize SuperdropNet network

        Args:
            act (torch.nn): activation function from torch.nn. TODO check type
            n_layers (int, optional): Number of layers. Defaults to 5.
            ns (int, optional): Number of neurons per layer. Defaults to 200.
            out_features (int, optional): Number of output features. Defaults to 4.
            depth (int, optional): Number of input features. Defaults to 9.
            p (float, optional): Dropout probability. Defaults to 0.25.
            use_batch_norm (bool, optional): If True, use batch norm layers. Defaults to False.
            use_dropout (bool, optional): If True, use dropout layers. Defaults to False.
        """    

        super().__init__()

        self.layers = []
        self.layer_size = []

        in_features = depth
        for i in range(n_layers):

            self.layers.append(nn.Linear(in_features, ns))
            # nn.init.kaiming_normal_(self.layers[i].weight, mode='fan_out')
            if use_batch_norm:
                self.layers.append(nn.BatchNorm1d(ns))
            in_features = ns

        self.layers.append(nn.Linear(ns, out_features))
        self.layers = nn.ModuleList(self.layers)
        self.dropout = nn.Dropout(p)
        self.activation = act
        self.n_layers = n_layers
        self.use_dropout = use_dropout

    def _forward_impl(self, x):
        """Implements the forward pass through the network layers.
        
        Args:
            x (torch.Tensor): Input tensor
            
        Returns:
            torch.Tensor: Output after passing through all layers
        """
        # Track if we're on last layer
        last_layer_idx = len(self.layers) - 1

        # Single pass through all layers
        for i, layer in enumerate(self.layers):
            x = layer(x)
            # Only apply activation and dropout to hidden layers
            if i < last_layer_idx:
                x = self.activation(x)
                if self.use_dropout:
                    x = self.dropout(x)

        return x

    def forward(self, x):
        '''Applies the forward pass of the network.'''
        return self._forward_impl(x)

class SuperdropNetInferenceModel(torch.nn.Module):
    '''SuperdropNet model for evaluation only. Adapted from the original LightningModule.'''
    def __init__(
        self,
        updates_mean,
        updates_std,
        inputs_mean,
        inputs_std,
        act=nn.ReLU(),
        n_layers=3,
        ns=200,
        depth=9,
        p=0.25,
        moment_scheme=2,
        use_batch_norm=False,
        use_dropout=False,
        pretrained_path=None
    ):
        """Initialize SuperdropNet model for evaluation only.

        Args:
            updates_mean (_type_): Mean to scale updates. TODO check type
            updates_std (_type_): Standard deviation to scale updates. TODO check type
            inputs_mean (_type_): Mean to scale inputs. TODO check type
            inputs_std (_type_): Standard deviation to scale inputs. TODO check type
            act (_type_, optional): Activation function. Defaults to nn.ReLU().
            n_layers (int, optional): Number of layers. Defaults to 3.
            ns (int, optional): Number of neurons. Defaults to 200.
            depth (int, optional): Number of input features. Defaults to 9.
            p (float, optional): Dropout probability. Defaults to 0.25.
            moment_scheme (int, optional): Order of moment scheme. Defaults to 2.
            use_batch_norm (bool, optional): If True, use batch norm. Defaults to False.
            use_dropout (bool, optional): If True, use dropout. Defaults to False.
            pretrained_path (_type_, optional): Path to checkpoint with pretrained weights. Defaults to None.
        """    
        super().__init__()
        self.moment_scheme = moment_scheme
        self.out_features = moment_scheme * 2

        self.updates_std = updates_std.float()
        self.updates_mean = updates_mean.float()
        self.inputs_mean = inputs_mean.float()
        self.inputs_std = inputs_std.float()

        self.pretrained_path = pretrained_path

        self.model = plNetwork(
            act, n_layers, ns, self.out_features, depth, p, use_batch_norm, use_dropout
        )

        if self.pretrained_path is None:
            raise ValueError('Pretrained path is required for evaluation.')
        else:
            if torch.cuda.is_available():
                saved_ckpt = torch.load(self.pretrained_path)
            else:
                saved_ckpt = torch.load(self.pretrained_path, map_location=torch.device('cpu'))
            state_dict = saved_ckpt['state_dict']
            # remove 'model.' from the keys
            new_state_dict = {}
            for k, v in state_dict.items():
                new_state_dict[k.replace('model.', '')] = v
            self.model.load_state_dict(new_state_dict)

        # This model is only for inference
        self.model.eval()

    def test_step(self, initial_moments):
        """Test step for SuperdropNet model. For moment-wise evaluation as used for ODE solve.

        Args:
            initial_moments (torch.Tensor): Input moments.

        Returns:
            torch.Tensor: Updates. TODO check
        """
        with torch.no_grad():
            preds = self.model(initial_moments.float())
        return preds

class WrappedSuperdropNet(torch.nn.Module):
    '''
    Wraps the existing SuperdropNet implementation in one torch.nn.Module for use with FTorch.
    
    This version is TorchScript-compatible by removing NumPy operations.
    '''
    def __init__(self, pretrained_path: str, timestep=20):
        '''
        Initialize WrappedSuperdropNet with hard coded mean and std values for input and updates.
        
        Args:
            pretrained_path (str): Path to the pretrained model.
            timestep : Timestep to update the weights with.
        '''
        super().__init__()
        
        # Convert hard-coded numpy arrays to torch tensors
        self.register_buffer(
            "inputs_mean", 
            torch.tensor([[0.0002621447787797809, 51128093.51524663,
                           0.0003302890736022656, 5194.251154308974,
                           0.5566250557023539, 4.8690682855354596e-12,
                           0.0005924338523807814, 1.0848856769219835e-05,
                           2.0193905073168525]])
        )
        self.register_buffer(
            "inputs_std", 
            torch.tensor([[0.0003865559774857862, 86503916.13808665,
                           0.00041369562655559327, 19127.947970150628,
                           0.46107363560819126, 3.873092422358367e-12,
                           0.00042887039563850967, 1.920461805101116e-06,
                           1.3098055608321857]])
        )
        self.register_buffer(
            "updates_mean", 
            torch.tensor([[-8.527820407019667e-08, -13961.459867976775,
                           8.527678028525988e-08, 0.010221931180955181]])
        )
        self.register_buffer(
            "updates_std", 
            torch.tensor([[3.600841676033818e-07, 55095.904252313965,
                           3.6008419243808887e-07, 68.6678997504877]])
        )
        
        # the actual model
        self.backbone = SuperdropNetInferenceModel(
            self.updates_mean, self.updates_std, self.inputs_mean, self.inputs_std,
            pretrained_path=pretrained_path
        )

        # class attribute assigned in create_input.
        self.lo_arr = None
        self.timestep = timestep

    def forward(self, all_moments_in: torch.Tensor) -> torch.Tensor:
        '''
        Replaces simulation_forecast.test(). Called from ICON using FTorch.
        
        From ICON cloud microphysics, we pass a so-called ik-slice. Its dimensions are
        - dim_i: Horizontal dimension of the ik-slice. Matches nproma.
        - dim_k: Vertical dimension of the ik-slice.
        - 4 moments in the order of: Lc, Nc, Lr, Nr (cloud%q, cloud%n, rain%q, rain%n).

        With FTorch, we do not need to worry about transposing the input tensor when switching between
        row-major (Fortran) and column-major (C) memory layout. FTorch handles this automatically.

        This implies we only need to reshape during the forward call
        -----
        ICON slice: dim_i x dim_k x moments
        SuperdropNet expects: dim_ik  x moments
        SuperdropNet returns: dim_ik x moments
        ICON expects: dim_i x dim_k x moments
        -----

        Args:
          all_moments_in (torch.Tensor): Initial moments passed from ICON. Shape: dim_i x dim_k x moments

        Returns:
          moments_out (torch.Tensor): Updated moments to be passed to ICON. Shape: dim_i x dim_k x moments
        '''

        # Store original shape
        dim_i, dim_k, dim_m = all_moments_in.shape

        # Swap axes and flatten ik dimension
        # dim_i x dim_k x moments -> dim_ik x moments
        all_moments_in = all_moments_in.reshape(-1, dim_m)

        # Create input for the model
        inputs = self.create_input(all_moments_in)

        # Run the model for the update
        predictions_updates = self.backbone.test_step(inputs)
        
        # Un-scale updates
        updates = (predictions_updates * self.updates_std) + self.updates_mean
        
        # Calculate output moments from input moments and updates
        moments_out = all_moments_in[:, :4] + (updates * self.timestep)
        
        moments_out = self.check_preds(moments_out, all_moments_in)
        
        # Reshape for ICON: dim_ik x moments -> dim_i x dim_k x moments
        moments_out = moments_out.reshape(dim_i, dim_k, dim_m)
        return moments_out

    def create_input(self, all_moments_in: torch.Tensor) -> torch.Tensor:
        '''
        Create input for SuperdropNet by concatenating extra features.
        
        Returns:
          inputs (torch.Tensor)
        '''

        # xc: average mass of cloud droplets (Lc / Nc)
        xc = all_moments_in[:, 0] / (all_moments_in[:, 1] + 1e-8)
        self.lo_arr = all_moments_in[:, 2] + all_moments_in[:, 0]

        # Avoid division by zero; torch.where returns 0 if denominator is zero
        tau = torch.where(self.lo_arr != 0, all_moments_in[:, 2] / self.lo_arr, 0)
        
        # Create rm and nu tensors
        rm = torch.full_like(self.lo_arr, 13e-6)
        nu = torch.ones_like(self.lo_arr)
        
        # Concatenate model parameters along the last dimension
        model_params = torch.stack((self.lo_arr, rm, nu), dim=1)
        inputs = torch.cat((all_moments_in, tau.unsqueeze(1), xc.unsqueeze(1), model_params), dim=1)
        
        # scale inputs; note: inputs_mean and inputs_std are buffers/tensors with shape [1, num_features]
        inputs = (inputs - self.inputs_mean) / self.inputs_std
        return inputs

    def check_preds(self, moments_out: torch.Tensor, all_moments_in: torch.Tensor) -> torch.Tensor:
        """Performs sanity checks and adjustments on predicted moments.
        
        This method ensures physical consistency of the predicted moments by:
          1. Enforcing non-negative moments
          2. Irreversibility, only cloud to rain
          3. Maintaining liquid water conservation between cloud and rain water
          4. Setting output moments to zero when input moments were negligible
        
        Args:
            moments_out (torch.Tensor): Predicted moments, shape (batch_size, 4)
            all_moments_in (torch.Tensor): Input moments, shape (batch_size, 4)
            
        Returns:
            torch.Tensor: Adjusted moments.
        """
        # Enforce non-negative moments
        moments_out = torch.clamp(moments_out, min=0.0)

        # Irreversibility constraint:
        # Accretion, autoconversion, and evaporation should not lead to an increase in qc or a decrease in qr.
        # mask out cases where delta qc > 0 | delta qr < 0
        mask_delta = (moments_out[:, 0] - all_moments_in[:, 0]) > 0 
        moments_out[mask_delta, 0] = all_moments_in[mask_delta, 0]

        mask_delta_qnc = (moments_out[:, 1] - all_moments_in[:, 1]) > 0
        moments_out[mask_delta_qnc, 1] = all_moments_in[mask_delta_qnc, 1]

        # mass conservation constraint:
        moments_out[:, 2] = self.lo_arr - moments_out[:, 0]

        # Create a mask where the first input moment (qc) is < q_crit=1.e-9
        #  AND qr < qr_crit = 0
        mask = ((all_moments_in[:, 0] < 1e-9) & (all_moments_in[:, 2] == 0.0)).unsqueeze(-1)
        moments_out = torch.where(mask, all_moments_in, moments_out)
        return moments_out
