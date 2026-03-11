# Bioinformatics Sidecar — Package Reference

Curated packages for scientific bioinformatics research and thesis writing.
Organized by research phase, not alphabetically.

---

## 1. Data I/O — Reading Your Raw Data

These are non-negotiable. Every bioinformatics pipeline starts here.

### Python

| Package | What it does | Sidecar script idea |
|---------|-------------|-------------------|
| **Biopython** | FASTA/FASTQ/GenBank/PDB parsing, NCBI Entrez, BLAST, sequence alignment | `bio.py seq fetch --ncbi NM_001234` |
| **pysam** | SAM/BAM/CRAM/VCF files — read alignment data from NGS experiments | `bio.py bam stats sample.bam` |
| **HTSeq** | Count reads per gene from BAM + GTF annotation | `bio.py count reads.bam annotation.gtf` |
| **pyVCF3** / **cyvcf2** | VCF variant call format — fast, Cython-based | — |
| **h5py** | HDF5 files — used by 10x Genomics, scRNA-seq tools | — |
| **zarr** | Chunked cloud-ready array storage — large genomics matrices | — |
| **anndata** | Annotated data matrix — the universal format for single-cell data | — |
| **loompy** | Loom files — alternative single-cell storage format | — |

---

## 2. Genomics & Transcriptomics

The core bioinformatics analysis layer.

### Python

| Package | What it does | Use case |
|---------|-------------|---------|
| **scanpy** | Single-cell RNA-seq analysis — clustering, UMAP, trajectory | Full scRNA-seq pipeline |
| **PyDESeq2** | Differential gene expression (DEG) analysis in Python | RNA-seq DEG |
| **gseapy** | Gene Set Enrichment Analysis (GSEA) + Enrichr API | Pathway analysis |
| **goatools** | GO term enrichment, DAG traversal, semantic similarity | GO annotation |
| **mygene** | MyGene.info API — gene ID conversion, annotation | Gene lookup sidecar |
| **pyensembl** | Ensembl genome annotation — genes, transcripts, exons | Genome coordinate lookup |
| **pybedtools** | BED/GFF interval arithmetic — genomic region overlaps | Interval analysis |
| **deeptools** | NGS QC, bigWig, coverage, heatmaps | ChIP-seq / ATAC-seq |
| **MACS3** | Peak calling for ChIP-seq / ATAC-seq | Chromatin accessibility |
| **pyGenomeTracks** | Publication-quality genome browser plots | Thesis figures |
| **pyCirclize** | Circular genome / synteny plots (Circos-style) | Comparative genomics |
| **scvi-tools** | Variational autoencoders for single-cell — scVI, scANVI, totalVI | Deep learning scRNA |

### Sidecar script idea
```bash
# Gene annotation lookup
python sidecar/bio.py gene BRCA1 --info pathway,go,expression
# GO enrichment from a gene list
python sidecar/bio.py go gene_list.txt --organism human
```

---

## 3. Protein & Structural Biology

| Package | What it does | Use case |
|---------|-------------|---------|
| **BioPandas** | PDB/mmCIF → Pandas DataFrames | Structure analysis |
| **biotite** | Sequence + structure analysis, fast NumPy-based | Structure manipulation |
| **MDAnalysis** | Molecular dynamics trajectory analysis | MD simulations |
| **ProDy** | Protein dynamics, normal mode analysis, elastic networks | Flexibility analysis |
| **RDKit** | Cheminformatics — molecules, SMILES, fingerprints, descriptors | Drug discovery |
| **OpenMM** | GPU-accelerated MD simulation | Molecular simulation |
| **nglview** | 3D protein structure visualization in Jupyter | Notebook figures |
| **py3Dmol** | Lightweight 3D molecule viewer in notebooks | Quick structure viz |
| **esm** (Meta) | Protein language model embeddings — ESM-2, ESM-Fold | Protein ML |

---

## 4. ML/AI for Biology

The frontier — where thesis novelty usually lives.

### Python

