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


import configparser

def make_intro(intro_dir):
    """
    Make introduction png file

    :returns: png file path
    """
    tmp_path = tempfile.mkdtemp()

    filename = os.path.basename(glob.glob(os.path.abspath(intro_dir) + '/*tex')[0])
    filename = os.path.splitext(filename)[0]
    texfile = os.path.join(intro_dir, filename + '.tex')
    dvifile = os.path.join(tmp_path, filename + '.dvi')
    pngfile = os.path.join(tmp_path, filename + '.png')
    
    
    command = ['/usr/bin/latex', '-output-directory=' + str(tmp_path), str(texfile)]
    print(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    command = ['/usr/bin/dvipng', '-o', str(pngfile), str(dvifile)]
    print(command)
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


def prepare_pictures(tmp_path, num_frames_slide, pic_path, intro_dir):
    """
    Put pictures in tmp_path with a correct name (sorted)
    """
    print(tmp_path)
    gen = name_it(tmp_path)

    #Part 1, introduction
    introfile = make_intro(intro_dir)

    file_list = []
    for count in range(num_frames_slide):
        print('copy intro to')
        dest = gen.__next__() 
        shutil.copy(introfile, dest)
        file_list.append(dest)

    #Part 2, pictures
    pictures = sorted(os.listdir(pic_path), key=alphanum_key)
    pictures = [os.path.join(pic_path, item) for item in pictures]

    for item in pictures:
        dest = gen.__next__() 
        shutil.copy(item, dest)
        file_list.append(dest)

    return file_list

if __name__ == '__main__':
   
    config = configparser.ConfigParser()
    config.read('config.conf')


    cwd = os.getcwd()

    #pic_path = 'pictures/'
    intro_dir = config['intro'].get('path')
    fps = config['movie'].getint('fps')
    pic_path = config['movie'].get('path')
    intro_duration = config['intro'].getint('duration')  #seconds
    num_frames_slide = fps * intro_duration

    #Prepare pictures in tmp dir
    tmp_path = tempfile.mkdtemp()

    pictures = prepare_pictures(tmp_path, num_frames_slide, pic_path, intro_dir)
  
    #Encode the movie
    os.chdir(tmp_path)
    command = ['mencoder', 'mf://*', '-mf', 'fps='+str(fps), '-o', 'output.avi', 
        '-ovc', 'lavc', '-lavcopts', 'vcodec=msmpeg4v2:vbitrate=800']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    #Copy the movie
    shutil.copy('output.avi', cwd)
