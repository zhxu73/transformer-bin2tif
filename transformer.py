"""Converts binary image files to georeferenced TIFFs
"""

import argparse
import os
import logging

from terrautils.spatial import geojson_to_tuples as tr_geojson_to_tuples
from terrautils.formats import create_geotiff as tr_create_geotiff
import terraref.stereo_rgb

import configuration
import transformer_class

def add_parameters(parser: argparse.ArgumentParser) -> None:
    """Adds parameters
    Arguments:
        parser: instance of argparse
    """
    parser.add_argument('--save_intermediate', action='store_true',
                        help='saves the intermediate image file before it\'s saved as a geotiff')

# pylint: disable=unused-argument
def check_continue(transformer: transformer_class.Transformer, check_md: dict, transformer_md: dict, full_md: dict) -> tuple:
    """Checks if conditions are right for continuing processing
    Arguments:
        transformer: instance of transformer class
    Return:
        Returns a tuple containining the return code for continuing or not, and
        an error message if there's an error
    """
    have_file = False
    for one_file in check_md['list_files']():
        if one_file.endswith('.bin'):
            have_file = True
            break

    return (0) if have_file else (-1, "Missing raw image bin file from list of files")

def perform_process(transformer: transformer_class.Transformer, check_md: dict, transformer_md: dict, full_md: dict) -> dict:
    """Performs the processing of the data
    Arguments:
        transformer: instance of transformer class
    Return:
        Returns a dictionary with the results of processing
    """
    # Find the source file to process
    source_file = None
    for one_file in check_md['list_files']():
        if one_file.endswith('.bin'):
            source_file = one_file
            break

    # Initialize local variables
    logging.debug("Working with source file: %s", source_file)
    out_filename = os.path.splitext(os.path.basename(source_file))[0] + '.tif'
    out_file = os.path.join(check_md['working_folder'], out_filename)
    
    bin_type = 'left' if source_file.endswith('_left.bin') else 'right' if source_file.endswith('_right.bin') else None
    if not bin_type:
        msg = "Bin file must be a left or right file: '%s'" % source_file
        logging.error(msg)
        logging.error("    Returning an error")
        return {'code': -1000, 'error': msg}
    logging.debug("Source image is type: %s", bin_type)

    # Process the file
    try:
        bin_shape = terraref.stereo_rgb.get_image_shape(check_md['context_md'], bin_type)
        gps_bounds_bin = tr_geojson_to_tuples(check_md['context_md']['spatial_metadata'][bin_type]['bounding_box'])
    except KeyError:
        msg = "Spatial metadata is not properly identified. Unable to continue"
        logging.error(msg)
        return {'code': -1001, 'error': msg}
    logging.debug("Image bounds are: %s", str(gps_bounds_bin))

    # Perform actual processing
    if transformer.args.save_intermediate:
        intermediate_filename = os.path.join(check_md['working_folder'], "intermediate.tif")
        logging.info("Generating intermediate image file: %s", intermediate_filename)
    else:
        intermediate_filename = None
    new_image = terraref.stereo_rgb.process_raw(bin_shape, source_file, intermediate_filename)
    tr_create_geotiff(new_image, gps_bounds_bin, out_file, None, False,
                      transformer.generate_transformer_md(), check_md['context_md'], compress=True)

    return {
        'code': 0,
        'file': [{
            'path': out_file,
            'key': configuration.TRANSFORMER_TYPE
        }]
    }