| Package | What it does | Use case |
|---------|-------------|---------|
| **PyTorch Geometric** | Graph neural networks — molecules as graphs, PPI networks | GNN on proteins |
| **DGL-LifeSci** | Deep learning for drug discovery, molecular property prediction | Drug-target prediction |
| **scVI-tools** | VAE-based single-cell models with GPU support | Latent space biology |
| **CellChat** | Cell-cell communication inference from scRNA-seq | Signaling networks |
| **Harmony** | Batch integration for single-cell data | Multi-sample scRNA |
| **SCENIC** | Gene regulatory network inference | Transcription factors |
| **deepchem** | ML for chemistry — ADMET, binding affinity, quantum | Computational chemistry |
| **fair-esm** | Meta's ESM protein language models — embeddings + folding | Protein representation |
| **boltz** (EvolutionaryScale) | Biomolecular structure prediction | AlphaFold alternative |

---

## 5. Statistics & Data Analysis

| Package | What it does |
|---------|-------------|
| **scipy** | Statistical tests, signal processing, sparse matrices |
| **statsmodels** | Regression, GLMs, time series, hypothesis testing |
| **pingouin** | Statistical tests with effect sizes — cleaner than scipy.stats |
| **lifelines** | Survival analysis — Kaplan-Meier, Cox proportional hazards |
| **pymer4** | Mixed-effects models via R's lme4 (Python wrapper) |
| **polars** | Fast DataFrame library — much faster than pandas for large data |
| **pyarrow** | Columnar data, Parquet I/O — interop with R/Spark |

---

## 6. Database & Knowledge Access

Sidecar scripts that query external biomedical databases — huge time savers.

### Python

| Package / API | What it accesses | Sidecar script idea |
|---------------|-----------------|-------------------|
| **Biopython Entrez** | PubMed, NCBI Gene, NCBI Nucleotide, SRA | `literature.py pubmed "CRISPR 2024" --top 20` |
| **bioservices** | UniProt, KEGG, STRING, ChEMBL, Ensembl, Reactome REST APIs | `bio.py pathway BRCA1 --db kegg` |
| **mygene** | MyGene.info — fast gene annotation (symbol, alias, GO, pathway) | `bio.py gene-info TP53` |
| **pyuniprot** | UniProt protein annotation | Protein function lookup |
| **requests-cache** | Cache HTTP API responses — essential for rate-limited bio APIs | Used in all sidecar API scripts |
| **Bio.Entrez** | PubMed full-text fetch, abstracts, MeSH terms | Literature RAG pipeline |
| **europepmc** | Europe PMC API — open access full text retrieval | Full-text for RAG |

### Key public databases to integrate
```
NCBI    → genes, sequences, literature (Entrez API)
UniProt → protein function, domains, variants
STRING  → protein-protein interactions
KEGG    → metabolic pathways, drug targets
Reactome→ curated biological pathways
ChEMBL  → bioactive molecules, drug data
PDB     → 3D protein structures
GEO     → gene expression datasets
```

---

## 7. Visualization (Thesis Figures)

Publication-quality figures are critical for a thesis.

### Python

| Package | Strength | When to use |
|---------|----------|------------|
| **matplotlib** | Full control, publication defaults | All figures |
| **seaborn** | Statistical plots — violin, heatmap, clustermap | Distribution plots |
| **plotly** | Interactive — great for Gradio UI and notebooks | Exploratory analysis |
| **altair** | Grammar of graphics — declarative, elegant | Dashboard-style figures |
| **pyGenomeTracks** | Genome browser panels — multiple tracks | Genomic data figures |
| **pyCirclize** | Circos-style circular plots | Synteny, gene families |
| **nglview** | 3D protein structures in Jupyter | Structural figures |
| **cellpose** | Cell segmentation visualization | Microscopy data |
| **squidpy** | Spatial transcriptomics analysis + visualization | Spatial data |
| **anndata + scanpy plots** | UMAP, violin, dotplot for single-cell | scRNA-seq figures |

---

## 8. Thesis Writing & Reproducibility

The glue between analysis and publication.

### Python

