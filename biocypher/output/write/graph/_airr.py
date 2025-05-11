"""Module to provide the AnnData writer class for BioCypher."""

from biocypher._logger import logger
from biocypher.output.write._writer import _Writer


class _AirrWriter(_Writer):
    """A minimal placeholder writer class that implements the required methods
    but performs no actual writing operations, since there is an existing anndata native writer functionality
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Placeholder writer initialized")

    def _write_node_data(self, nodes) -> bool:
        """Required implementation that does nothing with nodes."""
        logger.info("Placeholder: Node data received but not processed")
        return True

    def _write_edge_data(self, edges) -> bool:
        """Required implementation that does nothing with edges."""
        logger.info("Placeholder: Edge data received but not processed")
        return True

    def _construct_import_call(self) -> str:
        """Return a placeholder import script."""
        return "# This is a placeholder import script\nprint('No actual import functionality implemented')"

    def _get_import_script_name(self) -> str:
        """Return a placeholder script name."""
        return "placeholder_import.py"
