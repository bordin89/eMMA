import torch
import os
import numpy as np
import click
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

LOG = logging.getLogger(__name__)


@click.command()
@click.option(
    "--distance_source",
    type=click.Choice(["foldseek", "embeddings"]),
    help="Parameter: Source of distances, either from embeddings or Foldseek scans",
    required=True,
)
@click.option(
    "--input_to_process",
    type=str,
    help="Input: PT file from ESM embeddings or Foldseek ouput",
    required=True,
)
@click.option(
    "--embedding_distance",
    type=click.Choice(["cosine", "euclidean"]),
    help="Parameter: Embedding distance metric. (default: euclidean)",
    default="euclidean",
)
@click.option(
    "--matrix_output_file",
    type=click.File("wt"),
    required=True,
    help="Output: Distance matrix file for eMMA input",
)
@click.option(
    "--labels_file",
    type=click.File("rt"),
    required=True,
    help="Input: List of labels (i.e. sequence identifiers) used in embeddings or foldseek search",
)
def create_distance_matrix(
    distance_source,
    input_to_process,
    embedding_distance,
    matrix_output_file,
    labels_file,
):
    """
    Create distance matrix based on embedding distances or Foldseek 1/bitscore distances
    """
    LOG.info(f"Processing: {input_to_process} source: {distance_source}")
    nodes_labels = create_list_of_labels(labels_file)
    labels_list = list(nodes_labels)

    # Foldseek distances based on (1/bitscore)
    if distance_source == "foldseek":
        fh_type = "rt"
        foldseek_output_fh = open(input_to_process, fh_type)
        foldseek_results = {}
        for line in foldseek_output_fh:
            results = line.split()
            query, target, bitscore = results[0], results[1], results[-1]
            foldseek_results[f"{query}{target}"] = bitscore
        for i in range(len(labels_list)):
            for j in range(i, len(labels_list)):
                label1 = labels_list[i]
                label2 = labels_list[j]
                pair = f"{label1}{label2}"
                reverse_pair = f"{label2}{label1}"
                if label1 == label2:
                    matrix_output_file.write(f">{label1} >{label2} 0.0\n")
                    continue
                elif pair in foldseek_results:
                    LOG.info(pair)
                    LOG.info(foldseek_results[pair])
                    matrix_output_file.write(
                        f">{label1} >{label2} {float(1/int(foldseek_results[pair]))}\n"
                    )
                elif reverse_pair in foldseek_results:
                    LOG.info(reverse_pair)
                    matrix_output_file.write(
                        f">{label2} >{label1} {float(1/int(foldseek_results[reverse_pair]))}\n"
                    )
                else:
                    matrix_output_file.write(f">{label1} >{label2} 100\n")

    # Embeddings distances (euclidean or cosine)
    elif distance_source == "embeddings":
        fh_type = "rb"
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
        embedding_fh = open(input_to_process, fh_type)
        embeddings = torch.load(embedding_fh, map_location=device)
        embedding_dict = {}
        for embedding in embeddings:
            label = embedding["label"]
            embedding_dict[label] = embedding["mean_representations"][33]
        if embedding_distance == "cosine":
            distance = cosine_distance
        else:
            distance = euclidean_distance
        for i in range(len(labels_list)):
            for j in range(i, len(labels_list)):
                label1 = labels_list[i]
                label2 = labels_list[j]
                if label1 in embedding_dict and label2 in embedding_dict:
                    matrix_output_file.write(
                        f">{label1} >{label2} {distance(embedding_dict[label1],embedding_dict[label2])}\n"
                    )
                else:
                    matrix_output_file.write(f">{label1} >{label2} 100\n")
    else:
        LOG.error("Unknown source for matrix data")
    LOG.info("DONE")


def euclidean_distance(embedding1, embedding2):
    return np.linalg.norm(embedding1 - embedding2)


def cosine_distance(embedding1, embedding2):
    cosine_sim = torch.nn.functional.cosine_similarity(embedding1, embedding2, dim=0)
    cosine_dist = 1 - cosine_sim
    return cosine_dist


def create_list_of_labels(labels_fh):
    labels_set = set()
    for line in labels_fh:
        label = line.rstrip()
        labels_set.add(label)
    return labels_set

