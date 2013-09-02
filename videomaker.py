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

    if im.size[1] / im.size[0] > wbg.size[1] / wbg.size[0]:
        logger.debug('Case 1')
        # Match size along the vert. dir.
        ratio = wbg.size[1]/im.size[1]
        newsize = (math.floor(im.size[0]*ratio), wbg.size[1])
        box = (math.floor(math.fabs(wbg.size[0]-newsize[0])/2), 0)
    else:
        logger.debug('Case 2')
        ratio = wbg.size[0]/im.size[0]
        newsize = (wbg.size[0], math.floor(im.size[1]*ratio))
        box = (0, math.floor(math.fabs(wbg.size[1]-im.size[1])/2))
        box = (0, math.floor(math.fabs(wbg.size[1]-newsize[1])/2))

    logger.debug('im Size: %s' % str(im.size))
    logger.debug('bg Size: %s' % str(wbg.size))
    logger.debug('New Size: %s' % str(newsize))
    logger.debug('Box: %s' % str(box))
    im = im.resize(newsize)

    wbg.paste(im, box=box)
    return wbg


def name_it(tmp_path, digits=6):
    """
    Iterator returning a picture name located in tmp_path

    :param tmp_path:
    :param digits: number of digits used in the name
    :returns: iterator
    """
    i = 0
    while True:
        pngfile = os.path.join(tmp_path, str(i).zfill(digits) + '.png')
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


#class VideoSection():
#    """
#    Gather data about a video section
#
#
#    :repeat: repeat the movie N times
#    """
#    def __init__(self, path, num_frame_slide, number=1, repeat=1):
#        self.path = path
#        self.num_frame_slide = num_frame_slide
#        self.number = number
#        self.repeat = repeat


