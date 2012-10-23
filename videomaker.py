#!/usr/bin/python

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# Author: Francois Boulogne <fboulogne at sciunto dot org>, 2012

import tempfile
import glob
import os.path
import subprocess
import re
import shutil
import argparse


import configparser

def make_slide(intro_dir):
    """
    Make introduction png file

    :returns: png file path
    """
    tmp_path = tempfile.mkdtemp()

    filename = os.path.basename(glob.glob(os.path.abspath(intro_dir) + '/*tex')[0]) #TODO check length
    filename = os.path.splitext(filename)[0] 
    texfile = os.path.join(intro_dir, filename + '.tex')
    dvifile = os.path.join(tmp_path, filename + '.dvi')
    pngfile = os.path.join(tmp_path, filename + '.png')
    
    
    command = ['/usr/bin/latex', '-output-directory=' + str(tmp_path), str(texfile)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    command = ['/usr/bin/dvipng', '-o', str(pngfile), str(dvifile)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return pngfile

def name_it(tmp_path):
    """
    Iterator returning a picture name located in tmp_path
    """
    i = 0
    while True:
        pngfile = os.path.join(tmp_path, str(i).zfill(5) + '.png')
        yield(pngfile)
        i += 1



##############Natural sorting

def tryint(s):
    try:
        return int(s)
    except:
        return s
     
def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

##############Natural sorting


def prepare_pictures(tmp_path, pic_paths, num_frames_intro_slide, intro_dir, num_frames_end_slide, end_dir):
    """
    Put pictures in tmp_path with a correct name (sorted)
    """
    gen = name_it(tmp_path)

    #Part 1, introduction
    if intro_dir:
        introfile = make_slide(intro_dir)

        for count in range(num_frames_intro_slide):
            dest = gen.__next__() 
            shutil.copy(introfile, dest)

    #Part 2, pictures
    for pic_path in pic_paths:
        slide = make_slide(pic_path)
        for count in range(20): #FIXME
            dest = gen.__next__() 
            shutil.copy(slide, dest)


        pictures = sorted(os.listdir(pic_path), key=alphanum_key)
        pictures = [os.path.join(pic_path, item) for item in pictures]

        for item in pictures:
            dest = gen.__next__() 
            shutil.copy(item, dest)

    #Part 3, end
    if end_dir:
        endfile = make_slide(end_dir)

        for count in range(num_frames_end_slide):
            dest = gen.__next__() 
            shutil.copy(endfile, dest)


if __name__ == '__main__':
  
    parser = argparse.ArgumentParser(description='', epilog='')
    parser.add_argument('conf', help='Configuration file', metavar='CONF')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.conf)


    cwd = os.getcwd()

    #Movie section
    fps = config['movie'].getint('fps')
    output = config['movie'].get('output', 'output')

    #Opening
    open_dir = config['opening'].get('path', None)
    open_duration = config['opening'].getint('duration', 0)  #seconds
    num_frames_open_slide = fps * open_duration

    #Body
    pic_paths = config['body'].get('path').split(',')

    #Ending
    end_dir = config['ending'].get('path', None)
    end_duration = config['ending'].getint('duration', 0)  #seconds
    num_frames_end_slide = fps * end_duration

    #Prepare pictures in tmp dir
    tmp_path = tempfile.mkdtemp()

    pictures = prepare_pictures(tmp_path, pic_paths, num_frames_open_slide, open_dir, num_frames_end_slide, end_dir)
  
    #Encode the movie
    os.chdir(tmp_path)
    command = ['mencoder', 'mf://*', '-mf', 'fps='+str(fps), '-o', 'output.avi', 
        '-ovc', 'lavc', '-lavcopts', 'vcodec=msmpeg4v2:vbitrate=800']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    #Copy the movie
    shutil.copy('output.avi', os.path.join(cwd, output + '.avi'))
