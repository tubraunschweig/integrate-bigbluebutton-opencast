
import os
import shutil

FFMPEG = 'ffmpeg -threads 2'
VID_ENCODER = 'libx264'


def set_logfile(file):
    global logfile
    logfile = file


def mux_slideshow_audio(video_file, audio_file, out_file):
    command = '%s -i %s -i %s -map 0 -map 1 -codec copy -shortest %s 2>> %s' % (FFMPEG, video_file, audio_file, out_file, logfile)
    os.system(command)


def extract_audio_from_video(video_file, out_file):
    command = '%s -i %s -ab 160k -ac 2 -ar 44100 -vn %s 2>> %s' % (FFMPEG, video_file, out_file, logfile)
    os.system(command)


def create_video_from_image(image, duration, out_file):
    print "*************** create_video_from_image ******************"
    print image, "\n", duration, "\n", out_file
    command = '%s -loop 1 -r 10 -f image2 -i %s -c:v %s -t %s -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" %s 2>> %s' % (FFMPEG, image, VID_ENCODER, duration, out_file, logfile)
    os.system(command)

def concat_videos(video_list, out_file):
    command = '%s -f concat -safe 0 -i %s -vcodec libx264 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" %s 2>> %s' % (FFMPEG, video_list, out_file, logfile)
    os.system(command)


def mp4_to_ts(input, output):
    command = '%s -i %s -c copy -bsf:v h264_mp4toannexb -f mpegts %s 2>> %s' % (FFMPEG, input, output, logfile)
    os.system(command)


def concat_ts_videos(input, output):
    command = '%s -i %s -c copy -bsf:a aac_adtstoasc %s 2>> %s' % (FFMPEG, input, output, logfile)
    os.system(command)


def trim_video(video_file, start, end, out_file):
    start_h = start / 3600
    start_m = start / 60 - start_h * 60
    start_s = start % 60

    end_h = end / 3600
    end_m = end / 60 - end_h * 60
    end_s = end % 60

    str1 = '%d:%d:%d' % (start_h, start_m, start_s)
    str2 = '%d:%d:%d' % (end_h, end_m, end_s)
    command = '%s -ss %s -t %s -i %s -vcodec copy -acodec copy %s 2>> %s' % (FFMPEG, str1, str2, video_file, out_file, logfile)
    os.system(command)


def trim_video_by_seconds(video_file, start, end, out_file):
    command = '%s -ss %s -i %s -vcodec libx264 -t %s %s 2>> %s' % (FFMPEG, start, video_file, end, out_file, logfile)
    os.system(command)


def trim_video_start(dictionary, length, full_vid, video_trimmed):
    times = dictionary.keys()
    times.sort()
    trim_video(full_vid, int(round(times[2])), int(length), video_trimmed)


def mp3_to_aac(mp3_file, aac_file):
    command = '%s -i %s -c:a libfdk_aac %s 2>> %s' % (FFMPEG, mp3_file, aac_file, logfile)
    os.system(command)

#def overlay_video(video_file1,ovelay_file,output_name):
#    command = '%s -i %s -i %s -b:v 1M -filter_complex "[1:v]scale=320:180 [ovrl],  [0:v][ovrl]overlay= main_w - (overlay_w + 10) :  main_h-(overlay_h +10)" %s -y 2>> %s' % (FFMPEG,video_file1,ovelay_file,output_name,logfile)
#    os.system(command)
