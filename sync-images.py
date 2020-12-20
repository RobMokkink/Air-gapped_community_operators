#!/usr/bin/python3
'''
Script to sync operators
'''
#------------------
# Imports
#------------------
import argparse
import os
import glob
import fnmatch
import re
import json
import shlex
import subprocess
import fileinput

#------------------
# Global vars
#------------------
CSV_FILE = "*clusterserviceversion*"

#------------------
# Functions
#------------------

def get_ops_csv_files(ops_dir):
    '''
    Get all csv files and get
    all the images
    '''

    file_list = []

    for dir, _, files in os.walk(ops_dir):
        for file in files:
            # Get the clusterservice files
            if glob.fnmatch.fnmatch(file, CSV_FILE):
                # Get the full filepath
                file_path = os.path.join(dir, file)

                file_list.append(file_path)
    # Return a list with all the files
    return file_list

def get_images_locations(filelist,registry,dump):
    '''
    Get all the image locations in the files
    '''

    # Create empty dict
    img_dict = {}

    # Loop through the files
    for csv_file in filelist:

        # open and read the file
        with open(csv_file, 'rt') as fh:
            get_text = fh.read()

            # Get all the image locations
            # I assume docker.io and quay.io
            get_img_loc = re.findall("docker.io/.*|quay.io/.*", get_text)

            # Loop through the found image locations and add them
            for img_loc in get_img_loc:

                # Check for vaulty image locations
                # Have seen these a couple of times
                if "@@" in img_loc:
                    print("%s is vaulty" % (img_loc))

                    # Adjust the variable
                    adj_loc = img_loc.replace("@@", "@")
                    print("Adjusted to %s" %(adj_loc))

                    # Adjust the file
                    with fileinput.FileInput(csv_file, inplace=True) as fh:
                        for line in fh:
                            print(line.replace(img_loc, adj_loc), end='')

                    # Assign the variable the proper value
                    img_loc = adj_loc

                # Old location
                old_loc = img_loc.rstrip("\n")

                # New location
                raw_new_loc = old_loc.split('/')
                if len(raw_new_loc) == 3:
                    new_loc = "%s/%s-%s" % (registry, raw_new_loc[1], raw_new_loc[2])
                if len(raw_new_loc) == 2:
                    new_loc = "%s/%s" % (registry, raw_new_loc[1])

                # Add entry's to the dictionary
                img_dict[old_loc] = new_loc

    # Dump to file
    if dump:
        with open('mapping.json', 'w') as jf:
            jf.write(json.dumps(img_dict))
    
    # return the dictionary
    return img_dict

def copy_images(mapping_dict, authjson):
    '''
    Use skopeo to do the copy
    '''

    # Create /dev/null
    FNULL = open(os.devnull, 'w')

    # Loop through the list
    for src_img, dest_img in mapping_dict.items():
        # Info
        print("Copy %s to %s" % (src_img, dest_img))

        # Create command
        cmd = "skopeo copy -a --dest-tls-verify=false --authfile=%s docker://%s docker://%s" % (authjson, src_img, dest_img)
   
        # Perform the copy
        try:
            subprocess.check_call(shlex.split(cmd),stdout=FNULL)
        except subprocess.CalledProcessError:
            print("Error with copy %s" % (src_img))

def adj_files(file_list, mapping_dict):
    '''
    Adjust the files
    '''
 
    # Loop through the list of files
    for csv_file in file_list:
        for old_loc, new_loc in mapping_dict.items():
            # Adjust the file
            with fileinput.FileInput(csv_file, inplace=True) as fh:
                for line in fh:
                    print(line.replace(old_loc, new_loc), end='')

def run():
    '''
    Main function
    '''

    parser = argparse.ArgumentParser(description='Community Operator Syncer')
    parser.add_argument('--dir', required=True, help='directory containing the operators information')
    parser.add_argument('--registry', required=True, help='registry location')
    parser.add_argument('--authfile', required=True, help='registry authentication file')
    parser.add_argument('--dumpjson', action='store_true', help='option to dump json mapping file')
    args = parser.parse_args()

    # Get all the operator clusterserviceversion files
    get_files = get_ops_csv_files(args.dir)

    # Get all the images inside the files and dump them to json
    get_images = get_images_locations(get_files, args.registry, args.dumpjson)

    # Do skopeo action
    copy_images(get_images, args.authfile)

    # Adjust files
    adj_files(get_files, get_images)

if __name__ == '__main__':
    run()
