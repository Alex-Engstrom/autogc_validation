# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 16:54:16 2025

@author: aengstrom
"""
# Code outline via chatgpt
def run_pipeline(spec: PipelineSpec, site: str, month: str):
    state = load_or_create_state(spec.name, site, month)
    for step in spec.steps:
        if not state.is_completed(step.__name__):
            step(site=site, month=month, state=state)
            state.mark_completed(step.__name__)
            save_state(state)
