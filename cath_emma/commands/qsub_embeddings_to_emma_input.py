import click
import os
import logging
from .qsub_to_embeddings import count_lines

SGE_TMEM = "16G"
SGE_H_RT = "8:0:0"
SGE_JOB_NAME = "emma-prep"

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
    "--sfam_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="Input: Path to folder containing individual project folders i.e.<sfam-path>/{mda1,mda2}",
    )
@click.option(
    "--venv_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
    help="Path to venv with installed dependencies for CATH-eMMA CLI"
    )
@click.option(
    "--output_script",
    type=click.File("wt"),
    required=True,
    help="Output: File containing batch array script to process all MDAs/Projects in SuperFamily."
    )

def qsub_embeddings_to_emma_input(mda_list,sfam_path,venv_path,output_script):
    """Create eMMA input files from distance matrices"""
    line_count = count_lines(mda_list)
    output_script.write(
        f"""\
#$ -l tmem={SGE_TMEM}
#$ -l h_vmem={SGE_TMEM}
#$ -l h_rt={SGE_H_RT}
#$ -S /bin/bash
#$ -j y
#$ -N {SGE_JOB_NAME}
#$ -e /dev/null
#$ -o /dev/null
#$ -cwd
#$ -P cath
#$ -t 1-{line_count}
PROJECT=$(head -n $SGE_TASK_ID {os.path.abspath(mda_list.name)} | tail -n 1)\n\

export DATADIR='{sfam_path}'
module load python/3.8.5
source {venv_path}

echo `date` ${{PROJECT}} START

awk -F ',' '{{print $1}}' ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_reps.csv > ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_ids_list 

cath-emma-cli create-distance-matrix --distance_source embeddings --input_to_process ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_embedded.pt --embedding_distance euclidean --matrix_output_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_embedding_matrix.ssv --labels_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_ids_list

mkdir -p ${{DATADIR}}/${{PROJECT}}/starting_clusters
mkdir -p ${{DATADIR}}/${{PROJECT}}/starting_clusters/${{PROJECT}}
echo ${{PROJECT}} > ${{DATADIR}}/${{PROJECT}}/projects.txt

cath-emma-cli create-starting-clusters-from-centroids --cluster_reps_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_reps.csv --starting_clusters_dir ${{DATADIR}}/${{PROJECT}}/starting_clusters/${{PROJECT}} --cluster_mapping_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_cluster_mapping.tsv
            """)
    LOG.info(f"Generated qsub script for embeddings generation -> {output_script.name}")