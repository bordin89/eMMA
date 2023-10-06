# CATH-eMMA workflow

### Overview of steps involved (repeat for each SuperFamily):

#### Create starting files

- Export project variables 

- Activate Environment

- Fetch MDA projects in folders

- Run MMseqs to generate S90 clusters (module: cath-emma-cli qsub_to_mmseqs2)

- Convert S90 to TSV for Embeddings generation (or on the side generate Foldseek all-vs-all) (part of cath-emma-cli qsub_to_mmseqs2)

- Create job submission scripts to generate embeddings (cath-emma-cli qsub-to-embeddings) 

- Generate embeddings using previous step via qsub

- Run SGE job to generate eMMA input from embeddings (cath-emma-cli qsub_embeddings_to_emma_input)

- Run qsub_emma_run (make sure perl or plenv is set up correctly with dependencies)

-

### 1. Export Project Variables
- PARENTDIR = `/SAN/cath/cath_v4_3_0/embed_sfams` (i.e. Parent directory containing all CATH SuperFamily DATADIRs)
- DATADIR = `/SAN/cath/cath_v4_3_0/embed_sfams/3.40.50.620` (i.e. path to your superfamily)
- CODE_DIR= `/SAN/cath/cath_v4_3_0/embed_sfams/cath-emma` (i.e path to emma repository)
- PROJECTLIST = `/SAN/cath/cath_v4_3_0/embed_sfams/mda_list` (i.e. list of MDA folders in SuperFamily)

```
export PARENTDIR='/SAN/cath/cath_v4_3_0/embed_sfams'
export DATADIR='/SAN/cath/cath_v4_3_0/embed_sfams/3.40.50.620'
export PROJECTLIST='${PARENTDIR}/mda_list'
export CODE_DIR='/SAN/cath/cath_v4_3_0/embed_sfams/cath-emma'
```

Current working directory (PARENTDIR): /SAN/cath/cath_v4_3_0/embed_sfams

PROJECTLIST = ${DATADIR}/mda_list

Individual mdas data are organised as 
`
cwd: ${DATADIR}/${PROJECT}/${PROJECT}.fasta
`

### 2. Activate environment

- Run module load python/3.8.5

- Activate venv

- Update PIP 

`
pip install --upgrade pip wheel
`

- Change directory to CATH-eMMA repo and install requirements

```
cd ${CODE_DIR}
pip install -e . 
```

Call the CLI using cath-emma-cli. It should return all available modules


### 3. Run MMseqs to generate S90 clusters

Switching from CD-HIT to MMseqs. 

MMseqs has a guide to convert the CD-HIT behaviour to MMseqs in its user guide, found here https://mmseqs.com/latest/userguide.pdf at page 70

Batch processing via qsub (RECOMMENDED) 

```
cath-emma-cli qsub-to-mmseqs2 --mda_list mda_list_test --mmseqs_bin_dir ${PARENTDIR}/mmseqs/bin --sfam_path ${DATADIR} --venv_path ${PARENTDIR}/venv/bin/activate --output_script ${PARENTDIR}/001_run_mmseqs_mda.sh
qsub ${PARENTDIR}/001_run_mmseqs_mda.sh
```

or command for one MDA

`
mmseqs/bin/mmseqs easy-cluster ${DATADIR}/${PROJECT}/${PROJECT}.fasta ${DATADIR}/${PROJECT}/${PROJECT} tmp_${PROJECT} -s 7.5 --min-seq-id 0.9 --cov-mode 4 -c 0.95
`


### 4. Convert S90 Reps to TSV file for embedding generation

This step is taken care of by the qsub-to-mmseqs2 module. For reference, the command launched by qsub-to-mmseqs2 is:

`
cath-emma-cli convert-fasta-to-csv-for-embed --input_file ${DATADIR}/${PROJECT}/${PROJECT}_rep_seq.fasta --output_file ${DATADIR}/${PROJECT}/${PROJECT}_reps.csv
`


### 5. Create job submission scripts to generate embeddings

```
cath-emma-cli qsub-to-embeddings --qsub_output_file ${PARENTDIR}/002_submit_embeddings_qsub.sh --array_job True --project_list_file ${PARENTDIR}/mda_list --venv_location ${PARENTDIR}/venv/bin/activate --sequence_suffix _reps.csv --project_path ${DATADIR}
qsub ${PARENTDIR}/002_submit_embeddings_qsub.sh
```



Edit script to change time requirements if needed by large SFAMS (?). It seems that the largest MDA in the HUPs takes 4 hours (with a lot of wiggle room) on GPU, 120 hours on CPU.

### 6. Create embeddings or Foldseek half-matrix

The next qsub module takes care of step 6, 7 and 8
This is done using the `qsub-embeddings-to-emma-input` module as follows:

