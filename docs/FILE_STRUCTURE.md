# File Structure — `D:\autogc_validation`

Generated 2026-09-01. Reflects the state of the filesystem at generation time — regenerate to refresh, since `data/`, `validation/`, and `ezchrom/` grow monthly.

## Conventions

- **Excluded entirely** (not shown): `.claude/`, `.pytest_cache/`, `.git/`, `__pycache__/`, `*.egg-info`, `.ipynb_checkpoints/` — tool caches and build artifacts with no documentation value.
- **`data/`, `validation/`, `ezchrom/`**: shown only down to the two-letter site-code folder (`ED`, `EQ`, `HW`, `LP`, `RB`) — these are per-site working folders that grow monthly and hold hundreds of thousands of files combined, so they are not expanded further. Each site folder is annotated with its total subfolder and file count instead.
- **Collapsed** (name shown, contents not expanded): vendored/generated subtrees such as `.quarto/` render caches, flagged inline as *(vendored/generated — not expanded)*.
- **Summarized**: outside of `data/`/`validation/`/`ezchrom/`, any folder holding more than 30 files directly lists a count, a breakdown by extension, and 3 example filenames instead of every file (e.g. `docs/gc_files/`).
- Everything else (code, docs, notebooks, templates, config) is listed in full.

## Top-level layout

- `data/` — raw AutoGC chromatogram exports, organized `<SITE>/<YYYYMM>/`
- `docs/` — reference PDFs, SOPs, and GC control-software files
- `ezchrom/` — EZChrom instrument software exports per site (Method/Result/Sample Prep/Sequence/Template)
- `misc/` — one-off analysis
- `notebooks/` — Jupyter notebooks for database management, investigations, and presentations
- `src/autogc_validation/` — the installable Python package (database, io, qc, plots, reports, workspace modules)
- `templates/` — case narrative and MDVR Excel templates
- `tests/` — pytest suite
- `validation/` — per-site, per-month validation working folders (AQS submissions, FINAL/Original data, MDVR packages, case narratives)

## Tree

