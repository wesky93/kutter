import unittest
from decimal import Decimal
from typing import TypedDict, Union, List, Dict

from lightkube import Client
from lightkube.config.kubeconfig import KubeConfig
from lightkube.models.core_v1 import NodeStatus
from lightkube.models.meta_v1 import ObjectMeta
from lightkube.resources.core_v1 import Node, Namespace
from lightkube.utils.quantity import parse_quantity


class NodeResource(TypedDict):
    cpu: Decimal
    memory: Decimal


class NodesSummary(TypedDict):
    count: int
    total_capacity: NodeResource
    total_allocatable: NodeResource


class KubeTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(KubeTestCase, self).__init__(*args, **kwargs)
        self.kube_client = self.get_kube_client()

    def get_kube_client(self):
        config = KubeConfig.from_env()
        client = Client(config=config, field_manager="kutter-test")
        return client

    def setUp(self):
        self.reset_kube()

    def tearDown(self):
        """
        This method is called after each test
        :return:
        """
        self.reset_kube()

    def list_node(self, **kwargs):
        return self.kube_client.list(Node, **kwargs)

    def create_node(
        self,
        name: str,
        cpu: str,
        memory: str,
        labels: Dict = None,
        annotations: Dict = None,
    ):
        node = Node(metadata=ObjectMeta(), status=NodeStatus())
        node.metadata.name = name
        allocatable = dict(cpu=cpu, memory=memory)
        node.status.allocatable = allocatable
        node.status.capacity = allocatable

        if labels:
            node.metadata.labels = labels
        if annotations:
            node.metadata.annotations = annotations
        return self.kube_client.create(node)

    def bulk_create_nodes(
        self,
        count: int,
        name_prefix: str,
        cpu: str,
        memory: str,
        labels: Dict = None,
        annotations: Dict = None,
    ):
        nodes = []
        for i in range(count):
            name = f"{name_prefix}-{i}"
            node = self.create_node(
                name=name,
                cpu=cpu,
                memory=memory,
                labels=labels,
                annotations=annotations,
            )
            nodes.append(node)
        return nodes

    def nodes_summary(
        self, labels: Union[List, Dict] = None, fields: Union[List, Dict] = None
    ) -> NodesSummary:
        nodes = self.list_node(labels=labels, fields=fields)
        count = 0
        allocatable = NodeResource(cpu=Decimal("0"), memory=Decimal("0"))
        capacity = NodeResource(cpu=Decimal("0"), memory=Decimal("0"))

        for node in nodes:
            count += 1
            allocatable["cpu"] += parse_quantity(node.status.allocatable["cpu"])
            allocatable["memory"] += parse_quantity(node.status.allocatable["memory"])
            capacity["cpu"] += parse_quantity(node.status.capacity["cpu"])
            capacity["memory"] += parse_quantity(node.status.capacity["memory"])
        summary = NodesSummary(
            count=count, total_capacity=capacity, total_allocatable=allocatable
        )
        return summary

    def reset_kube(self):
        """
        Reset the kubernetes cluster
        :return:
        """
        namespaces = self.kube_client.list(Namespace)
        for ns in namespaces:
            if ns.metadata.name not in ["default", "kube-system", "kube-public"]:
                self.kube_client.delete(Namespace, ns.metadata.name)

        self.kube_client.deletecollection(Node)
