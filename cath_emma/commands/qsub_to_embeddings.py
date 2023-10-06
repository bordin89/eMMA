import click
import logging
import os

SGE_TMEM = "12G"
SGE_H_RT = "4:0:0"
SGE_JOB_NAME = "esm_embed"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

LOG = logging.getLogger(__name__)

@click.command()
@click.option(
    "--qsub_output_file",
    type=click.File("wt"),
    required=True,
    help="Output: bash script for SGE job submission to generate embeddings",
)
@click.option(
    "--array_job",
    type=click.Choice(["True", "False"]),
    default="True",
    help="Input: Flag for array job. Requires list of projects. (default: True)",
)
@click.option(
    "--project_path",
    required=True,
    default=os.getcwd(),
    help="Input: Absolute path to folder containing the projects or individual run",
)
@click.option(
    "--project_list_file",
    type=click.File("rt"),
    default=None,
    help="Input: file containing project ids for array processing. optional, required if array_job set to True",
)
@click.option(
    "--sequence_suffix",
    type=str,
    default="_reps.csv",
    help="Input: suffix of csv file containing sequences in case of project id. example \{project\}_reps.csv -> _reps.csv",
)
@click.option(
    "--embeddings_suffix",
    type=str,
    default="_embedded.pt",
    help="Input: suffix of embeddings file containing sequences in case of project id. example \{project\}_embedded.pt -> _embedded.pt",
)
@click.option(
    "--venv_location",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
    help="Input: Path to venv/bin/activate location with required packages installed for cath-emma-cli",
)
@click.option(
    "--input_sequence_csv_path",
    type=str,
    default=None,
    help="Input: String containing the path to the input sequence csv.",
)
@click.option(
    "--embeddings_output_path",
    type=str,
    default=None,
    help="Input: String containing the path where the embeddings will be stored.",
)
@click.option(
    "--esm_model",
    type=str,
    default="esm2",
    help="Input: String containing the type of ESM model to use. (default: esm2)",
)
def qsub_to_embeddings(
    qsub_output_file,
    array_job,
    project_path,
    project_list_file,
    sequence_suffix,
    embeddings_suffix,
    venv_location,
    input_sequence_csv_path,
    embeddings_output_path,
    esm_model,
):
    """Generate a qsub job for calculating ESM2 embeddings using calculate_esm_embeddings module"""
    qsub_output_file.write(
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
#$ -l gpu=true
#$ -P cath
"""
    )
    if array_job == "True":
        line_count = count_lines(project_list_file)
        qsub_output_file.write(
            f"""\
#$ -t 1-{line_count}
DATADIR={project_path}
PROJECT_ID=$(head -n $SGE_TASK_ID {os.path.abspath(project_list_file.name)} | tail -n 1)\n\
"""
        )
    qsub_output_file.write(
        f"""\
echo `date` start
module load python/3.8.5
source {venv_location}\
"""
    )
    project = ""
    input_sequence = input_sequence_csv_path
    embeddings_output = embeddings_output_path
    if array_job == "True":
        project_path  = f"${{DATADIR}}"
        project = f"${{PROJECT_ID}}"
        input_sequence = f"{project}{sequence_suffix}"
        embeddings_output = f"{project}{embeddings_suffix}"
    qsub_output_file.write(
        f"""
cath-emma-cli calculate-esm-to-embed --input_sequence_csv {project_path}/{project}/{input_sequence} --embeddings_output {project_path}/{project}/{embeddings_output} --esm_model {esm_model}
"""
    )
    LOG.info(f"Generated qsub script for embeddings generation -> {qsub_output_file.name}")

def count_lines(filehandle):
    sum = 0
    for line in filehandle:
        sum += 1
    return sum
