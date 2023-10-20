import torch

import metatensor.torch
from metatensor.torch import Labels, TensorBlock, TensorMap

from .data import load_data


def check_operation(reduce_over_samples):
    tensor = load_data("qm7-power-spectrum.npz")

    assert tensor.sample_names == ["structure", "center"]
    reduced_tensor = reduce_over_samples(tensor, "center")

    assert isinstance(reduced_tensor, torch.ScriptObject)
    assert reduced_tensor.sample_names == ["structure"]


def test_operations_as_python():
    check_operation(metatensor.torch.sum_over_samples)
    check_operation(metatensor.torch.mean_over_samples)
    check_operation(metatensor.torch.std_over_samples)
    check_operation(metatensor.torch.var_over_samples)


def test_operations_as_torch_script():
    check_operation(torch.jit.script(metatensor.torch.sum_over_samples))
    check_operation(torch.jit.script(metatensor.torch.mean_over_samples))
    check_operation(torch.jit.script(metatensor.torch.std_over_samples))
    check_operation(torch.jit.script(metatensor.torch.var_over_samples))


def test_reduction_all_samples():
    block_1 = TensorBlock(
        values=torch.tensor(
            [
                [1, 2, 4],
                [3, 5, 6],
                [-1.3, 26.7, 4.54],
            ]
        ),
        samples=Labels.range("s", 3),
        components=[],
        properties=Labels(["p"], torch.IntTensor([[0], [1], [5]])),
    )
    keys = Labels(names=["key_1", "key_2"], values=torch.IntTensor([[0, 0]]))
    X = TensorMap(keys, [block_1])

    sum_X = metatensor.torch.sum_over_samples(X, sample_names=["s"])
    mean_X = metatensor.torch.mean_over_samples(X, sample_names=["s"])
    var_X = metatensor.torch.var_over_samples(X, sample_names=["s"])
    std_X = metatensor.torch.std_over_samples(X, sample_names=["s"])

    assert sum_X[0].samples == Labels.single()
    assert metatensor.torch.equal_metadata(sum_X, mean_X)
    assert metatensor.torch.equal_metadata(sum_X, std_X)
    assert metatensor.torch.equal_metadata(mean_X, var_X)

    assert torch.all(sum_X[0].values == torch.sum(X[0].values, axis=0))
    assert torch.all(mean_X[0].values == torch.mean(X[0].values, axis=0))
    assert torch.allclose(std_X[0].values, torch.std(X[0].values, correction=0, axis=0))
    assert torch.allclose(var_X[0].values, torch.var(X[0].values, correction=0, axis=0))
