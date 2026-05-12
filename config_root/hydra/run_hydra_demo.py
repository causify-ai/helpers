#!/usr/bin/env python
"""
This script demonstrates Hydra's key features using config files from
config_example1/ directory.

Features:
1. @hydra.main decorator with config_path
2. CLI overrides
3. Parameter sweeps (multi-run)
4. Config composition (model groups)
5. Both file-based and structured configs (ConfigStore)

Usage examples:
# Install the required dependencies.
docker > sudo /bin/bash -c "(source /venv/bin/activate; pip install hydra-core omegaconf)"

# Run with defaults (uses config_example1/base_config.yaml + model/linear.yaml).
> config_root/hydra/run_hydra_demo.py

# Override parameters.
> config_root/hydra/run_hydra_demo.py model.learning_rate=0.001 training.batch_size=64

# Multi-run with sweeps.
> config_root/hydra/run_hydra_demo.py --multirun model.learning_rate=0.001,0.01,0.1

# Select different model from config group (uses model/xgboost.yaml).
> config_root/hydra/run_hydra_demo.py model=xgboost

# Select random forest model (uses model/rf.yaml).
> config_root/hydra/run_hydra_demo.py model=rf

# Print config without running.
> config_root/hydra/run_hydra_demo.py --cfg job
"""

import logging
from typing import Any, Dict

import hydra
import omegaconf as omgcfg

_LOG = logging.getLogger(__name__)


# #############################################################################
# Pipeline functions
# #############################################################################


def _load_data(cfg: Any) -> Dict[str, Any]:
    """
    Simulate data loading from configuration.

    :param cfg: data configuration (DictConfig or structured config)
    :return: dictionary containing simulated data information
    """
    # Extract data configuration parameters.
    data_path = cfg.data_path
    features = cfg.features
    target = cfg.target
    _LOG.info("Loading data from: %s", data_path)
    _LOG.info("Features: %s", features)
    _LOG.info("Target: %s", target)
    # Simulate loading by returning dummy info.
    data_info = {
        "num_samples": 10000,
        "num_features": len(features),
        "feature_names": features,
    }
    return data_info


def _build_model(cfg: Any) -> Dict[str, Any]:
    """
    Build model based on configuration.

    :param cfg: model configuration (DictConfig or structured config)
    :return: dictionary containing model type and parameters
    """
    # Extract model name: works with both DictConfig and structured config.
    model_name = cfg.name
    _LOG.info("Building model: %s", model_name)
    model_info = {"type": model_name, "params": {}}
    # Configure model-specific parameters.
    if model_name == "linear":
        lr = cfg.learning_rate
        reg = cfg.regularization
        _LOG.info("Learning rate: %s", lr)
        _LOG.info("Regularization: %s", reg)
        model_info["params"] = {"lr": lr, "reg": reg}
    elif model_name == "xgboost":
        n_est = cfg.n_estimators
        depth = cfg.max_depth
        lr = cfg.learning_rate
        _LOG.info("N estimators: %s", n_est)
        _LOG.info("Max depth: %s", depth)
        _LOG.info("Learning rate: %s", lr)
        model_info["params"] = {"n_est": n_est, "depth": depth, "lr": lr}
    elif model_name == "random_forest":
        n_est = cfg.n_estimators
        depth = cfg.max_depth
        _LOG.info("N estimators: %s", n_est)
        _LOG.info("Max depth: %s", depth)
        model_info["params"] = {"n_est": n_est, "depth": depth}
    return model_info


def _train_model(
    cfg: Any,
    data_info: Dict[str, Any],
    model_info: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Train model with given configuration.

    :param cfg: training configuration (DictConfig or structured config)
    :param data_info: data information dictionary
    :param model_info: model information dictionary
    :return: training results dictionary
    """
    # Extract training parameters.
    batch_size = cfg.batch_size
    num_epochs = cfg.num_epochs
    shuffle = cfg.shuffle
    val_split = cfg.validation_split
    _LOG.info("Training configuration:")
    _LOG.info("Batch size: %s", batch_size)
    _LOG.info("Num epochs: %s", num_epochs)
    _LOG.info("Shuffle: %s", shuffle)
    _LOG.info("Validation split: %s", val_split)
    # Calculate training metrics.
    num_batches = data_info["num_samples"] // batch_size
    _LOG.info("Total batches per epoch: %s", num_batches)
    # Return simulated training results.
    training_results = {
        "final_loss": 0.0123,
        "best_epoch": 85,
        "model_type": model_info["type"],
    }
    return training_results


def _run_pipeline(cfg: omgcfg.DictConfig) -> None:
    """
    Run the complete pipeline.

    :param cfg: complete system configuration
    """
    pipeline_name = cfg.pipeline_name
    output_dir = cfg.output_dir
    _LOG.info("=" * 80)
    _LOG.info("Starting pipeline: %s", pipeline_name)
    _LOG.info("=" * 80)
    # Print full resolved config for debugging.
    _LOG.info("\nComplete Configuration:")
    _LOG.info("\n%s", omgcfg.OmegaConf.to_yaml(cfg))
    # Execute pipeline: load data, build model, train model.
    _LOG.info("\n" + "=" * 80)
    _LOG.info("STEP 1: Load Data")
    _LOG.info("=" * 80)
    data_info = _load_data(cfg.data)
    _LOG.info("\n" + "=" * 80)
    _LOG.info("STEP 2: Build Model")
    _LOG.info("=" * 80)
    model_info = _build_model(cfg.model)
    _LOG.info("\n" + "=" * 80)
    _LOG.info("STEP 3: Train Model")
    _LOG.info("=" * 80)
    training_results = _train_model(cfg.training, data_info, model_info)
    # Display final results.
    _LOG.info("\n" + "=" * 80)
    _LOG.info("PIPELINE COMPLETE")
    _LOG.info("=" * 80)
    _LOG.info("Model: %s", model_info["type"])
    _LOG.info("Final Loss: %s", training_results["final_loss"])
    _LOG.info("Best Epoch: %s", training_results["best_epoch"])
    _LOG.info("Output directory: %s", output_dir)


# #############################################################################
# Main entry point with Hydra decorator
# #############################################################################


# Load from YAML files in config_example1/.
@hydra.main(
    version_base=None,
    config_path="config_example1",
    config_name="base_config",
)
def main(cfg: omgcfg.DictConfig) -> None:
    """
    Main entry point with Hydra decorator.

    The @hydra.main decorator:
    - Loads configuration from YAML files in config_example1/
    - Handles config composition (defaults: - model: linear)
    - Handles CLI overrides
    - Manages output directories
    - Enables multi-run for sweeps

    Config files used:
    - config_example1/base_config.yaml: Main configuration
    - config_example1/model/linear.yaml: Linear model (default)
    - config_example1/model/xgboost.yaml: XGBoost model (use with model=xgboost)
    - config_example1/model/rf.yaml: Random Forest model (use with model=rf)

    :param cfg: composed configuration from Hydra
    """
    _run_pipeline(cfg)


if __name__ == "__main__":
    # Hydra automatically:
    # 1. Loads config from config_example1/base_config.yaml.
    # 2. Applies defaults (loads model/linear.yaml by default).
    # 3. Parses command-line arguments and applies overrides.
    # 4. Calls `main(cfg)` with fully composed configuration.
    main()
