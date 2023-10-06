import click
import os
import logging
from .qsub_to_embeddings import count_lines

SGE_TMEM = "1G"
SGE_H_RT = "1:0:0"
SGE_JOB_NAME = "emma-populate"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

LOG = logging.getLogger(__name__)

@click.command()
@click.option(
    "--mda_list",
    type=click.File("rt"),
    required=True,
    help="Input: List of MDAs for Gemma and FunFHMMER",
)
@click.option(
    "--venv_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
    help="Path to venv with installed dependencies for CATH-eMMA CLI"
    )
@click.option(
    "--sfam_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="Input: Path to folder containing individual project folders i.e.<sfam-path>/{mda1,mda2}",
    )
@click.option(
    "--output_script",
    type=click.File("wt"),
    required=True,
    help="Output: File containing batch array script to process all MDAs/Projects in SuperFamily."
    )

def qsub_emma_to_ff_input(mda_list,venv_path,sfam_path,output_script):
    """Create qsub to populate clusters centroids after eMMA"""
    line_count = count_lines(mda_list)
    output_script.write(
        f"""\
#$ -l tmem={SGE_TMEM}
#$ -l h_vmem={SGE_TMEM}
#$ -l h_rt={SGE_H_RT}
#$ -S /bin/bash
#$ -j y
#$ -N {SGE_JOB_NAME}
#$ -cwd
#$ -P cath
#$ -t 1-{line_count}
PROJECT=$(head -n $SGE_TASK_ID {os.path.abspath(mda_list.name)} | tail -n 1)\n\
export DATADIR='{sfam_path}'
module load python/3.8.5
source {venv_path}
echo $(date) ${{PROJECT}} START

cath-emma-cli populate-cluster-centroids \\
    --cluster_reps_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_reps.csv \\
    --all_fasta ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}.fasta \\
    --centroids_tree_dir ${{DATADIR}}/${{PROJECT}}/trees/${{PROJECT}}/simple_ordering.hhconsensus.windowed \\
    --filled_tree_dir ${{DATADIR}}/${{PROJECT}}/filled_tree_first_iter \\
    --starting_clusters_mapping_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_cluster_mapping.tsv \\
    --mmseqs_cluster_mapping ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_cluster.tsv \\

echo $(date) ${{PROJECT}} END
            """)
    LOG.info(f"Generated qsub script for {line_count} eMMA projects on {sfam_path} -> {output_script.name}")