```
cath-emma-cli qsub-embeddings-to-emma-input --mda_list ${PARENTDIR}/mda_list_test --sfam_path ${DATADIR} --venv_path ${PARENTDIR}/venv/bin/activate --output_script ${PARENTDIR}/003_submit_embeddings_to_emma.sh
qsub ${PARENTDIR}/003_submit_embeddings_to_emma.sh
```

In order to generate a full matrix, particularly with Foldseek since it limits the number of hits in the output (or there aren't any above the thresold), we need to generate a list of cluster representatives in order to generate a full matrix. 
For both embeddings distances and Foldseek distances this is set by default as a distance of 100. (Adjust if needed).


`
awk -F ',' '{print $1}' $DATADIR/${PROJECT}/${PROJECT}_reps.csv > $DATADIR/${PROJECT}/${PROJECT}_ids_list
`

`
cath-emma-cli create-distance-matrix --distance_source embeddings --input_to_process ${DATADIR}/${PROJECT}/${PROJECT}_embedded.pt --embedding_distance euclidean --matrix_output_file ${DATADIR}/${PROJECT}/${PROJECT}_embedding_matrix_test.ssv --labels_file ${DATADIR}/${PROJECT}/${PROJECT}_ids_list
`

### 7. Create starting_clusters folder and project

```
mkdir ${DATADIR}/${PROJECT}/starting_clusters
mkdir ${DATADIR}/${PROJECT}/starting_clusters/${PROJECT}
echo $PROJECT > ${DATADIR}/${PROJECT}/projects.txt
```



### 8. Create fasta for each centroid in starting_clusters/{project_name}

Requirements:

- CSV file created from convert-fasta-to-csv-for-embed

- starting_clusters folder and project ID

Output:

- starting_cluster/project populated with starting clusters (cluster representatives/centroids from MMseqs2)

`
cath-emma-cli create-starting-clusters-from-centroids --cluster_reps_file ${DATADIR}/${PROJECT}/${PROJECT}_reps.csv --starting_clusters_dir ${DATADIR}/${PROJECT}/starting_clusters/${PROJECT} --cluster_mapping_file ${DATADIR}/${PROJECT}/${PROJECT}_cluster_mapping.tsv
`

### 9. Run eMMA 

Requirements:

- Plenv https://github.com/tokuhirom/plenv 
- Install eMMA PERL dependencies in plenv

```
cath-emma-cli qsub-emma-input-to-emma-output --mda_list ${PARENTDIR}/mda_list_test --sfam_path ${DATADIR} --plenv_path /home/nbordin/.plenv/versions/5.20.2/bin --output_script ${PARENTDIR}/004_submit_emma.sh --code_dir ${PARENTDIR}/cath-emma
qsub 004_submit_emma.sh
```

This cli module generates a QSUB script to run eMMA in local mode.

~/.plenv/versions/5.20.2/bin/perl <emma_repository>/Cath-Gemma/script/prepare_research_data.pl --local --projects-list-file projects.txt --output-root-dir .  

### 10. Generate qsub to repopulate starting clusters with sequences. 

The qsub runs 

```
cath-emma-cli populate-cluster-centroids \\
    --cluster_reps_file ${DATADIR}/${PROJECT}/${PROJECT}_reps.csv \\
    --all_fasta ${DATADIR}/${PROJECT}/${PROJECT}.fasta \\
    --centroids_tree_dir ${DATADIR}/${PROJECT}/trees/${PROJECT}/simple_ordering.hhconsensus.windowed \\
    --filled_tree_dir ${DATADIR}/${PROJECT}/filled_tree_first_iter \\
    --starting_clusters_mapping_file ${DATADIR}/${PROJECT}/${PROJECT}_cluster_mapping.tsv \\
    --mmseqs_cluster_mapping ${DATADIR}/${PROJECT}/${PROJECT}_cluster.tsv 
```


Output:

- Starting clusters (full) folder
- Populated clusters, both starting and merge_node

```
cath-emma-cli qsub-emma-to-ff-input \
    --mda_list ${PARENTDIR}/mda_list \
    --venv_path ${PARENTDIR}/venv/bin/activate \
    --sfam_path ${DATADIR} \
    --output_script ${PARENTDIR}/005_submit_emma_to_ff_input.sh

qsub 005_submit_emma_to_ff_input.sh
```


### Run FunFHMMER

Requirements:

- Plenv https://github.com/tokuhirom/plenv 
- Install FunFHMMER using the instructions at 
https://github.com/UCL/cath-funfhmmer/tree/funfhmmer-emma
and install dependencies in Plenv

```
git clone -b funfhmmer_v2.2 git@github.com:UCL/cath-funfhmmer.git 
cd cath-funfhmmer/funfhmmer
<your plenv perl> Makefile.PL
<your plenv cpanm> --installdeps . 
```




