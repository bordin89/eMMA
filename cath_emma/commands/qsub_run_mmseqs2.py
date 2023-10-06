import click
import os
import logging
from .qsub_to_embeddings import count_lines

SGE_TMEM = "16G"
SGE_H_RT = "1:0:0"
SGE_JOB_NAME = "emma-mmseqs2"

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
    "--mmseqs_bin_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="Path MMseqs2 bin directory"
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


def qsub_to_mmseqs2(mda_list,mmseqs_bin_dir,sfam_path,venv_path,output_script):
    """Generate SGE QSUB file to generate S90 clusters using MMseqs2"""
    line_count = count_lines(mda_list)
    output_script.write(
        f"""\
#$ -l tmem={SGE_TMEM}
#$ -l h_vmem={SGE_TMEM}
#$ -l h_rt={SGE_H_RT}
#$ -S /bin/bash
#$ -e /dev/null
#$ -o /dev/null
#$ -j y
#$ -N {SGE_JOB_NAME}
#$ -cwd
#$ -P cath
#$ -t 1-{line_count}
PROJECT=$(head -n $SGE_TASK_ID {os.path.abspath(mda_list.name)} | tail -n 1)\n\
DATADIR={sfam_path}
module load python/3.8.5
source {venv_path}

echo `date` ${{PROJECT}} START

{mmseqs_bin_dir}/mmseqs easy-cluster ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}.fasta ${{DATADIR}}/${{PROJECT}}/${{PROJECT}} ${{DATADIR}}/${{PROJECT}}/tmp_${{PROJECT}} -s 7.5 --min-seq-id 0.9 --cov-mode 4 -c 0.95
cath-emma-cli convert-fasta-to-csv-for-embed --input_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_rep_seq.fasta --output_file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}_reps.csv
echo `date` ${{PROJECT}} DONE
""")
    LOG.info(f"Generated qsub script for MMseqs2 -> {output_script.name}")