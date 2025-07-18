from pathlib import Path

import pytest
import torch as th
import transformers as tr
from datasets import Dataset


@pytest.fixture(scope="module")
def text_dataset_path() -> Path:
    dir_path = Path(__file__).parent.absolute()
    return Path(dir_path, "test_data", "pile_text.jsonl")


@pytest.fixture(scope="module")
def text_dataset(text_dataset_path: Path) -> Dataset:
    dataset = Dataset.from_json(str(text_dataset_path))
    assert isinstance(dataset, Dataset)
    return dataset


@pytest.fixture(
    scope="module",
    params=[
        "EleutherAI/pythia-70m-deduped",
        "bigscience/bloom-560m",
        "EleutherAI/gpt-neo-125M",
        "facebook/opt-125m",
        "mockmodel/llama-tiny",
        "mockmodel/gemma-tiny",
        "mockmodel/gemma-2-tiny",
        "gpt2",
    ],
)
def random_small_model(request: str) -> tr.PreTrainedModel:
    small_model_name = request.param
    th.manual_seed(42)

    # We use a random model with the correct config instead of downloading the
    # whole pretrained checkpoint.
    if small_model_name == "mockmodel/llama-tiny":
        config = tr.LlamaConfig(
            vocab_size=32_000,
            hidden_size=128,
            num_hidden_layers=4,
            num_attention_heads=4,
        )
    elif small_model_name == "mockmodel/gemma-tiny":
        config = tr.GemmaConfig(
            vocab_size=32_000,
            hidden_size=128,
            num_hidden_layers=4,
            num_attention_heads=4,
            num_key_value_heads=4,
            head_dim=32,
        )

    elif small_model_name == "mockmodel/gemma-2-tiny":
        config = tr.Gemma2Config(
            vocab_size=32_000,
            hidden_size=128,
            intermediate_size=512,  # Usually 4x hidden_size for MLP
            num_hidden_layers=4,
            num_attention_heads=4,
            num_key_value_heads=4,
            head_dim=32,
            # Gemma-2 specific parameters
            hidden_activation="gelu_pytorch_tanh",  # Gemma-2 default
            query_pre_attn_scalar=32,  # Scaled down from 256 (should match head_dim)
            sliding_window=128,  # Scaled down from 4096
            final_logit_softcapping=30.0,  # Gemma-2 default
            attn_logit_softcapping=50.0,  # Gemma-2 default
            attention_bias=False,  # Gemma-2 default
            attention_dropout=0.0,  # Gemma-2 default
            rms_norm_eps=1e-06,  # Gemma-2 default
            rope_theta=10000.0,  # Gemma-2 default
            max_position_embeddings=512,  # Scaled down from 8192
        )
    else:
        config = tr.AutoConfig.from_pretrained(small_model_name)

    model = tr.AutoModelForCausalLM.from_config(config)
    model.eval()

    return model


@pytest.fixture(
    scope="module",
    params=[
        "EleutherAI/pythia-70m-deduped",
        "bigscience/bloom-560m",
        "EleutherAI/gpt-neo-125M",
        "facebook/opt-125m",
        "gpt2",
    ],
)
def small_model_tokenizer(request: str) -> tr.PreTrainedTokenizerBase:
    return tr.AutoTokenizer.from_pretrained(request.param, use_fast=True)


@pytest.fixture(scope="module")
def gpt2_tokenizer():
    return tr.AutoTokenizer.from_pretrained("gpt2", use_fast=True)


@pytest.fixture(scope="module")
def opt_random_model() -> tr.PreTrainedModel:
    config = tr.AutoConfig.from_pretrained("facebook/opt-125m")
    model = tr.AutoModelForCausalLM.from_config(config)
    model.eval()
    return model


@pytest.fixture(scope="module")
def gpt2_tiny_random_model_local_path(
    tmpdir_factory, gpt2_tokenizer: tr.PreTrainedTokenizerBase
):
    config = tr.AutoConfig.from_pretrained("gpt2")
    config.n_heads = 2
    config.n_embed = 8
    config.n_layers = 2
    model = tr.AutoModelForCausalLM.from_config(config)
    assert isinstance(model, tr.PreTrainedModel)
    tmp_path = tmpdir_factory.mktemp("gpt2_random_model_local")
    model.save_pretrained(tmp_path)
    gpt2_tokenizer.save_pretrained(tmp_path)
    return tmp_path
