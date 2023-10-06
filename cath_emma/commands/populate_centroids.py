import os
import shutil
from pathlib import Path
import click
import logging
from Bio import SeqIO

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

LOG = logging.getLogger(__name__)


@click.command()
@click.option(
    "--cluster_reps_file",
    type=click.File("rt"),
    required=True,
    help="Input: CSV file of cluster representatives from MMseqs2 in ID,FASTA format (example: ${PROJECT}_reps.csv)",
)
@click.option(
    "--all_fasta",
    type=click.File("rt"),
    required=True,
    help="All project sequences in a single FASTA file",
)
@click.option(
    "--centroids_tree_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="GeMMA 'trees' folder containing tree with centroids, starting cluster alignments and centroids"
)
@click.option(
    "--filled_tree_dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    help="Output: path to starting_clusters directory",
    required=True,
)
@click.option(
    "--starting_clusters_mapping_file",
    type=click.File('rt'),
    help="Mapping between cluster centroids and starting clusters used in Gemma 1st iteration (i.e. A0A2V3IUZ9/42-202       working_1.faa)",
    required=True,
)
@click.option(
    "--mmseqs_cluster_mapping",
    type=click.File("rt"),
    help="Cluster membership file from MMseqs (example: {PROJECT}_cluster.tsv)",
    required=True,
    )

def populate_cluster_centroids(cluster_reps_file,all_fasta,centroids_tree_dir,filled_tree_dir,starting_clusters_mapping_file,mmseqs_cluster_mapping):
    """Populate starting cluster centroids with all sequences in the cluster"""
    # Declare dictionaries
    dict_mmseqs = {}
    dict_starting_clusters = {}
    # Populate MMseqs cluster membership distances
    for line in mmseqs_cluster_mapping:
        cluster_rep,cluster_member = line.split('\t')
        cluster_rep = cluster_rep.rstrip()
        cluster_member = cluster_member.rstrip()
        if cluster_rep not in dict_mmseqs:
            dict_mmseqs[cluster_rep] = [cluster_member]
        else:
            dict_mmseqs[cluster_rep].append(cluster_member)
    # Populate starting clusters mapping dictionary
    for line in starting_clusters_mapping_file:
        line = line.rstrip()
        cluster_rep, starting_cluster_filename = line.split('\t')
        dict_starting_clusters[cluster_rep] = starting_cluster_filename

    # Create BioPython SeqIO dictionary
    sequence_dict = SeqIO.to_dict(SeqIO.parse(all_fasta, "fasta"))

    # Create filled starting clusters
    counter = 1
    if not os.path.exists(filled_tree_dir):
        os.makedirs(f'{filled_tree_dir}/starting_cluster_alignments/',exist_ok=True)
        os.makedirs(f'{filled_tree_dir}/merge_node_alignments/',exist_ok=True)
        shutil.copy(f'{centroids_tree_dir}/tree.trace',f'{filled_tree_dir}/')
        shutil.copy(f'{centroids_tree_dir}/tree.newick',f'{filled_tree_dir}/')

        
    for cluster_id in dict_mmseqs:
        filled_cluster_name = dict_starting_clusters[cluster_id]
        seq_to_write = []
        output_file = f'{filled_tree_dir}/starting_cluster_alignments/{filled_cluster_name}'
        for seq_id in dict_mmseqs[cluster_id]:
            seq_to_write.append(sequence_dict[seq_id])
        SeqIO.write(seq_to_write, output_file, "fasta")
        counter +=1
    LOG.info(f'Filled {counter} starting clusters alignments for FunFHMMER')
    
    # Create filled merge node alignments
    counter_merge = 0
    for file in Path(f'{centroids_tree_dir}/merge_node_alignments/').iterdir():
        centroid_alignment = SeqIO.index(str(file), "fasta")
        centroid_keys = set(centroid_alignment.keys())
        shared_ids = centroid_keys & set(dict_mmseqs.keys())
        with open(f'{filled_tree_dir}/merge_node_alignments/{file.name}','wt') as filled_merge_node_fh:
            for id in shared_ids:
                for cluster_member in dict_mmseqs[id]:
                    filled_merge_node_fh.write(f'>{sequence_dict[cluster_member].description}\n{sequence_dict[cluster_member].seq}\n')
        counter_merge +=1
    LOG.info(f'Filled {counter_merge} merge_node alignments for FunFHMMER')
            
