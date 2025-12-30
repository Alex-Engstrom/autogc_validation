# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 15:24:01 2025

@author: aengstrom
"""

import os
import zipfile
import shutil
from pathlib import Path
from VOC_validation_pipeline.pipeline.utils import assert_local_drive 
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def unzip_files(source_directory: os.PathLike, 
                destination_directory: os.PathLike, 
                delete_zip_after_extract: bool =False, 
                create_subfolders: bool=True, 
                allow_network_drive: bool = False)->list[Path]:
    """
    Unzips all zip files in a source directory to a destination directory,
    preserving the original modification dates.
    
    Parameters:
    source_directory (str): Path to the directory containing zip files
    destination_directory (str): Path where extracted files should be saved
    delete_zip_after_extract (bool): Whether to delete the zip file after extraction
    create_subfolders (bool): Whether to create subfolders for each zip file
    
    Returns:
    list: List of successfully extracted zip files
    """
    
    # Convert to Path objects for easier handling
    source_directory_path = Path(source_directory)
    destination_directory_path = Path(destination_directory)
    
    #Check if paths are on a network location
    for path in [source_directory_path, destination_directory_path]:
        assert_local_drive(path, allow_network_drive)
                
    
    # Check if source directory exists
    # --- Validate source directory ---
    if not source_directory_path.exists():
        logger.error(f"Source directory does not exist: {source_directory}")
        raise FileNotFoundError(f"Source directory does not exist: {source_directory}")

    if not source_directory_path.is_dir():
        logger.error(f"Source path is not a directory: {source_directory}")
        raise NotADirectoryError(f"Source path is not a directory: {source_directory}")

    # --- Validate destination directory ---
    if not os.access(destination_directory_path, os.W_OK):
        logger.error(f"Destination directory not writable: {destination_directory_path}")
        raise PermissionError(f"Destination directory not writable: {destination_directory_path}")

    # Create destination directory if it doesn't exist
    destination_directory_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Destination directory: {destination_directory_path}")
    
    # Find all zip files in source directory
    zip_files = list(source_directory_path.glob("*.zip"))    
    if not zip_files:
        logger.info(f"No zip files found in {source_directory_path}")
        return []
    logger.info(f"Found {len(zip_files)} zip file(s) in source directory")
    
    successfully_extracted: list[Path] = []
    
    for zip_file in zip_files:
        try:
            print(f"\nProcessing: {zip_file.name}")
            
            # Determine extraction path
            if create_subfolders:
                extract_folder_name = zip_file.stem
                extract_path = destination_directory_path / extract_folder_name
            else:
                extract_path = destination_directory_path
            
            # Create extraction directory if it doesn't exist
            extract_path.mkdir(parents=True, exist_ok = True)
            print(f"Extracting to: {extract_path}")
            
            # Extract the zip file with date preservation
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                logger.info(f"Found {len(file_list)} file(s) in zip")
                
                # Extract each file individually to preserve modification dates
                for file_info in zip_ref.infolist():
                    # Extract the file
                    zip_ref.extract(file_info, extract_path)
                    
                    # Get the full path to the extracted file
                    extracted_file_path = extract_path / file_info.filename
                    
                    # Preserve the original modification date
                    if not file_info.is_dir():
                        date_time = file_info.date_time
                        timestamp = datetime(*date_time).timestamp()
                        os.utime(extracted_file_path, (timestamp, timestamp))
                        
                
                logger.info(f"✓ Successfully extracted {len(file_list)} file(s)")
            
            successfully_extracted.append(zip_file)
            
            # Delete zip file if requested
            if delete_zip_after_extract:
                zip_file.unlink()
                logger.info(f"✓ Deleted original zip file: {zip_file.name}")
                
        except zipfile.BadZipFile:
            logger.exception(f"✗ Error: {zip_file.name} is not a valid zip file")
        except PermissionError:
            logger.exception(f"✗ Error: Permission denied when processing {zip_file.name}")
        except Exception as e:
            logger.exception(f"✗ Error processing {zip_file.name}: {e}")
    
    logger.info(f"""\n=== Summary ===
                Total zip files processed: {len(zip_files)}
                Successfully extracted: {len(successfully_extracted)}
                """)
    
    return successfully_extracted