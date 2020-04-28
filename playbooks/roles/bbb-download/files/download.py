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
# Deskshare
SOURCE_DESKSHARE = source_dir + 'deskshare/deskshare.mp4'
TMP_DESKSHARE_FILE = temp_dir + 'deskshare.mp4'


def extract_timings(bbb_version):
    doc = minidom.parse(events_file)
    dictionary = {}
    total_length = 0
    j = 0

    for image in doc.getElementsByTagName('image'):
        path = image.getAttribute('xlink:href')

        if j == 0 and '2.0.0' > bbb_version:
            path = u'/usr/local/bigbluebutton/core/scripts/logo.png'
            j += 1

        in_times = str(image.getAttribute('in')).split(' ')
        out_times = image.getAttribute('out').split(' ')

        try:
            temp = float(out_times[len(out_times) - 1])

            if temp > total_length:
                total_length = temp

            occurrences = len(in_times)
            for i in range(occurrences):
                dictionary[float(in_times[i])] = temp_dir + str(path)

        except:
            print >> sys.stderr, "Exception extract_timings"
            print >> sys.stderr, str(image.getAttribute('in')).split(' ')
            print >> sys.stderr, str(image.getAttribute('out')).split(' ')
            print >> sys.stderr, "occurrences"
            print >> sys.stderr, occurrences
            print >> sys.stderr, "dictionary"
            print >> sys.stderr, dictionary
            print >> sys.stderr, "total_length"
            print >> sys.stderr, total_length

    return dictionary, total_length

def create_drawing(dims,result):
    try:
        print >> sys.stderr, "-=create_drawing=-"
        copy_mp4(SOURCE_DESKSHARE, TMP_DESKSHARE_FILE)

        drawing_list = temp_dir + 'drawing_list.txt'
        f = open(drawing_list, 'w')

        tree = ET.parse(source_dir + 'cursor.xml')
        cursor={}
        for child in tree.findall('event'):
            cord=child.find('cursor').text.split()
            cursor[round(float(child.get('timestamp')),1)]={'x':float(cord[0]),'y':float(cord[1])};

        images=[]
        svg=collections.OrderedDict()

        html = open(source_dir + "shapes.svg", "r")
        parsed_html = BeautifulSoup(html,'lxml')
        for elem in parsed_html.svg:
          if elem.name == 'image':
            images.append(elem)
            id=elem['id']
          if elem.name == 'g':
            for elem_2nd in elem:
              if elem_2nd.name == 'g':
                if id in svg:
                  svg[id].append(elem_2nd)
                else:
                  svg[id] = [elem_2nd]
        for img in images:
          bild=collections.OrderedDict()
          video_list=[]
          duration_list=[]
          duration=0.1
          if "deskshare.png" in img['xlink:href']:
            ffmpeg.trim_video_by_seconds(TMP_DESKSHARE_FILE, round(float(img['in']),1), round(float(img['out']),1)-round(float(img['in']),1), temp_dir + "draw_" + str(img['id']) + ".mp4")
            ffmpeg.mp4_to_ts(temp_dir + "draw_" + str(img['id']) + ".mp4", temp_dir + "draw_" + str(img['id']) + ".ts")
            f.write('file ' + temp_dir + "draw_" + str(img['id']) + ".ts" + '\n')
          else:
            background = "<image width='"+img['width']+"' height='"+img['height']+"' xlink:href='data:image/png;base64,"+base64.b64encode(open(img['xlink:href'], "rb").read())+"'/>"
            bild.update({ 'background' : background })
            if img['id'] in svg:
              for time in numpy.arange(round(float(img['in']),1),round(float(img['out']),1)+0.1,0.1):
                time=round(time,1)
                before=bild.copy()

                if time in cursor:
                    bild.update({ 'cursor' : cursor[time] })

                for draw in svg[img['id']]:
                  if "poll" in str(draw):
                    poll_base="data:image/svg+xml;base64,"+base64.b64encode(open(draw.image['xlink:href'], "rb").read())
                    if round(float(draw['timestamp']),1) == time or (round(float(draw['timestamp']),1) < round(float(img['in']),1) and draw['undo'] == '-1'):
                      bild.update({ draw['shape'] : str(draw).replace('visibility:hidden;', '').replace('style="visibility:hidden"', '').replace('visibility:hidden', '').replace('\n', '').replace(draw.image['xlink:href'],poll_base) })
                    if round(float(draw['undo']),1) == time:
                      bild.update({ draw['shape'] : '' })
                  else:
                    if round(float(draw['timestamp']),1) == time or (round(float(draw['timestamp']),1) < round(float(img['in']),1) and draw['undo'] == '-1'):
                      bild.update({ draw['shape'] : str(draw).replace('visibility:hidden;', '').replace('style="visibility:hidden"', '').replace('visibility:hidden', '').replace('\n', '') })
                    if round(float(draw['undo']),1) == time:
                      bild.update({ draw['shape'] : '' })

                if before != bild:
                  write_svg_file = temp_dir + "draw_" + str(time) + ".svg"
                  write_svg = open(write_svg_file, 'a+')
                  write_svg.write("<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1' width='" + str(img['width']) + "' height='" + str(img['height']) + "'>")
                  if len(bild) >= 1:
                    for k, v in bild.items():
                      if v and k != 'cursor':
                        write_svg.write(v)
                  if 'cursor' in bild:
                    write_svg.write("<circle r='8' cx='" + str(int(img['width'])*float(bild['cursor']['x'])) + "' cy='" + str(int(img['height'])*float(bild['cursor']['y'])) + "' style='fill:red;stroke:gray;stroke-width:0.1'/>")
                  write_svg.write("</svg>")
                  write_svg.close()
                  if len(video_list)!=0:
                    duration_list.append(round(duration,1))
                    duration=0.1
                  video_list.append(write_svg_file)
                else:
                  duration=duration+0.1
                if time == round(float(img['out']),1):
                  duration_list.append(round(duration,1))
                  duration=0.1
            else:
              write_svg_file = temp_dir + "draw_" + str(img['id']) + ".svg"
              write_svg = open(write_svg_file, 'a+')
              write_svg.write("<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1' width='" + str(img['width']) + "' height='" + str(img['height']) + "'>")
              write_svg.write("<rect xmlns='http://www.w3.org/2000/svg' width='100%' height='100%' fill='#00ff00'/>")
              write_svg.write(background)
              write_svg.write("</svg>")
              write_svg.close()
              video_list.append(write_svg_file)
              duration_list.append(round(round(float(img['out']),1)-round(float(img['in']),1),1))
            if not len(video_list) > 0:
              write_svg_file = temp_dir + "draw_" + str(img['id']) + ".svg"
              write_svg = open(write_svg_file, 'a+')
              write_svg.write("<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1' width='" + str(img['width']) + "' height='" + str(img['height']) + "'>")
              write_svg.write("<rect xmlns='http://www.w3.org/2000/svg' width='100%' height='100%' fill='#00ff00'/>")
              write_svg.write(background)
              write_svg.write("</svg>")
              write_svg.close()
              video_list.append(write_svg_file)
              duration_list.append(round(round(float(img['out']),1)-round(float(img['in']),1),1))
            for i in range(0,len(video_list)):
              ffmpeg.create_video_from_image(video_list[i], round(float(duration_list[i]),1), video_list[i]+".ts")
              f.write('file ' + video_list[i] + ".ts" + '\n')
        f.close();
        ffmpeg.concat_videos(drawing_list, result)
        os.remove(drawing_list)
    except Exception, e:
        print(e)
        print >> sys.stderr, "Exception create_drawing"