| Package | What it does | Sidecar idea |
|---------|-------------|-------------|
| **Quarto** (CLI) | Reproducible papers, notebooks → PDF/HTML/DOCX | `thesis.py render chapter3.qmd` |
| **papermill** | Parameterized Jupyter notebooks — run with different inputs | Automated figure generation |
| **nbconvert** | Jupyter → PDF/LaTeX/HTML | `thesis.py export notebook.ipynb --format pdf` |
| **jupytext** | Sync notebooks ↔ plain Python scripts (git-friendly) | Version-controlled notebooks |
| **matplotlib** `rcParams` | Nature/Science journal figure styles | `thesis.py set-style nature` |
| **SciencePlots** | matplotlib styles for journals (Nature, IEEE, MNRAS) | Publication figures |
| **latexify-py** | Convert Python functions to LaTeX math | Methods section |
| **bibtexparser** | Parse .bib files — validate, deduplicate, format | Reference management |

### Node.js / CLI Tools

| Tool | What it does |
|------|-------------|
| **Pandoc** (CLI) | Universal document converter — Markdown → LaTeX → Word → PDF |
| **citation-js** | Citation formatting, DOI lookup, BibTeX → APA/Vancouver |
| **zotero-cli** | Zotero reference manager from terminal |

### Sidecar script ideas
```bash
# Fetch paper citation info from DOI
python sidecar/thesis.py cite 10.1038/s41586-021-03819-2 --format vancouver

# Validate all citations in your .bib file
python sidecar/thesis.py bib-check references.bib

# Generate Methods section draft from a pipeline config
python sidecar/thesis.py methods-draft pipeline_config.yaml
```

---

## 9. Workflow & Reproducibility

| Tool | Language | What it does |
|------|----------|-------------|
| **Snakemake** | Python | Pipeline DAGs with automatic re-runs on file changes |
| **Nextflow** | DSL2 | Cloud-ready bioinformatics pipelines (nf-core community) |
| **Prefect** | Python | Modern workflow orchestration with UI |
| **DVC** | Python | Data version control — track large files in git |
| **conda-lock** | Python | Reproducible conda environments |
| **nf-core tools** | Python CLI | Access 100+ validated bioinformatics pipelines |

---

## 10. LLM + RAG for Literature Research

Extending the sidecar for AI-assisted research.

### Python

| Package | What it does |
|---------|-------------|
| **langchain** | LLM orchestration, document loaders, chains |
| **langgraph** | Agentic workflows with state machines |
| **langchain-ollama** | Ollama integration for local LLMs |
| **docling** | Scientific PDF parsing — tables, figures, equations |
| **marker-pdf** | Fast PDF → Markdown (good for text-heavy papers) |
| **arxiv** | arXiv API Python wrapper |
| **semanticscholar** | Semantic Scholar API — citations, references, authors |
| **habanero** | CrossRef API — DOI metadata, journal info |
| **pgvector** | pgvector Python client |
| **chromadb** | Lightweight local vector DB (alternative to pgvector) |
| **rank-bm25** | Pure Python BM25 for keyword search |

### Sidecar scripts enabled
```bash
# Find all papers that cite a specific paper
python sidecar/literature.py citing 2401.12345 --top 20

# Summarize a paper's methods section
python sidecar/literature.py summarize paper.pdf --section methods

# Generate related work draft from your indexed collection
python sidecar/literature.py related-work "batch correction single-cell"
```

---

## Recommended Starting Stack (Week 1)

If you install nothing else, start with these:

```bash
uv add \
  biopython \          # foundational bio I/O
  scanpy anndata \     # single-cell (most used in current research)
  gseapy goatools \    # pathway/GO enrichment
  scienceplots \       # publication figures immediately
  papermill \          # reproducible notebook runs
  semanticscholar \    # literature discovery
  bioservices          # UniProt/KEGG/STRING APIs
```

---

## What to Research on arXiv for Each

| Topic | arXiv search |
|-------|-------------|
| Single-cell methods | `"single-cell RNA" "deep learning" 2024` |
| Protein language models | `"protein language model" ESM 2024` |
| Graph neural networks for biology | `"graph neural network" genomics protein 2024` |
| RAG for biomedical literature | `"retrieval augmented generation" biomedical 2024` |
| Foundation models biology | `"foundation model" biology genomics 2024` |
| Spatial transcriptomics | `"spatial transcriptomics" analysis method 2024` |
