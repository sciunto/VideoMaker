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
import logging


def make_slide(intro_dir, resolution=(1200, 800)):
    """
    Make introduction png files

    :param intro_dir:
    :param resolution: picture resolution of the slides
    :returns: png file path
    """
    resol = str(resolution[0]) + 'x' + str(resolution[1])

    #TODO: we should delete this
    tmp_path = tempfile.mkdtemp()
    logger.debug('tmp_path for slide %s', tmp_path)

    tex_glob = glob.glob(os.path.abspath(intro_dir) + '/*tex')
    if tex_glob == []:
        return None
    if len(tex_glob) > 1:
        print('Error, non uniq tex file in %s' % intro_dir)
        return None

    filename = os.path.splitext(os.path.basename(tex_glob[0]))[0]
    texfile = os.path.join(intro_dir, filename + '.tex')
    dvifile = os.path.join(tmp_path, filename + '.dvi')
    pdffile = os.path.join(tmp_path, filename + '.pdf')
    pngfile = os.path.join(tmp_path, filename + '.png')

    #command = ['/usr/bin/latex', '-output-directory=' + str(tmp_path), str(texfile)]
    command = ['/usr/bin/pdflatex', '-output-directory=' + str(tmp_path), str(texfile)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    command = ['/usr/bin/convert', '-density', '600', str(pdffile), '-resize', resol,  str(pngfile)]
    #command = ['/usr/bin/dvipng', '-o', str(pngfile), str(dvifile)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return pngfile


def name_it(tmp_path):
    """
    Iterator returning a picture name located in tmp_path

    :param tmp_path:
    :returns: iterator
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
    return [tryint(c) for c in re.split('([0-9]+)', s)]

##############Natural sorting


class VideoSection():
    """
    Gather data about a video section


    :repeat: repeat the movie N times
    """
    def __init__(self, path, num_frame_slide, every=1, repeat=1):
        self.path = path
        self.num_frame_slide = num_frame_slide
        self.every = every
        self.repeat = repeat


def prepare_pictures(tmp_path, opening, bodies, ending):
    """
    Put pictures in tmp_path with a correct name (sorted)

    :param tmp_path:
    :param opening:
    :param bodies:
    :param ending:
    """
    logger.info('Prepare pictures...')
    resolution = (1200, 800)
    resolution = (800, 600)
    gen = name_it(tmp_path)

    #Part 1, opening
    if opening.path:
        logger.info('[Opening]')
        introfile = make_slide(opening.path, resolution)

        if introfile:
            for count in range(opening.num_frame_slide):
                shutil.copy(introfile, gen.__next__())

    #Part 2, body
    logger.info('[Body]')
    for body in bodies:
        slide = make_slide(body.path, resolution)
        if slide:
            for count in range(body.num_frame_slide):
                shutil.copy(slide, gen.__next__())

        #TODO: for each picture:
        # * resize in order that the resolution is in the resolution defined above
        # * Extend the picture (background color) to have exactly the same resolution
        pictures = sorted(os.listdir(body.path), key=alphanum_key)
        pictures = [os.path.join(body.path, item) for item in pictures]

        logger.debug('List of pictures: %s' % pictures)
        for rep in range(repeat):
            for item in pictures[::body.every]:
                shutil.copy(item, gen.__next__())

    #Part 3, ending
    if ending.path:
        logger.info('[Ending]')
        endfile = make_slide(ending.path, resolution)
        if endfile:
            for count in range(ending.num_frame_slide):
                shutil.copy(endfile, gen.__next__())


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='', epilog='')
    parser.add_argument('conf', help='Configuration file', metavar='CONF')
    parser.add_argument('-d', '--debug', action='store_true',
                        default=False, help='Run in debug mode')

    args = parser.parse_args()

    if args.debug:
        llevel = logging.DEBUG
    else:
        llevel = logging.INFO
    logger = logging.getLogger()
    logger.setLevel(llevel)

    steam_handler = logging.StreamHandler()
    steam_handler.setLevel(llevel)
    logger.addHandler(steam_handler)

    config = configparser.ConfigParser()
    config.read(args.conf)

    cwd = os.getcwd()

    #Movie section
    fps = config['movie'].getint('fps')
    output = config['movie'].get('output', 'output')

    #Opening
    open_duration = config['opening'].getint('duration', 0)  # seconds
    opening_section = VideoSection(config['opening'].get('path', None), fps * open_duration)

    #Body
    pic_paths = config['body'].get('path').split(',')
    every = config['body'].getint('every', 1)
    repeat = config['body'].getint('repeat', 1)
    body_sections = [VideoSection(path, config['body'].getint('duration', 0), every, repeat) for path in pic_paths]

    #Ending
    end_duration = config['ending'].getint('duration', 0)  # seconds
    end_section = VideoSection(config['ending'].get('path', None), fps * end_duration)

    #Prepare pictures in tmp dir
    tmp_path = tempfile.mkdtemp()
    logger.debug('tmp_path for pictures %s', tmp_path)

    prepare_pictures(tmp_path, opening_section, body_sections, end_section)

    #Encode the movie
    logger.info('Generate the movie...')
    os.chdir(tmp_path)
    command = ['mencoder', 'mf://*.png', '-mf', 'fps=25',
               '-vf', 'scale=800:600',
               '-o', 'output.avi',
               '-ovc', 'xvid',
               '-xvidencopts', 'bitrate=500']
    logging.debug('command: ' + str(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    logging.debug(stdout.decode('utf8'))
    logging.warning(stderr.decode('utf8'))

    #Copy the movie
    logging.debug('Move to %s' % cwd)
    shutil.copy('output.avi', os.path.join(cwd, output + '.avi'))
    #Delete the tmp dir
    logging.debug('Delete the tmp_dir %s' % tmp_path)
    shutil.rmtree(tmp_path)
