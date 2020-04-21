# integrate-bigbluebutton-opencast

This Integration for Opencast is a further development of https://weblog.lkiesow.de/20200318-integrate-bigbluebutton-opencast/ and https://github.com/fernandoheb/bbb-download.

- BigBlueButton 2.2.X is supported (21.04.2020)
- Screenshare supported (21.04.2020)
- Whiteboard partially supported (21.04.2020)

## Bugs

(Still room for improvement)

- The time of the last Whiteboard Slide is longer than the Actual Recording pause time.
- The Ansbile Roles takes to runs to work
- On the Whiteboard Recording, Text Blocks will not appear.

## Requirements

(Still room for improvement)

1. python2.7
2. ffmpeg compiled with libx264 support (included)
3. Installed and configured BigBlueButton Server (2.2.X)
4. Your BigBlueButton creates MP4 Videos
5. A lot of Diskspace for temporary files

## Installation

(Still room for improvement)

1. Check your environment for compatibility with this Integration.
2. Replace the ocseries in download_control.rb at line 56 with your default Opencast Series.
3. Edit the Opencast Settings in download_control.rb starting at line 31.
4. Install the integration with your Ansbile playbook.
5. It is possible that the Ansible Role Fails at the first time.

## Usage

(Still room for improvement)

The Upload to Opencast will only happen if your Room has meta_ocpresenter= defined.
You can add meta_octitle for A subject and meta_ocseries with your Series from Opencast.

The python script that produces the "downloadable" material, will be called for each recording automatically by the BigBlueButton monitoring scripts, after each recording has been transcoded and published.

## Outputs

A link to download the created MP4 manually, will look like this: https://yourBBBserverURL/download/presentation/{meetingID}/{meetingID}_presentation.mp4

Final MP4 video will include only presentation, whiteboard, audio and screenshare (no chat window).