def make_slide(tex_path, tmp_path, resolution=(1200, 800)):
    """
    Make introduction png files

    :param tex_path: path to the tex file
    :param tmp_path: path to a tmp dir
    :param resolution: picture resolution of the slides
    :returns: png file path
    """
    logger.debug('Build a tex file')
    resol = str(resolution[0]) + 'x' + str(resolution[1])

    filename = os.path.splitext(os.path.basename(tex_path))[0]
    #dvifile = os.path.join(tmp_path, filename + '.dvi')
    pdffile = os.path.join(tmp_path, filename + '.pdf')
    pngfile = os.path.join(tmp_path, filename + '.png')

    #command = ['/usr/bin/latex', '-output-directory=' + str(tmp_path), str(texfile)]
    command = ['/usr/bin/pdflatex', '-output-directory=' + str(tmp_path), str(tex_path)]
    logger.debug('Command: %s' % command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    command = ['/usr/bin/convert', '-density', '600', str(pdffile), '-resize', resol,  str(pngfile)]
    logger.debug('Command: %s' % command)
    #command = ['/usr/bin/dvipng', '-o', str(pngfile), str(dvifile)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return pngfile


#def prepare_pictures(output_dir, opening, bodies, ending, resolution=(800, 600), tmp_loc=None):
#    """
#    Put pictures in tmp_path with a correct name (sorted)
#
#    :param output_dir: path where final images are written before making the video
#    :param opening: :class:`VideoSection` instance for opening
#    :param bodies: :class:`VideoSection` instance for bodies
#    :param ending: :class:`VideoSection` instance for ending
#    :param resolution: Tuple speciafying the resolution
#    :param tmp_loc: path where tmp dirs are created
#    """
#    logger.info('Prepare pictures...')
#    # Start a generator
#    gen = name_it(output_dir)
#    # Background: auto-generated for the moment
#    bg = Image.new("RGB", resolution, color=(0, 0, 0)) # Black.
#    # Angle to rotate each image (for futher improvements)
#    angle = 0
#
#    #Part 1, opening
#    if opening.path:
#        logger.info('[Opening]')
#        tmp_path = tempfile.mkdtemp(dir=tmp_loc, prefix='tmp_open')
#        introfile = make_slide(opening.path, tmp_path, resolution)
#        if introfile:
#            for count in range(opening.num_frame_slide):
#                shutil.copy(introfile, gen.__next__())
#        shutil.rmtree(tmp_path)
#
#    #Part 2, body
#    logger.info('[Body]')
#    for body in bodies:
#        tmp_path = tempfile.mkdtemp(dir=tmp_loc, prefix='tmp_body')
#        slide = make_slide(body.path, tmp_path, resolution)
#        if slide:
#            for count in range(body.num_frame_slide):
#                shutil.copy(slide, gen.__next__())
#        shutil.rmtree(tmp_path)
#
#        pictures = sorted(os.listdir(body.path), key=alphanum_key)
#        pictures = [os.path.join(body.path, item) for item in pictures]
#
#        tmp_file = tempfile.mkstemp(dir=tmp_loc, prefix='pic')
#        if body.number >= 1:
#            # duplicate the picture...
#            times = math.floor(body.number)
#            for rep in range(repeat):
#                for item in pictures:
#                    logger.debug('Process: %s' % item)
#                    # stick the item on a background
#                    full_im = Image.open(item)
#                    full_im = add_bg(full_im, bg, angle=angle)
#                    full_im.save(tmp_file)
#                    for time in range(times):
#                        shutil.copy(tmp_file, gen.__next__())
#        elif body.number < 1:
#            # pick one every...
#            every = math.floor(1/body.number)
#            for rep in range(repeat):
#                for item in pictures[::every]:
#                    logger.debug('Process: %s' % item)
#                    # stick the item on a background
#                    full_im = Image.open(item)
#                    full_im = add_bg(full_im, bg, angle=angle)
#                    full_im.save(tmp_file)
#                    shutil.copy(tmp_file, gen.__next__())
#        shutil.rmtree(tmp_path)
#
#    #Part 3, ending
#    if ending.path:
#        logger.info('[Ending]')
#        tmp_path = tempfile.mkdtemp(dir=tmp_loc, prefix='tmp_end')
#        endfile = make_slide(ending.path, tmp_path, resolution)
#        if endfile:
#            for count in range(ending.num_frame_slide):
#                shutil.copy(endfile, gen.__next__())
#        shutil.rmtree(tmp_path)






class Video():
    """
    Class to prepare and build a video

    :param resolution:
    :param tmp_dir: Temp directory path
    """
    def __init__(self, resolution, tmp_dir=None):
        self.tmp_dir = tmp_dir
        self.resolution = resolution
        self.pic_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        self.generator = name_it(self.pic_dir)

    def populate_with_slides(self, path, number):
        """
        Add slides to the tmp dir
        :param path: path to the tex file
        :param number: number of images #FIXME: time?
        """
        logger.debug('Populate with slide: %s' %path)
        tmp_path = tempfile.mkdtemp(dir=self.tmp_dir, prefix='tmpSlide')
        endfile = make_slide(path, tmp_path, self.resolution)
        if endfile:
            for count in range(number):
                shutil.copy(endfile, self.generator.__next__())
        shutil.rmtree(tmp_path)

    def populate_with_pictures(self, path, number, repeat):
        """
        Add pictures to the tmp dir
        :param path: path to pictures
        """
        # Background: auto-generated for the moment
        bg = Image.new("RGB", resolution, color=(0, 0, 0)) # Black.
        # Angle to rotate each image (for futher improvements)
        angle = 0
        pictures = sorted(os.listdir(path), key=alphanum_key)
        pictures = [os.path.join(path, item) for item in pictures]

        tmp_file = tempfile.mkstemp(dir=self.tmp_dir, prefix='tmpImage', suffix='.png')[1]
        if number >= 1:
            # duplicate the picture...
            times = math.floor(number)
            for rep in range(repeat):
                for item in pictures:
                    logger.debug('Process: %s' % item)
                    # stick the item on a background
                    full_im = Image.open(item)
                    full_im = add_bg(full_im, bg, angle=angle)
                    print(tmp_file)
                    full_im.save(tmp_file)
                    for time in range(times):
                        shutil.copy(tmp_file, self.generator.__next__())
        elif number < 1:
            # pick one every...
            every = math.floor(1 / number)
            for rep in range(repeat):
                for item in pictures[::every]:
                    logger.debug('Process: %s' % item)
                    # stick the item on a background
                    full_im = Image.open(item)
                    full_im = add_bg(full_im, bg, angle=angle)
                    full_im.save(tmp_file)
                    shutil.copy(tmp_file, self.generator.__next__())
        os.remove(tmp_file)

    def make(self, cwd, output, fps=25):
        """
        Build the video

        :param fps: frame per second
        """

        #Encode the movie
        logger.info('Generate the movie...')
        os.chdir(self.pic_dir)
        command = ['mencoder', 'mf://*.png', '-mf', 'fps='+str(fps),
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
        #TODO: put this somewhere
        #Delete the self.pic_dir
        #logging.debug('Delete the tmp_dir %s' % tmp_path)
        #shutil.rmtree(tmp_path)


#def old():
#    parser = argparse.ArgumentParser(description='', epilog='')
#    parser.add_argument('conf', help='Configuration file', metavar='CONF')
#    parser.add_argument('-t', '--tmp', metavar='TMP',
#                        default=None, help='Directery where are stored tmp files')
#    parser.add_argument('-d', '--debug', action='store_true',
#                        default=False, help='Run in debug mode')
#
#    args = parser.parse_args()
#
#    if args.debug:
#        llevel = logging.DEBUG
#    else:
#        llevel = logging.INFO
#    logger = logging.getLogger()
#    logger.setLevel(llevel)
#
#    steam_handler = logging.StreamHandler()
#    steam_handler.setLevel(llevel)
#    logger.addHandler(steam_handler)
#
#    config = configparser.ConfigParser()
#    config.read(args.conf)
#
#    cwd = os.getcwd()
#    FPS = 25
#    resolution = (800, 600)
#
#    #Movie section
#    output = config['movie'].get('output', 'output')
#
#    #Opening
#    open_duration = config['opening'].getint('duration', 0)  # seconds
#    opening_section = VideoSection(config['opening'].get('path', None), FPS * open_duration)
#
#    #Body
#    pic_paths = config['body'].get('path').split(',')
#    inifps = config['body'].getint('inifps', 1)
#    speed = config['body'].getint('speed', 1)
#    repeat = config['body'].getint('repeat', 1)
#
#    number = FPS / inifps / speed
#    body_sections = [VideoSection(path, config['body'].getint('duration', 0), number, repeat) for path in pic_paths]
#
#    #Ending
#    end_duration = config['ending'].getint('duration', 0)  # seconds
#    end_section = VideoSection(config['ending'].get('path', None), FPS * end_duration)
#
#    #Prepare pictures in tmp dir
#    tmp_path = tempfile.mkdtemp(dir=args.tmp)
#    logger.debug('tmp_path for pictures %s', tmp_path)
#
#    prepare_pictures(tmp_path, opening_section, body_sections, end_section,
#                     resolution=resolution, tmp_loc=args.tmp)
#
#    #Encode the movie
#    logger.info('Generate the movie...')
#    os.chdir(tmp_path)
#    command = ['mencoder', 'mf://*.png', '-mf', 'fps='+str(FPS),
#               '-vf', 'scale=800:600',
#               '-o', 'output.avi',
#               '-ovc', 'xvid',
#               '-xvidencopts', 'bitrate=500'
#               ]
#    logging.debug('command: ' + str(command))
#    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    stdout, stderr = process.communicate()
#    logging.debug(stdout.decode('utf8'))
#    logging.warning(stderr.decode('utf8'))
#
#    #Copy the movie
#    logging.debug('Move to %s' % cwd)
#    shutil.copy('output.avi', os.path.join(cwd, output + '.avi'))
#    #Delete the tmp dir
#    logging.debug('Delete the tmp_dir %s' % tmp_path)
#    shutil.rmtree(tmp_path)



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

    cwd = os.getcwd()
    FPS = 25
    resolution = (800, 600)
    correct_json_version = 0.1

    vid = Video(resolution, tmp_dir=args.tmp)

    import json
    from collections import OrderedDict

    root_dir = os.path.split(os.path.abspath(args.conf))[0]
    logger.debug('root_dir: %s' % root_dir)
    with open(args.conf, 'r') as jsonfile:
        conf = json.load(jsonfile, object_pairs_hook=OrderedDict)
        for section, value in conf.items():
            if section == 'meta':
                logger.debug('detected json version: ' + str(value['jsonversion']))
                if not value['jsonversion'] == correct_json_version:
                    #FIXME: look for a better exception
                    raise ValueError('Your jsonfile does not look to be at the correct version')
            if section == 'movie':
                output = value['output']
            if section == 'data':
                for subsection, subvalue in value.items():
                    if subvalue['type'] == 'tex':
                        duration = subvalue['duration']
                        path = os.path.join(root_dir, subvalue['path'])
                        number = FPS * duration
                        number = 1 #FIXME
                        vid.populate_with_slides(path, number)
                    elif subvalue['type'] == 'image':
                        path = os.path.join(root_dir, subvalue['path'])
                        inifps = subvalue['inifps']
                        speed = subvalue['speed']
                        repeat = subvalue['repeat']

                        number = FPS / inifps / speed
                        number = 1 # FIXME
                        vid.populate_with_pictures(path, number, repeat)
                    else:
                        raise ValueError('Wrong type')

        vid.make(cwd, output=output, fps=FPS)
