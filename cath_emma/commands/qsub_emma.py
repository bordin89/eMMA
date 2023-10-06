import click
import os
import logging
from .qsub_to_embeddings import count_lines

SGE_TMEM = "16G"
SGE_H_RT = "12:0:0"
SGE_JOB_NAME = "emma"

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
    "--plenv_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="Path to plenv Perl (plenv) with installed dependencies for GeMMA (i.e. /home/nbordin/.plenv/versions/5.20.2/bin/perl)"
    )
@click.option(
    "--distance_matrix",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
    help="Path to distance file (either embeddings or Foldseek based)"
)
@click.option(
    "--output_script",
    type=click.File("wt"),
    required=True,
    help="Output: QSUB bash script for launching eMMA."
    )
@click.option(
    "--matrix_suffix",
    type=str,
    default="_embedding_matrix.ssv",
    help="Input: suffix of csv file containing sequences in case of project id. example \{project\}_reps.csv -> _reps.csv",
)
@click.option(
    "--code_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="Path to cath-emma repository"
    )
def qsub_emma_input_to_emma_output(mda_list,sfam_path,plenv_path,distance_matrix,output_script,matrix_suffix,code_dir):
    """Create eMMA qsub file"""
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
export CODE_DIR='{code_dir}'
echo $(date) ${{PROJECT}} START

# Swap for embeddings location file once added as an option to perl GeMMA. Switch distance matrix required to True.

{plenv_path}/perl ${{CODE_DIR}}/Cath-Gemma/script/prepare_research_data.pl \\
    --local \\
    --projects-list-file ${{DATADIR}}/${{PROJECT}}/projects.txt \\
    --output-root-dir ${{DATADIR}}/${{PROJECT}} \\
    --tmp-dir /dev/shm/ \\
    --embs-file ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}{matrix_suffix}
    1> ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}.stdout \\
    2> ${{DATADIR}}/${{PROJECT}}/${{PROJECT}}.stderr

echo $(date) ${{PROJECT}} END
            """)
    LOG.info(f"Generated qsub script for {line_count} eMMA projects on {sfam_path} -> {output_script.name}")