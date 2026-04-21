# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 12:01:13 2026

@author: aengstrom
"""
import logging
from pathlib import Path
from autogc_validation.workspace.result import WorkspaceResult

logger = logging.getLogger(__name__)
def _generate_checklist(
    result: WorkspaceResult,
    site: str,
    year: int,
    month: int,
) -> Path:
    """Generate a monthly validation checklist inside the workspace.

    Creates a Markdown file with checkbox sections for each week and
    for month-level tasks.

    Args:
        result: WorkspaceResult from create_workspace (must have base_dir set).
        site: Site name code (e.g. "RB").
        year: Year.
        month: Month number (1-12).

    Returns:
        Path to the created checklist file.
    """
    yyyymm = f"{year}{month:02d}"

    content = f"""# {site} {yyyymm} Validation Checklist

## Setup
- [] Review MAX and OP log and add new QC canisters to the database
- [] Verify missing dat file count matches data in MAX
- [] Check filename/date mismatches, especially at week boundaries
- [] Download crosstab pre-changes
- [] Add month to MDVR cell
- [] Copy operator log entries
## Validation
- [] Check canister dates and concentrations in MAX, op log, and sqlite db
- [] Check calibration forms


### Week 1


### Week 2


### Week 3


### Week 4
## Review
## Final Steps
- [] Upload to Xchange network
- [] Verify upload in AQS 
- [] Download to pdf AQS emails
- [] Check all boxes in MDVR and convert to PDF
- [] Convert case narrative to PDF
- [] Zip up month folder

"""

    checklist_path = result.base_dir / f"{site}{yyyymm}_checklist.md"
    checklist_path.write_text(content)
    logger.info("Checklist created: %s", checklist_path)
    return checklist_path



