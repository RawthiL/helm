import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import date
import importlib_resources as resources

import dacite
import yaml


# Different modalities
TEXT_MODEL_TAG: str = "TEXT_MODEL_TAG"
IMAGE_MODEL_TAG: str = "IMAGE_MODEL_TAG"
CODE_MODEL_TAG: str = "CODE_MODEL_TAG"
EMBEDDING_MODEL_TAG: str = "EMBEDDING_MODEL_TAG"

# Some model APIs have limited functionalities
FULL_FUNCTIONALITY_TEXT_MODEL_TAG: str = "FULL_FUNCTIONALITY_TEXT_MODEL_TAG"
LIMITED_FUNCTIONALITY_TEXT_MODEL_TAG: str = "LIMITED_FUNCTIONALITY_TEXT_MODEL_TAG"

# ChatML format
CHATML_MODEL_TAG: str = "CHATML_MODEL_TAG"

# OpenAI Chat format
OPENAI_CHATGPT_MODEL_TAG: str = "openai_chatgpt"

# For Anthropic models
ANTHROPIC_CLAUDE_1_MODEL_TAG: str = "ANTHROPIC_CLAUDE_1_MODEL_TAG"
ANTHROPIC_CLAUDE_2_MODEL_TAG: str = "ANTHROPIC_CLAUDE_2_MODEL_TAG"

# Models which emit garbage tokens when temperature=0.
BUGGY_TEMP_0_TAG: str = "BUGGY_TEMP_0_TAG"

# Models that are used for ablations and fine-grained analyses.
# These models are selected specifically because of their low marginal cost to evaluate.
ABLATION_MODEL_TAG: str = "ABLATION_MODEL_TAG"

# Some models (e.g., T5) have stripped newlines.
# So we cannot use \n as a stop sequence for these models.
NO_NEWLINES_TAG: str = "NO_NEWLINES_TAG"

# Some models (e.g., UL2) require a prefix (e.g., [NLG]) in the
# prompts to indicate the mode before doing inference.
NLG_PREFIX_TAG: str = "NLG_PREFIX_TAG"

# Some models can follow instructions.
INSTRUCTION_FOLLOWING_MODEL_TAG: str = "INSTRUCTION_FOLLOWING_MODEL_TAG"

# For Vision-langauge models (VLMs)
VISION_LANGUAGE_MODEL_TAG: str = "VISION_LANGUAGE_MODEL_TAG"


CONFIG_PACKAGE = "helm.config"
MODEL_METADATA_FILE: str = "model_metadata.yaml"
METADATAS_REGISTERED: bool = False


# Frozen is set to false as the model_deployment_registry.py file
# might populate the deployment_names field.
@dataclass(frozen=False)
class ModelMetadata:
    name: str
    """Name of the model group (e.g., "openai/davinci"). This is the name of the model,
    not the name of the deployment.
    Usually formatted as "<creator_organization>/<engine_name>". Example: "ai21/j1-jumbo"."""

    creator_organization_name: str
    """Name of the organization that created the model."""

    display_name: str
    """Name that is going to be displayed to the user (on the website, etc.)."""

    description: str
    """Description of the model, to be displayed on the website."""

    access: str
    """Description of the access level of the model. Should be one of the following:
    - "open": the model is open-source and can be downloaded from the internet.
    - "closed": not accessible
    - "limited": accessible with an API key.
    If there are multiple deployments, this should be the most permissive access across all deployments."""

    release_date: date
    """Release date of the model."""

    tags: List[str] = field(default_factory=list)
    """Tags corresponding to the properties of the model."""

    num_parameters: Optional[int] = None
    """Number of parameters in the model.
    This should be a string as the number of parameters is usually a round number (175B),
    but we set it as an int for plotting purposes."""

    deployment_names: Optional[List[str]] = None
    """List of the model deployments for this model. Should at least contain one model deployment.
    Refers to the field "name" in the ModelDeployment class. Defaults to a single model deployment
    with the same name as the model."""

    @property
    def creator_organization(self) -> str:
        """
        Extracts the creator organization from the model name.
        Example: 'ai21/j1-jumbo' => 'ai21'
        This can be different from the hosting organization.
        """
        return self.name.split("/")[0]

    @property
    def engine(self) -> str:
        """
        Extracts the model engine from the model name.
        Example: 'ai21/j1-jumbo' => 'j1-jumbo'
        """
        return self.name.split("/")[1]


