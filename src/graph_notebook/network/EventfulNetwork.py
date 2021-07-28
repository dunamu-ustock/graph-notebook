"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from collections import defaultdict
import collections
from networkx import MultiDiGraph
from .Network import Network

EVENT_ADD_NODE = 'add_node'
EVENT_ADD_NODE_DATA = 'add_node_data'
EVENT_ADD_NODE_PROPERTY = 'add_node_property'
EVENT_ADD_EDGE = 'add_edge'
EVENT_ADD_EDGE_DATA = 'add_edge_data'

VALID_EVENTS = [EVENT_ADD_NODE, EVENT_ADD_NODE_DATA, EVENT_ADD_NODE_PROPERTY, EVENT_ADD_EDGE, EVENT_ADD_EDGE_DATA]


class EventfulNetwork(Network):
    """
    EventfulNetwork provides hooks to receive notifications of changes
    which have taken place due to method invocations. For each method in
    the base class Network, any callbacks which are registered to the method will
    be invoked, packaging the arguments of the method invoked into a payload for
    subscribers to see/take action on.

    All method signatures for callbacks should follow the form callback(network, event_name, data)
    Callbacks will happen after the method is finished being invoked. For instance, if add_node is called,
    the EventfulNetwork will call super().add_node(...) then look for callbacks to dispatch.
    """

    def __init__(self, graph: MultiDiGraph = None, callbacks: dict = None):
        if callbacks is None:
            callbacks = defaultdict(list)
        self.callbacks = callbacks

        if graph is None:
            graph = MultiDiGraph()
        super().__init__(graph)

    def strip_and_truncate_label(self, old_label: str, max_len: int):
        label = str(old_label).strip("[]'")
        return label if len(label) <= max_len else label[:max_len - 3] + '...'

    def flatten(self, d:dict, parent_key='', sep='_') -> dict:
        """Flattens dictionaries including nested dictionaties

        Args:
            d (dict): The dictionary to flatten
            parent_key (str, optional): The parent key name to append. Defaults to ''.
            sep (str, optional): The seperator between the parent and sub key. Defaults to '_'.

        Returns:
            [dict]: The flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def register_universal_callback(self, callback):
        """
        Registers the given callback to all events which can be emitted by the Eventful Network
        """
        if not callable(callback):
            raise ValueError("callback must be callable")

        for event_name in VALID_EVENTS:
            self.register_callback(event_name, callback)

    def register_callback(self, event, callback):
        if not callable(callback):
            raise ValueError("callback must be callable.")

        self.callbacks[event].append(callback)

    def dispatch_callbacks(self, event_name, data):
        if event_name in self.callbacks:
            for c in self.callbacks[event_name]:
                c(self, event_name, data)

    def add_node_property(self, node_id: str, key: str, value: str):
        super().add_node_property(node_id, key, value)
        data = {
            'node_id': node_id,
            'key': key,
            'value': value
        }
        self.dispatch_callbacks(EVENT_ADD_NODE_PROPERTY, data)

    def add_node(self, node_id: str, data: dict = None):
        if data is None:
            data = {}
        super().add_node(node_id, data)
        payload = {
            'node_id': node_id,
            'data': data
        }
        self.dispatch_callbacks(EVENT_ADD_NODE, payload)

    def add_edge(self, from_id: str, to_id: str, edge_id: str, label: str, data: dict = None):
        if data is None:
            data = {}
        super().add_edge(from_id, to_id, edge_id, label, data)
        payload = {
            'from_id': from_id,
            'to_id': to_id,
            'edge_id': edge_id,
            'label': label,
            'data': data
        }
        self.dispatch_callbacks(EVENT_ADD_EDGE, payload)

    def add_node_data(self, node_id: str, data: dict = None):
        if data is None:
            data = {}
        super().add_node_data(node_id, data)
        d = {
            'node_id': node_id,
            'data': data
        }
        self.dispatch_callbacks(EVENT_ADD_NODE_DATA, d)

    def add_edge_data(self, from_id: str, to_id: str, edge_id, data: dict = None):
        if data is None:
            data = {}
        super().add_edge_data(from_id, to_id, edge_id, data)
        d = {
            'from_id': from_id,
            'to_id': to_id,
            'edge_id': edge_id,
            'data': data
        }

        self.dispatch_callbacks(EVENT_ADD_EDGE_DATA, d)