```text
autogc_validation/
├── data/
│   ├── ED/  *(not expanded — 1 subfolders, 0 files)*
│   ├── EQ/  *(not expanded — 15 subfolders, 18996 files)*
│   ├── HW/  *(not expanded — 1 subfolders, 288 files)*
│   ├── LP/  *(not expanded — 15 subfolders, 19016 files)*
│   ├── RB/  *(not expanded — 4 subfolders, 4268 files)*
│   ├── .gitkeep
│   ├── autogc.db
│   └── autogc.sql
├── docs/
│   ├── gc_files/
│   │   └── MMove/
│   │       └── *(38 files: .txt x32, .dll x2, .exe x2, .ini x1, .dat x1; e.g. Ionic.Zip.dll, Log01.txt, Log02.txt, ...)*
│   │   └── *(31 files: .exe x14, .txt x13, .xlsm x1, .xlsx x1, .ini x1, .dll x1; e.g. AS.txt, L1.txt, L2.txt, ...)*
│   ├── 2023 QUAP.docx.pdf
│   ├── aqs_data_coding_manual.pdf
│   ├── CDS-Admin Guide.pdf
│   ├── CDS_EZ-users-guide.pdf
│   ├── data-validation-guidance-document-final-august-2021.pdf
│   ├── FILE_STRUCTURE.md
│   ├── Final Handbook Document 1_17.pdf
│   ├── PAMS QAPP R1 May 2023 (1) (1).pdf
│   ├── RB-AQS uploading.md
│   ├── sop_auto-gc_markes_agilent_draft_october_2020 (5).docx
│   ├── TAD R3 May 2023.pdf
│   ├── TI_TOC1250G_TOCGasGenerator.pdf
│   ├── UDAQ40_JANUARY2025AutoGC operations.pdf
│   └── UDAQ41 AutoGC Validation Revision 3 (2) (1).pdf
├── ezchrom/
│   ├── EQ/  *(not expanded — 6 subfolders, 39 files)*
│   ├── HW/  *(not expanded — 5 subfolders, 38 files)*
│   ├── LP/  *(not expanded — 6 subfolders, 102 files)*
│   ├── RB/  *(not expanded — 2 subfolders, 39 files)*
│   └── .gitkeep
├── misc/
│   └── 2methyl2butene/
│       └── 2methyl2butene.xlsx
├── notebooks/
│   ├── aqs_files_to_review/
│   │   ├── RB_SITE-RB_RedButte_INSERT_06-01-2025_to_06-30-2025 (2).txt
│   │   ├── RD_SITE-RB_RedButte_INSERT_06-01-2025_to_06-30-2025 (3).txt
│   │   ├── RD_SITE-RB_RedButte_INSERT_07-01-2025_to_07-31-2025 (2).txt
│   │   ├── RD_SITE-RB_RedButte_INSERT_09-01-2025_to_09-30-2025 (2).txt
│   │   ├── RD_SITE-RB_RedButte_INSERT_10-01-2025_to_10-31-2025.txt
│   │   ├── RD_SITE-RB_RedButte_INSERT_11-01-2025_to_11-30-2025.txt
│   │   └── RD_SITE-RB_RedButte_INSERT_12-01-2025_to_12-31-2025 (1).txt
│   ├── database/
│   │   ├── add_sites.ipynb
│   │   ├── eq_db_management.ipynb
│   │   ├── hw_db_management.ipynb
│   │   ├── lp_db_management.ipynb
│   │   └── rb_db_management.ipynb
│   ├── investigations/
│   │   └── LP_ethane/
│   │       ├── .quarto/  *(vendored/generated — not expanded)*
│   │       ├── amount_crosstab_run_[B].csv
│   │       ├── amount_crosstab_run_[C].csv
│   │       ├── amount_crosstab_run_[E].csv
│   │       ├── amount_crosstab_run_[Q].csv
│   │       ├── amount_crosstab_run_[S].csv
│   │       ├── ethane_benzene_timeseries.png
│   │       ├── lp_blanks.py
│   │       ├── LP_ethane.ipynb
│   │       ├── lp_ethane.pdf
│   │       ├── lp_ethane.py
│   │       ├── lp_ethane.qmd
│   │       ├── lp_ethane.quarto_ipynb_1
│   │       ├── lp_ethane.quarto_ipynb_10
│   │       ├── lp_ethane.quarto_ipynb_11
│   │       ├── lp_ethane.quarto_ipynb_12
│   │       ├── lp_ethane.quarto_ipynb_13
│   │       ├── lp_ethane.quarto_ipynb_14
│   │       ├── lp_ethane.quarto_ipynb_2
│   │       ├── lp_ethane.quarto_ipynb_3
│   │       ├── lp_ethane.quarto_ipynb_4
│   │       ├── lp_ethane.quarto_ipynb_5
│   │       ├── lp_ethane.quarto_ipynb_6
│   │       ├── lp_ethane.quarto_ipynb_7
│   │       ├── lp_ethane.quarto_ipynb_8
│   │       └── lp_ethane.quarto_ipynb_9
│   ├── presentations/
│   │   ├── 20260721/
│   │   │   ├── cdf_out/
│   │   │   │   ├── EQSC01Gdat-Back Signal.cdf
│   │   │   │   ├── EQSC01Gdat-Front Signal.cdf
│   │   │   │   ├── EQSC01Kdat-Back Signal.cdf
│   │   │   │   └── EQSC01Kdat-Front Signal.cdf
│   │   │   ├── result_sequence/
│   │   │   │   ├── EQSC01G.dat.tx1
│   │   │   │   └── EQSC01K.dat.tx1
│   │   │   ├── test_data/
│   │   │   │   ├── EQBC01C.dat
│   │   │   │   ├── EQCC01A.dat
│   │   │   │   ├── EQCC01B.dat
│   │   │   │   ├── EQSC01D.dat
│   │   │   │   ├── EQSC01E.dat
│   │   │   │   ├── EQSC01F.dat
│   │   │   │   ├── EQSC01G.dat
│   │   │   │   ├── EQSC01H.dat
│   │   │   │   ├── EQSC01I.dat
│   │   │   │   ├── EQSC01J.dat
│   │   │   │   ├── EQSC01K.dat
│   │   │   │   ├── EQSC01L.dat
│   │   │   │   ├── EQSC01M.dat
│   │   │   │   ├── EQSC01N.dat
│   │   │   │   ├── EQSC01O.dat
│   │   │   │   ├── EQSC01P.dat
│   │   │   │   ├── EQSC01Q.dat
│   │   │   │   ├── EQSC01R.dat
│   │   │   │   ├── EQSC01S.dat
│   │   │   │   ├── EQSC01T.dat
│   │   │   │   ├── EQSC01U.dat
│   │   │   │   ├── EQSC01V.dat
│   │   │   │   ├── EQSC01W.dat
│   │   │   │   └── EQSC01X.dat
│   │   │   ├── cdf.py
│   │   │   ├── chrom.py
│   │   │   ├── chrom_parser.ipynb
│   │   │   ├── dataset.py
│   │   │   ├── samples.py
│   │   │   └── test_method.met
│   │   ├── 20260625PAMScall.ipynb
│   │   └── image.png
│   ├── check_aqs.ipynb
│   ├── EQ_MDVR_template.xlsx
│   ├── MDVR_template_test.xlsx
│   ├── move_txt_files.ipynb
│   ├── so2spike.ipynb
│   ├── start_month.ipynb
│   ├── test.ipynb
│   ├── todo.ipynb
│   ├── Untitled.ipynb
│   └── workspace_workflow.ipynb
├── src/
│   └── autogc_validation/
│       ├── database/
│       │   ├── airvision/
│       │   │   ├── __init__.py
│       │   │   └── station_temp.py
│       │   ├── conn/
│       │   │   ├── __init__.py
│       │   │   └── connection.py
│       │   ├── enums/
│       │   │   ├── __init__.py
│       │   │   ├── canister_type.py
│       │   │   ├── column_type.py
│       │   │   ├── compound_code.py
│       │   │   ├── compound_name.py
│       │   │   ├── concentration_unit.py
│       │   │   ├── priority.py
│       │   │   ├── qualifier_code.py
│       │   │   ├── sample_type.py
│       │   │   ├── sites.py
│       │   │   └── voc_category.py
│       │   ├── management/
│       │   │   ├── __init__.py
│       │   │   ├── __main__.py
│       │   │   ├── backup.py
│       │   │   └── init_db.py
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── calibration.py
│       │   │   ├── canister.py
│       │   │   ├── mdl.py
│       │   │   ├── site.py
│       │   │   ├── version.py
│       │   │   └── voc.py
│       │   ├── operations/
│       │   │   ├── __init__.py
│       │   │   ├── calibrations.py
│       │   │   ├── canister_info.py
│       │   │   ├── create_table.py
│       │   │   ├── delete.py
│       │   │   ├── get_table.py
│       │   │   ├── insert.py
│       │   │   ├── mdl_info.py
│       │   │   ├── update.py
│       │   │   └── voc_info.py
│       │   ├── utils/
│       │   │   ├── __init__.py
│       │   │   └── data_loaders.py
│       │   ├── __init__.py
│       │   └── config.py
│       ├── io/
│       │   ├── __init__.py
│       │   ├── cdf.py
│       │   ├── samples.py
│       │   └── txt.py
│       ├── plots/
│       │   ├── __init__.py
│       │   ├── ambient.py
│       │   ├── distribution.py
│       │   ├── qc.py
│       │   ├── recovery.py
│       │   ├── room_temp.py
│       │   ├── rt.py
│       │   └── summary.py
│       ├── qc/
│       │   ├── __init__.py
│       │   ├── blanks.py
│       │   ├── calibrations.py
│       │   ├── precision.py
│       │   ├── recovery.py
│       │   ├── room_temp.py
│       │   ├── rt_outliers.py
│       │   ├── screening.py
│       │   └── utils.py
│       ├── reports/
│       │   ├── case_narrative/
│       │   ├── __init__.py
│       │   ├── aqs.py
│       │   ├── orsat.py
│       │   ├── populate_MDVR.py
│       │   ├── qc_table.py
│       │   ├── qualifiers.py
│       │   └── reprocess_plan.py
│       ├── workspace/
│       │   ├── case_narrative/
│       │   │   ├── __init__.py
│       │   │   ├── casenarrative.py
│       │   │   ├── flags.py
│       │   │   ├── plots.py
│       │   │   └── test.qmd
│       │   ├── __init__.py
│       │   ├── checklist.py
│       │   ├── files.py
│       │   ├── folders.py
│       │   ├── notebook.py
│       │   ├── parsing.py
│       │   └── result.py
│       ├── __init__.py
│       ├── conversions.py
│       └── dataset.py
├── templates/
│   ├── case_narrative/
│   │   └── logo.png
│   └── mdvr/
│       ├── .gitkeep
│       └── MDVR_template.xlsx
├── tests/
│   ├── test_pipeline/
│   │   └── test_utils/
│   ├── __init__.py
│   ├── conftest.py
│   ├── outline
│   ├── test_blanks.py
│   ├── test_conversions.py
│   ├── test_database.py
│   ├── test_dataset.py
│   ├── test_enums.py
│   ├── test_folders.py
│   ├── test_mdvr.py
│   ├── test_models.py
│   ├── test_qc_utils.py
│   ├── test_recovery.py
│   ├── test_reprocess_plan.py
│   ├── test_samples.py
│   └── test_screening.py
├── validation/
│   ├── ED/  *(not expanded — 22 subfolders, 5870 files)*
│   ├── EQ/  *(not expanded — 396 subfolders, 70640 files)*
│   ├── HW/  *(not expanded — 76 subfolders, 13517 files)*
│   ├── LP/  *(not expanded — 289 subfolders, 40044 files)*
│   ├── RB/  *(not expanded — 137 subfolders, 18692 files)*
│   └── .gitkeep
├── .gitignore
├── CLAUDE.md
├── environment.yml
├── pyproject.toml
└── README.md
```