@dataclass(frozen=True)
class ModelMetadataList:
    models: List[ModelMetadata] = field(default_factory=list)


ALL_MODELS_METADATA: List[ModelMetadata] = []
MODEL_NAME_TO_MODEL_METADATA: Dict[str, ModelMetadata] = {model.name: model for model in ALL_MODELS_METADATA}


# ===================== REGISTRATION FUNCTIONS ==================== #
def register_model_metadata_from_path(path: str) -> None:
    """Register model configurations from the given path."""
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    # Using dacite instead of cattrs because cattrs doesn't have a default
    # serialization format for dates
    model_metadata_list = dacite.from_dict(ModelMetadataList, raw)
    for model_metadata in model_metadata_list.models:
        register_model_metadata(model_metadata)


def register_model_metadata(model_metadata: ModelMetadata) -> None:
    """Register a single model configuration."""
    # hlog(f"Registered model metadata {model_metadata.name}")
    ALL_MODELS_METADATA.append(model_metadata)
    MODEL_NAME_TO_MODEL_METADATA[model_metadata.name] = model_metadata


def maybe_register_model_metadata_from_base_path(path: str) -> None:
    """Register model metadata from yaml file if the path exists."""
    if os.path.exists(path):
        register_model_metadata_from_path(path)


# ===================== UTIL FUNCTIONS ==================== #
def get_model_metadata(model_name: str) -> ModelMetadata:
    """Get the `Model` given the name."""
    register_metadatas_if_not_already_registered()
    if model_name not in MODEL_NAME_TO_MODEL_METADATA:
        raise ValueError(f"No model with name: {model_name}")

    return MODEL_NAME_TO_MODEL_METADATA[model_name]


def get_model_creator_organization(model_name: str) -> str:
    """Get the model's group given the name."""
    model: ModelMetadata = get_model_metadata(model_name)
    return model.creator_organization


def get_all_models() -> List[str]:
    """Get all model names."""
    register_metadatas_if_not_already_registered()
    return list(MODEL_NAME_TO_MODEL_METADATA.keys())


def get_models_by_creator_organization(organization: str) -> List[str]:
    """
    Gets models by creator organization.
    Example:   ai21   =>   ai21/j1-jumbo, ai21/j1-grande, ai21-large.
    """
    register_metadatas_if_not_already_registered()
    return [model.name for model in ALL_MODELS_METADATA if model.creator_organization == organization]


def get_model_names_with_tag(tag: str) -> List[str]:
    """Get all the name of the models with tag `tag`."""
    register_metadatas_if_not_already_registered()
    return [model.name for model in ALL_MODELS_METADATA if tag in model.tags]


def get_all_text_models() -> List[str]:
    """Get all text model names."""
    return get_model_names_with_tag(TEXT_MODEL_TAG)


def get_all_code_models() -> List[str]:
    """Get all code model names."""
    return get_model_names_with_tag(CODE_MODEL_TAG)


def get_all_instruction_following_models() -> List[str]:
    """Get all instruction-following model names."""
    return get_model_names_with_tag(INSTRUCTION_FOLLOWING_MODEL_TAG)


def register_metadatas_if_not_already_registered() -> None:
    global METADATAS_REGISTERED
    if not METADATAS_REGISTERED:
        path: str = resources.files(CONFIG_PACKAGE).joinpath(MODEL_METADATA_FILE)
        maybe_register_model_metadata_from_base_path(path)
        METADATAS_REGISTERED = True


def get_default_model_metadata(helm_model_name: str) -> ModelMetadata:
    return ModelMetadata(
        name=helm_model_name,
        creator_organization_name="Unknown",
        display_name=helm_model_name,
        description=helm_model_name,
        access="open",
        release_date=date.today(),
        tags=[TEXT_MODEL_TAG, FULL_FUNCTIONALITY_TEXT_MODEL_TAG],
    )