def get_presentation_dims(presentation_name):
    doc = minidom.parse(events_file)
    images = doc.getElementsByTagName('image')

    for el in images:
        name = el.getAttribute('xlink:href')
        pattern = presentation_name
        if re.search(pattern, name):
            height = int(el.getAttribute('height'))
            width = int(el.getAttribute('width'))
            return height, width


def prepare(bbb_version):
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    if not os.path.exists('audio'):
        global audio_path
        os.mkdir(audio_path)
        ffmpeg.extract_audio_from_video(source_dir + 'video/webcams.mp4', audio_path + 'audio.ogg')


    shutil.copytree("presentation", temp_dir + "presentation")
    dictionary, length = extract_timings(bbb_version)
    # debug
    print >> sys.stderr, "dictionary"
    print >> sys.stderr, (dictionary)
    print >> sys.stderr, "length"
    print >> sys.stderr, (length)
    dims = get_different_presentations(dictionary)
    # debug
    print >> sys.stderr, "dims"
    print >> sys.stderr, (dims)
    return dictionary, length, dims


def get_different_presentations(dictionary):
    times = dictionary.keys()
    print >> sys.stderr, "times"
    print >> sys.stderr, (times)
    presentations = []
    dims = {}
    for t in times:

        name = dictionary[t].split("/")[7]
        # debug
        print >> sys.stderr, "name"
        print >> sys.stderr, (name)
        if name not in presentations:
            presentations.append(name)
            dims[name] = get_presentation_dims(name)

    return dims


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

def bbbversion():
    global bbb_ver
    bbb_ver = 0
    s_events = minidom.parse(source_events)
    for event in s_events.getElementsByTagName('recording'):
        bbb_ver = event.getAttribute('bbb_version')
    return bbb_ver


def main():
    sys.stderr = open(LOGFILE, 'a')
    print >> sys.stderr, "\n<-------------------" + time.strftime("%c") + "----------------------->\n"

    bbb_version = bbbversion()
    print >> sys.stderr, "bbb_version: " + bbb_version

    os.chdir(source_dir)
    print >> sys.stderr, "Verifying record"
    try:
        if not video_exists(source_dir + '_presentation.mp4'):
            dictionary, length, dims = prepare(bbb_version)
            audio = audio_path + 'audio.ogg'
            result = source_dir + '_presentation.mp4'
            drawing = temp_dir + 'drawing.mp4'
            try:
                print >> sys.stderr, "Creating presentation's .Mp4 video..."
                print >> sys.stderr, "Drawing"
                create_drawing(dims,drawing)
                print >> sys.stderr, "Slideshow + audio"
                ffmpeg.mux_slideshow_audio(drawing, audio, result)

                print >> sys.stderr, "Presentation's Mp4 Creation Done"
            except:
                print >> sys.stderr, "Presentation's Mp4 Creation Failed"
        else:
            print >> sys.stderr, "Presentation record already exists: " + result
    finally:
        print >> sys.stderr, "Cleaning up temp files..."
        cleanup()
        print >> sys.stderr, "Process finished"



if __name__ == "__main__":
    main()
