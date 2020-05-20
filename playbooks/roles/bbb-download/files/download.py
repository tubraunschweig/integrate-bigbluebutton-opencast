from xml.dom import minidom
import xml.etree.ElementTree as ET
import sys
import os
import shutil
import zipfile
import ffmpeg
import re
import time
from bs4 import BeautifulSoup
import numpy
import collections
import base64
import glob

tmp = sys.argv[1].split('-')
try:
    if tmp[2] == 'presentation':
        meetingId = tmp[0] + '-' + tmp[1]
    else:
        sys.exit()
except IndexError:
    meetingId = sys.argv[1]

PATH = '/var/bigbluebutton/published/presentation/'
LOGS = '/var/log/bigbluebutton/download/'
source_dir = PATH + meetingId + "/"
temp_dir = source_dir + 'temp/'

audio_path = temp_dir + 'audio/'
events_file = 'shapes.svg'
LOGFILE = LOGS + meetingId + '.log'
ffmpeg.set_logfile(LOGFILE)
source_events = '/var/bigbluebutton/recording/raw/' + meetingId + '/events.xml'
SOURCE_DESKSHARE = source_dir + 'deskshare/deskshare.mp4'
TMP_DESKSHARE_FILE = temp_dir + 'deskshare.mp4'


def create_drawing(result):
    try:
        print >> sys.stderr, "[" + meetingId + "]-=create_drawing=-"
        copy_mp4(SOURCE_DESKSHARE, TMP_DESKSHARE_FILE)

        drawing_list = temp_dir + 'drawing_list.txt'
        f = open(drawing_list, 'w')

        tree = ET.parse(source_dir + 'cursor.xml')
        cursor = {}
        for child in tree.findall('event'):
            cord = child.find('cursor').text.split()
            cursor[round(float(child.get('timestamp')), 1)] = {'x': float(cord[0]), 'y': float(cord[1])}

        images = []
        svg = collections.OrderedDict()

        html = open(source_dir + "shapes.svg", "r")
        parsed_html = BeautifulSoup(html, 'lxml')
        for elem in parsed_html.svg:
            if elem.name == 'image':
                images.append(elem)
                id = elem['id']
            if elem.name == 'g':
                for elem_2nd in elem:
                    if elem_2nd.name == 'g':
                        if id in svg:
                            svg[id].append(elem_2nd)
                        else:
                            svg[id] = [elem_2nd]
        for img in images:
            bild = collections.OrderedDict()
            video_list = []
            duration_list = []
            duration = 0.1
            image_changed = False
            if "deskshare.png" in img['xlink:href']:
                ffmpeg.trim_video_by_seconds(TMP_DESKSHARE_FILE, round(float(img['in']), 1), round(float(img['out']), 1) - round(float(img['in']), 1), temp_dir + "draw_" + str(img['id']) + ".mp4")
                ffmpeg.mp4_to_ts(temp_dir + "draw_" + str(img['id']) + ".mp4", temp_dir + "draw_" + str(img['id']) + ".ts")
                f.write('file ' + temp_dir + "draw_" + str(img['id']) + ".ts" + '\n')
            else:
                background = "<image width='" + img['width'] + "' height='" + img['height'] + "' xlink:href='data:image/png;base64," + base64.b64encode(open(img['xlink:href'], "rb").read()) + "'/>"
                bild.update({'background': background})
                for time in numpy.arange(round(float(img['in']), 1), round(float(img['out']), 1), 0.1):
                    time = round(time, 1)
                    before = bild.copy()
                    if time in cursor:
                        bild.update({'cursor': cursor[time]})
                    if img['id'] in svg:
                        for draw in svg[img['id']]:
                            if "poll" in str(draw):
                                poll_base = "data:image/svg+xml;base64," + base64.b64encode(open(draw.image['xlink:href'], "rb").read())
                                if round(float(draw['timestamp']), 1) == time or (round(float(draw['timestamp']), 1) < round(float(img['in']), 1) and draw['undo'] == '-1'):
                                    bild.update({draw['shape']: str(draw).replace('visibility:hidden;', '').replace('style="visibility:hidden"', '').replace('visibility:hidden', '').replace('\n', '').replace(draw.image['xlink:href'], poll_base)})
                                if round(float(draw['undo']), 1) == time:
                                    bild.update({draw['shape']: ''})
                            else:
                                if round(float(draw['timestamp']), 1) == time or (round(float(draw['timestamp']), 1) < round(float(img['in']), 1) and draw['undo'] == '-1'):
                                    bild.update({draw['shape']: str(draw).replace('visibility:hidden;', '').replace('style="visibility:hidden"', '').replace('visibility:hidden', '').replace('\n', '')})
                                if round(float(draw['undo']), 1) == time:
                                    bild.update({draw['shape']: ''})

                    if before != bild:
                        image_changed = True
                        write_svg_file = temp_dir + "draw_" + str(time) + img['id'] + ".svg"
                        write_svg = open(write_svg_file, 'a+')
                        write_svg.write("<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1' width='" + str(img['width']) + "' height='" + str(img['height']) + "'>")
                        if len(bild) >= 1:
                            for k, v in bild.items():
                                if v and k != 'cursor':
                                    write_svg.write(v)
                        if 'cursor' in bild:
                            write_svg.write("<circle r='8' cx='" + str(int(img['width']) * float(bild['cursor']['x'])) + "' cy='" + str(int(img['height']) * float(bild['cursor']['y'])) + "' style='fill:red;stroke:gray;stroke-width:0.1'/>")
                        write_svg.write("</svg>")
                        write_svg.close()
                        if len(video_list) != 0:
                            duration_list.append(round(duration, 1))
                            duration = 0.1
                        video_list.append(write_svg_file)
                    else:
                        duration = duration + 0.1
                    if time == round(float(img['out']) - 0.1, 1):
                        if image_changed:
                            if round(duration - 0.1, 1) == 0:
                                del video_list[-1]
                            else:
                                duration_list.append(round(duration - 0.1, 1))
                        else:
                            duration_list.append(round(duration - 0.2, 1))
                        duration = 0.1
                for i in range(0, len(video_list)):
                    ffmpeg.create_video_from_image(video_list[i], round(float(duration_list[i]), 1), video_list[i] + ".ts")
                    f.write('file ' + video_list[i] + ".ts" + '\n')
        f.close()
        ffmpeg.concat_videos(drawing_list, result)
        os.remove(drawing_list)
    except Exception, e:
        print(e)
        print >> sys.stderr, "[" + meetingId + "]Exception create_drawing"


