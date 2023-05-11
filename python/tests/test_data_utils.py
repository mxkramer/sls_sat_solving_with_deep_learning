import pytest
from allpairspy import AllPairs
import sys

sys.path.append("../../")

from python.src.data_utils import SATTrainingDataset, JraphDataLoader
from python.src.sat_representations import VCG, LCG, SATRepresentation

pairs = [
    values
    for values in AllPairs(
        [
            [
                "python/tests/test_instances/single_instance/",
                "python/tests/test_instances/multiple_instances/",
            ],
            [VCG, LCG],
            [True, False],
            [1, 2],
        ]
    )
]


class TestParameterized(object):
    @pytest.mark.parametrize(
        ["data_dir", "representation", "return_candidates", "batch_size"], pairs
    )
    def test_instance_loading(
        self,
        data_dir,
        representation,
        return_candidates,
        batch_size,
    ):
        assert instance_loading_tester(data_dir, representation, return_candidates)

    @pytest.mark.parametrize(
        ["data_dir", "representation", "return_candidates", "batch_size"],
        pairs,
    )
    def test_collate_function(
        self, data_dir, representation, return_candidates, batch_size
    ):
        assert collate_function_tester(
            data_dir, representation, return_candidates, batch_size
        )


def instance_loading_tester(
    path: str, rep: SATRepresentation, return_candidates: bool = False
):
    dataset = SATTrainingDataset(
        data_dir=path, representation=rep, return_candidates=return_candidates
    )
    max_nodes = dataset.max_n_node
    max_edges = dataset.max_n_edge
    for problem, (padded_candidates, energies) in dataset:
        graph = problem.graph
        n_node_array = graph.n_node
        assert n_node_array.sum() == max_nodes
        assert padded_candidates.shape[1] == max_nodes
        assert energies.shape[0] == padded_candidates.shape[0]
        assert len(graph.receivers) == max_edges
        assert len(graph.senders) == max_edges
        assert len(graph.edges) == max_edges
        assert len(graph.nodes) == max_nodes
    return True


# TODO: also bringin testing for the returning the correlation graph, i.e. test neighbors
def collate_function_tester(
    path, rep: SATRepresentation, return_candidates: bool = False, batch_size=1
):
    dataset = SATTrainingDataset(
        data_dir=path, representation=rep, return_candidates=return_candidates
    )
    loader = JraphDataLoader(dataset, batch_size=batch_size)

    for i, batch in enumerate(loader):
        (masks, graphs, neighbors), (candidates, energies) = batch
        print("loading batch")
        batch_factor = (
            batch_size
            if (i + 1) * batch_size < len(dataset)
            else len(dataset) - i * batch_size
        )
        assert len(masks) == batch_factor * dataset.max_n_node
        assert graphs.n_node.sum() == batch_factor * dataset.max_n_node
        assert graphs.n_edge.sum() == batch_factor * dataset.max_n_edge
        assert len(graphs.receivers) == batch_factor * dataset.max_n_edge
        assert len(graphs.senders) == batch_factor * dataset.max_n_edge
        assert len(graphs.edges) == batch_factor * dataset.max_n_edge
        assert len(graphs.nodes) == batch_factor * dataset.max_n_node
        assert candidates.shape == energies.shape
        assert len(candidates) == batch_factor * dataset.max_n_node
    return True
