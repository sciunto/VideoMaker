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
import math
from PIL import Image


def add_bg(im, bg, angle=0):
    """
    Put image `im` on a background `bg`.
    Pre-rotate the image with an `angle`.

    """
    # Rotate the image
    if angle != 0:
        im = im.rotate(angle)

    if im.size == bg.size:
        # Nothing to hide!
        return im.copy()

    # Copy to do not overwrite bg
    wbg = bg.copy()

    if im.size[1] > im.size[0]:
        # Match size along the vert. dir.
        ratio = wbg.size[1]/im.size[1]
        newsize = (math.floor(im.size[0]*ratio), wbg.size[1])
        box = (math.floor(math.fabs(wbg.size[0]-im.size[0])/2), 0)
    else:
        ratio = wbg.size[0]/im.size[0]
        newsize = (wbg.size[0], math.floor(im.size[1]*ratio))
        box = (0, math.floor(math.fabs(wbg.size[1]-im.size[1])/2))

    im = im.resize(newsize)

    wbg.paste(im, box=box)
    return wbg


def make_slide(intro_dir, tmp_path, resolution=(1200, 800)):
    """
    Make introduction png files

    :param intro_dir: path to the dir containing a tex file
    :param resolution: picture resolution of the slides
    :returns: png file path
    """
    logger.debug('Build a tex file')
    resol = str(resolution[0]) + 'x' + str(resolution[1])


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

##############Natural sorting : end


class VideoSection():
    """
    Gather data about a video section


    :repeat: repeat the movie N times
    """
    def __init__(self, path, num_frame_slide, number=1, repeat=1):
        self.path = path
        self.num_frame_slide = num_frame_slide
        self.number = number
        self.repeat = repeat


def prepare_pictures(output_dir, opening, bodies, ending, tmp_loc=None):
    """
    Put pictures in tmp_path with a correct name (sorted)

    :param output_dir: path where final images are written before making the video
    :param opening: :class:`VideoSection` instance for opening
    :param bodies: :class:`VideoSection` instance for bodies
    :param ending: :class:`VideoSection` instance for ending
    :param tmp_loc: path where tmp dirs are created
    """
    logger.info('Prepare pictures...')
    #TODO: setup this somewhere
    resolution = (800, 600)
    gen = name_it(output_dir)
    # Background: auto-generated for the moment
    bg = Image.new("RGB", resolution, color=(0, 0, 0)) # Black.
    # Angle to rotate each image (for futher improvements)
    angle = 0

    #Part 1, opening
    if opening.path:
        logger.info('[Opening]')
        tmp_path = tempfile.mkdtemp(dir=tmp_loc)
        introfile = make_slide(opening.path, tmp_path, resolution)
        if introfile:
            for count in range(opening.num_frame_slide):
                shutil.copy(introfile, gen.__next__())
        shutil.rmtree(tmp_path)

    #Part 2, body
    logger.info('[Body]')
    for body in bodies:
        tmp_path = tempfile.mkdtemp(dir=tmp_loc)
        slide = make_slide(body.path, tmp_path, resolution)
        if slide:
            for count in range(body.num_frame_slide):
                shutil.copy(slide, gen.__next__())
        shutil.rmtree(tmp_path)

        pictures = sorted(os.listdir(body.path), key=alphanum_key)
        pictures = [os.path.join(body.path, item) for item in pictures]

        if body.number >= 1:
            # duplicate the picture...
            times = math.floor(body.number)
            for rep in range(repeat):
                for item in pictures:
                    logger.debug('Process: %s' % item)
                    # stick the item on a background
                    full_im = Image.open(item)
                    full_im = add_bg(full_im, bg, angle=angle)
                    full_im.save('/tmp/toto.png') #FIXME change this
                    for time in range(times):
                        shutil.copy('/tmp/toto.png', gen.__next__())
        elif body.number < 1:
            # pick one every...
            every = math.floor(1/body.number)
            for rep in range(repeat):
                for item in pictures[::every]:
                    logger.debug('Process: %s' % item)
                    # stick the item on a background
                    full_im = Image.open(item)
                    full_im = add_bg(full_im, bg, angle=angle)
                    full_im.save('/tmp/toto.png') #FIXME change this
                    shutil.copy('/tmp/toto.png', gen.__next__())

    #Part 3, ending
    if ending.path:
        logger.info('[Ending]')
        tmp_path = tempfile.mkdtemp(dir=tmp_loc)
        endfile = make_slide(ending.path, tmp_path, resolution)
        if endfile:
            for count in range(ending.num_frame_slide):
                shutil.copy(endfile, gen.__next__())
        shutil.rmtree(tmp_path)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='', epilog='')
    parser.add_argument('conf', help='Configuration file', metavar='CONF')
    parser.add_argument('-t', '--tmp', metavar='TMP',
                        default=None, help='Directery where are stored tmp files')
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
    output = config['movie'].get('output', 'output')

    #Opening
    open_duration = config['opening'].getint('duration', 0)  # seconds
    opening_section = VideoSection(config['opening'].get('path', None), 25 * open_duration)

    #Body
    pic_paths = config['body'].get('path').split(',')
    inifps = config['body'].getint('inifps', 1)
    speed = config['body'].getint('speed', 1)
    repeat = config['body'].getint('repeat', 1)

    number = 25 / inifps / speed
    body_sections = [VideoSection(path, config['body'].getint('duration', 0), number, repeat) for path in pic_paths]

    #Ending
    end_duration = config['ending'].getint('duration', 0)  # seconds
    end_section = VideoSection(config['ending'].get('path', None), 25 * end_duration)

    #Prepare pictures in tmp dir
    tmp_path = tempfile.mkdtemp(dir=args.tmp)
    logger.debug('tmp_path for pictures %s', tmp_path)

    prepare_pictures(tmp_path, opening_section, body_sections, end_section, tmp_loc=args.tmp)

    #Encode the movie
    logger.info('Generate the movie...')
    os.chdir(tmp_path)
    command = ['mencoder', 'mf://*.png', '-mf', 'fps=25',
               '-vf', 'scale=800:600',
               '-o', 'output.avi',
               '-ovc', 'xvid',
               '-xvidencopts', 'bitrate=500'
               ]
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