def prepare():
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    if not os.path.exists('audio'):
        global audio_path
        os.mkdir(audio_path)
        ffmpeg.extract_audio_from_video(source_dir + 'video/webcams.mp4', audio_path + 'audio.ogg')

    if glob.glob('/var/bigbluebutton/recording/raw/' + meetingId + '/video/*/*.webm'):
        webcams_found = open(source_dir + 'video/webcams.found', 'a+')
        webcams_found.write("Hi, I found some webcams for you!")
        webcams_found.close()

    shutil.copytree("presentation", temp_dir + "presentation")


def cleanup():
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def copy_mp4(result, dest):
    if os.path.exists(result):
        shutil.copy2(result, dest)


def video_exists(file):
    return os.path.exists(file)


def zipdir(path):
    filename = meetingId + '.zip'
    zipf = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for f in files:
            zipf.write(os.path.join(root, f))
    zipf.close()


def main():
    sys.stderr = open(LOGFILE, 'a')

    os.chdir(source_dir)
    print >> sys.stderr, "[" + meetingId + "]Verifying record"
    try:
        if not video_exists(source_dir + '_presentation.mp4'):
            prepare()
            audio = audio_path + 'audio.ogg'
            result = source_dir + '_presentation.mp4'
            drawing = temp_dir + 'drawing.mp4'
            try:
                print >> sys.stderr, "[" + meetingId + "]Creating presentation's .Mp4 video..."
                print >> sys.stderr, "[" + meetingId + "]Drawing"
                create_drawing(drawing)
                print >> sys.stderr, "[" + meetingId + "]Slideshow + audio"
                ffmpeg.mux_slideshow_audio(drawing, audio, result)

                print >> sys.stderr, "[" + meetingId + "]Presentation's Mp4 Creation Done"
            except:
                print >> sys.stderr, "[" + meetingId + "]Presentation's Mp4 Creation Failed"
        else:
            print >> sys.stderr, "[" + meetingId + "]Presentation record already exists: " + result
    finally:
        print >> sys.stderr, "[" + meetingId + "]Cleaning up temp files..."
        cleanup()
        print >> sys.stderr, "[" + meetingId + "]Process finished"


if __name__ == "__main__":
    main()
