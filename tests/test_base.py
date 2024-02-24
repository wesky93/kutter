import unittest
from random import randint

from lightkube.utils.quantity import equals_canonically, parse_quantity

from .base import KubeTestCase


class KubeTest(KubeTestCase):
    def assertResourceEqual(self, expected: dict, result: dict):
        self.assertTrue(
            equals_canonically(expected, result),
            f"dose not match resources\nexpected: {expected}\nresult: {result}",
        )

    def assertItemsIn(self, expected: dict, result: dict):
        """
        Compare the dictionary for the value I want.
        Use to check the value of labels, annotations.

        ex)
        expected = {'env': 'test'}
        result = {'env': 'test', 'note': 'test'}
        self.assertItemsIn(expected, result) == True

        :param expected:
        :param result:
        :return:
        """
        _result = True

        for k, v in expected.items():
            if k not in expected:
                _result = False
                break

            if result[k] != v:
                _result = False
                break
        self.assertTrue(
            _result, f"dose not match values\nexpected: {expected}\nresult: {result}"
        )

    def test_bulk_create_nodes(self):
        cpu = "2000m"
        memory = "2Gi"
        expected_allocatable = dict(cpu=cpu, memory=memory)

        labels = {"env": "test"}
        annotations = {"note": "test"}
        created_nodes = self.bulk_create_nodes(
            5, "test-node", cpu, memory, labels, annotations
        )

        expected_names = [node.metadata.name for node in created_nodes]

        nodes = list(self.list_node())
        sample_node = nodes[0]
        result_names = [node.metadata.name for node in nodes]

        # check node names
        self.assertEqual(expected_names, result_names)

        # check node metadata
        self.assertItemsIn(labels, sample_node.metadata.labels)
        self.assertItemsIn(annotations, sample_node.metadata.annotations)
        self.assertResourceEqual(expected_allocatable, sample_node.status.allocatable)

    def test_nodes_summary(self):
        cpu = "2000m"
        memory = "2Gi"
        labels = {"env": "test"}
        target_nodes_count = randint(3, 10)
        self.bulk_create_nodes(target_nodes_count, "test-node", cpu, memory, labels)

        dummy_cpu = "1000m"
        dummy_memory = "1Gi"
        dummy_labels = {"env": "dummy"}
        dummy_nodes_count = randint(2, 6)
        self.bulk_create_nodes(
            dummy_nodes_count, "dummy-node", dummy_cpu, dummy_memory, dummy_labels
        )

        target_allocate_cpu = parse_quantity(cpu) * target_nodes_count
        target_allocate_memory = parse_quantity(memory) * target_nodes_count

        dummy_allocate_cpu = parse_quantity(dummy_cpu) * dummy_nodes_count
        dummy_allocate_memory = parse_quantity(dummy_memory) * dummy_nodes_count

        total_nodes = target_nodes_count + dummy_nodes_count
        total_allocate_cpu = target_allocate_cpu + dummy_allocate_cpu
        total_allocate_memory = target_allocate_memory + dummy_allocate_memory

        with self.subTest("test all nodes summary"):
            all_nodes_summary = self.nodes_summary()
            self.assertEqual(all_nodes_summary["count"], total_nodes)
            self.assertEqual(
                all_nodes_summary["total_allocatable"]["cpu"], total_allocate_cpu
            )
            self.assertEqual(
                all_nodes_summary["total_allocatable"]["memory"], total_allocate_memory
            )

        with self.subTest("test filtered nodes summary"):
            target_nodes_summary = self.nodes_summary(labels=labels)
            self.assertEqual(target_nodes_summary["count"], target_nodes_count)
            self.assertEqual(
                target_nodes_summary["total_allocatable"]["cpu"], target_allocate_cpu
            )
            self.assertEqual(
                target_nodes_summary["total_allocatable"]["memory"],
                target_allocate_memory,
            )


if __name__ == "__main__":
    unittest.main()
