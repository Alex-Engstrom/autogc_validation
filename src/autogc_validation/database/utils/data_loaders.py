# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 14:49:57 2026

@author: aengstrom
"""

from typing import List
from ..models.voc import VOCInfo
from ..models.enums import VOCCategory, ColumnType, Priority
from ..config import VOC_DATA


def load_voc_info_from_dict(data: List[dict]) -> List[VOCInfo]:
    """
    Convert dictionary data to VOCInfo dataclass instances.
    
    Args:
        data: List of dictionaries with VOC information
        
    Returns:
        List of VOCInfo instances
        
    Raises:
        ValueError: If data validation fails
    """
    voc_list = []
    
    for item in data:
        try:
            voc = VOCInfo(
                aqs_code=item["aqs_code"],
                compound=item["compound"],
                category=VOCCategory(item["category"]),  # Convert to enum
                carbon_count=item["carbon_count"],
                molecular_weight=item["molecular_weight"],
                column=ColumnType(item["column"]),  # Convert to enum
                elution_order=item["elution_order"],
                priority=Priority(item["priority"])  # Convert to enum
            )
            
            # Validate the data
            voc.validate()
            
            voc_list.append(voc)
            
        except (KeyError, ValueError) as e:
            raise ValueError(f"Error loading VOC data for {item.get('compound', 'unknown')}: {e}")
    
    return voc_list


def load_standard_voc_data() -> List[VOCInfo]:
    """
    Load the standard VOC reference data.
    
    Returns:
        List of validated VOCInfo instances
    """
    raw_data = VOC_DATA
    return load_voc_info_from_dict(raw_data)