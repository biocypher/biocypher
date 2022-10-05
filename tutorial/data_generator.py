"""
Classes used to generate mock data for the BioCypher tutorial.
"""

import random
import string


class Protein:
    """
    Generates instances of proteins.
    """

    def __init__(self):
        self.id = self._generate_id()
        self.label = "uniprot_protein"
        self.properties = self._generate_properties()

    def _generate_id(self):
        lets = [random.choice(string.ascii_uppercase) for _ in range(3)]
        nums = [random.choice(string.digits) for _ in range(3)]

        # join alternating between lets and nums
        return "".join([x for y in zip(lets, nums) for x in y])

    def _generate_properties(self):
        properties = {}

        ## random amino acid sequence

        # random int between 50 and 250
        l = random.randint(50, 250)

        properties["sequence"] = "".join(
            [random.choice("ACDEFGHIKLMNPQRSTVWY") for _ in range(l)]
        )

        ## random description
        properties["description"] = " ".join(
            [random.choice(string.ascii_lowercase) for _ in range(10)]
        )

        ## taxon
        properties["taxon"] = "9606"

        return properties
