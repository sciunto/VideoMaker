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


class VideoSection():
    """
    Gather data about a video section
    """
    def __init__(self, path, num_frame_slide):
        self.path = path
        self.num_frame_slide = num_frame_slide


def prepare_pictures(tmp_path, opening, bodies, ending):
    """
    Put pictures in tmp_path with a correct name (sorted)
    """
    gen = name_it(tmp_path)

    #Part 1, opening
    if opening.path:
        introfile = make_slide(opening.path)

        for count in range(opening.num_frame_slide):
            #dest = gen.__next__() 
            shutil.copy(introfile, gen.__next__())

    #Part 2, body
    for body in bodies:
        slide = make_slide(body.path)
        for count in range(body.num_frame_slide): 
            #dest = gen.__next__() 
            shutil.copy(slide, gen.__next__())

        pictures = sorted(os.listdir(body.path), key=alphanum_key)
        pictures = [os.path.join(body.path, item) for item in pictures]

        for item in pictures:
            #dest = gen.__next__() 
            shutil.copy(item, gen.__next__())

    #Part 3, ending
    if ending.path:
        endfile = make_slide(ending.path)

        for count in range(ending.num_frame_slide):
            #dest = gen.__next__() 
            shutil.copy(endfile, gen.__next__())


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
    open_duration = config['opening'].getint('duration', 0)  #seconds
    opening_section = VideoSection(config['opening'].get('path', None), fps * open_duration)

    #Body
    pic_paths = config['body'].get('path').split(',')
    body_sections = [VideoSection(path, 10) for path in pic_paths] #FIXME

    #Ending
    end_duration = config['ending'].getint('duration', 0)  #seconds
    end_section = VideoSection(config['ending'].get('path', None), fps * end_duration)

    #Prepare pictures in tmp dir
    tmp_path = tempfile.mkdtemp()

    prepare_pictures(tmp_path, opening_section, body_sections, end_section)
  
    #Encode the movie
    os.chdir(tmp_path)
    command = ['mencoder', 'mf://*', '-mf', 'fps='+str(fps), '-o', 'output.avi', 
        '-ovc', 'lavc', '-lavcopts', 'vcodec=msmpeg4v2:vbitrate=800']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    #Copy the movie
    shutil.copy('output.avi', os.path.join(cwd, output + '.avi'))


