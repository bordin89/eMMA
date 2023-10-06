# eMMA
Functional Families generation using embedding distance matrices 

Overview
---------

Fork of CATH-Gemma switching the core from HHsuite to embeddings or structural distances. 

### Main features

- Revised protocol to use MMseqs2 instead of CD-HIT. 
- Python CLI generating SGE or local jobs
- embedding distances or 1/bitscore distances from Foldseek as data source for functional relationships

This repo is part of the FunFams pipeline as an intermediate step before FunFHMMER. 

The eMMA version of FunFHMMER can be found at [funfhmmer-emma](https://github.com/UCL/cath-funfhmmer/tree/funfhmmer-emma)

See the GeMMA [Wiki](https://github.com/UCL/cath-gemma/wiki) for documentation on GEMMA and check out the step-by-step walkthrough [here](https://github.com/bordin89/eMMA/blob/main/step-by-step-walkthrough.md).
