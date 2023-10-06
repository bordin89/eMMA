import logging
import click

from .commands import calculate_esm_embeddings
from .commands import convert_fasta_to_csv
from .commands import qsub_to_embeddings
from .commands import create_distance_matrix
from .commands import create_starting_clusters
from .commands import populate_centroids
from .commands import qsub_embeddings_to_emma_input
from .commands import qsub_run_mmseqs2
from .commands import qsub_emma
from .commands import qsub_populate_clusters

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

LOG = logging.getLogger(__name__)


@click.group()
@click.version_option()
@click.option("--verbose", "-v", "verbosity", default=0, count=True)
@click.pass_context
def cli(ctx, verbosity):
    "End-to-end CATH-eMMA workflow"

    root_logger = logging.getLogger()
    log_level = root_logger.getEffectiveLevel() - (10 * verbosity)
    root_logger.setLevel(log_level)
    LOG.info(
        f"Starting logging... (level={logging.getLevelName(root_logger.getEffectiveLevel())})"
    )


cli.add_command(calculate_esm_embeddings.calculate_esm_to_embed)
cli.add_command(convert_fasta_to_csv.convert_fasta_to_csv_for_embed)
cli.add_command(qsub_to_embeddings.qsub_to_embeddings)
cli.add_command(create_distance_matrix.create_distance_matrix)
cli.add_command(create_starting_clusters.create_starting_clusters_from_centroids)
cli.add_command(populate_centroids.populate_cluster_centroids)
cli.add_command(qsub_embeddings_to_emma_input.qsub_embeddings_to_emma_input)
cli.add_command(qsub_run_mmseqs2.qsub_to_mmseqs2)
cli.add_command(qsub_emma.qsub_emma_input_to_emma_output)
cli.add_command(qsub_populate_clusters.qsub_emma_to_ff_input)

