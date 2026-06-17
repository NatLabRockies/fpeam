"""Smoke tests for FPEAM.Router using a small synthetic road graph."""
import pytest
import numpy as np
import pandas as pd

from FPEAM.Router import Router


@pytest.fixture(scope='module')
def small_router():
    """
    Four nodes at known coordinates connected by three edges forming a path:
    node 1 (0,0) -- edge 1 (weight=1000m, county 001) -- node 2 (0,1)
    node 2 (0,1) -- edge 2 (weight=2000m, county 001) -- node 3 (0,2)
    node 3 (0,2) -- edge 3 (weight=1000m, county 003) -- node 4 (1,2)
    """
    edges = pd.DataFrame([
        {'edge_id': 1, 'statefp': '17', 'countyfp': '001',
         'u_of_edge': 1, 'v_of_edge': 2, 'weight': 1000.0, 'fclass': 1},
        {'edge_id': 2, 'statefp': '17', 'countyfp': '001',
         'u_of_edge': 2, 'v_of_edge': 3, 'weight': 2000.0, 'fclass': 1},
        {'edge_id': 3, 'statefp': '17', 'countyfp': '003',
         'u_of_edge': 3, 'v_of_edge': 4, 'weight': 1000.0, 'fclass': 1},
    ])
    node_map = pd.DataFrame([
        {'node_id': 1, 'x': 0.0, 'y': 0.0},
        {'node_id': 2, 'x': 0.0, 'y': 1.0},
        {'node_id': 3, 'x': 0.0, 'y': 2.0},
        {'node_id': 4, 'x': 1.0, 'y': 2.0},
    ])
    return Router(edges=edges, node_map=node_map, memory=None)


class TestRouterSmoke:

    def test_get_route_returns_dataframe(self, small_router):
        """get_route returns a DataFrame with region_transportation, fclass, vmt columns."""
        result = small_router.get_route(start=(0.0, 0.0), end=(1.0, 2.0))
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == {'region_transportation', 'fclass', 'vmt'}

    def test_route_covers_both_counties(self, small_router):
        """Route from node 1 to node 4 passes through county 001 and 003."""
        result = small_router.get_route(start=(0.0, 0.0), end=(1.0, 2.0))
        assert '17001' in result['region_transportation'].values
        assert '17003' in result['region_transportation'].values

    def test_vmt_is_positive(self, small_router):
        """All VMT values are positive (weight / 1000 * km_per_mile_conversion)."""
        result = small_router.get_route(start=(0.0, 0.0), end=(1.0, 2.0))
        assert (result['vmt'] > 0).all()

    def test_vmt_county_001_approx(self, small_router):
        """
        County 001 carries edges 1+2: total weight 3000m → ~1.863 miles.
        Tolerance is loose because node snapping may vary.
        """
        result = small_router.get_route(start=(0.0, 0.0), end=(1.0, 2.0))
        vmt_001 = result.loc[result['region_transportation'] == '17001', 'vmt'].sum()
        expected = (3000.0 / 1000.0) * 0.621371
        assert abs(vmt_001 - expected) < 0.01

    def test_nearest_node_fallback(self, small_router):
        """Start coordinates that don't land exactly on a node snap to the nearest."""
        # (0.01, 0.01) is closest to node 1 (0, 0)
        result = small_router.get_route(start=(0.01, 0.01), end=(0.99, 2.01))
        assert not result.empty


@pytest.fixture(scope='module')
def router_with_node_zero():
    """Graph where valid node IDs start at 0 (exposes the 'if not node_id' false-positive)."""
    import pandas as pd
    edges = pd.DataFrame([
        {'edge_id': 1, 'statefp': '17', 'countyfp': '001',
         'u_of_edge': 0, 'v_of_edge': 1, 'weight': 1000.0, 'fclass': 1},
    ])
    node_map = pd.DataFrame([
        {'node_id': 0, 'x': 0.0, 'y': 0.0},
        {'node_id': 1, 'x': 0.0, 'y': 1.0},
    ])
    return Router(edges=edges, node_map=node_map, memory=None)


class TestRouterNodeZero:

    def test_route_from_node_zero_does_not_raise(self, router_with_node_zero):
        """A graph with node_id=0 must not raise 'node is undefined' ValueError."""
        result = router_with_node_zero.get_route(start=(0.0, 0.0), end=(0.0, 1.0))
        assert not result.empty
        assert '17001' in result['region_transportation'].values
