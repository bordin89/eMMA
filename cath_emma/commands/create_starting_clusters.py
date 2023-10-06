import click
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

LOG = logging.getLogger(__name__)


@click.command()
@click.option(
    "--cluster_reps_file",
    type=click.File("rt"),
    required=True,
    help="Input: CSV file of cluster representatives from MMseqs2 in ID,FASTA format (example: ${PROJECT}_reps.tsv)",
)
@click.option(
    "--starting_clusters_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="Output: path to starting_clusters directory",
    required=True,
)
@click.option(
    "--fasta_suffix",
    type=str,
    help="Suffix for starting clusters FASTA files. (default: faa)",
    default="faa",
    )
@click.option(
    '--cluster_mapping_file',
    type=click.File('wt'),
    required=True,
    help="Mapping between cluster ids and working ids."
)

def create_starting_clusters_from_centroids(cluster_reps_file,starting_clusters_dir,fasta_suffix,cluster_mapping_file):
    """Create starting clusters of cluster representatives from MMseqs2"""
    counter = 1
    for line in cluster_reps_file:
        line = line.rstrip()
        cluster_rep_id,sequence = line.split(',')
        cluster_file = f'working_{counter}.{fasta_suffix}'
        with open(f'{starting_clusters_dir}/{cluster_file}','wt') as starting_cluster_fh:
            starting_cluster_fh.write(f'>{cluster_rep_id}\n{sequence}')
        cluster_mapping_file.write(f'{cluster_rep_id}\t{cluster_file}\n')
        counter +=1
    LOG.info(f'DONE. Created {counter-1} starting clusters.')
