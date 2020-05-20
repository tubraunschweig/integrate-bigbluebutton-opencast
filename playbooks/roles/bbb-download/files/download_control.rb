#!/usr/bin/ruby
# encoding: UTF-8

require 'optparse'
require 'psych'
require 'fileutils'
require "shellwords"
require "trollop"
require File.expand_path('../../../lib/recordandplayback', __FILE__)

opts = Trollop::options do
  opt :meeting_id, "Meeting id to archive", :type => String
end
meeting_id = opts[:meeting_id]

logger = Logger.new("/var/log/bigbluebutton/post_publish.log", 'weekly' )
logger.level = Logger::INFO
BigBlueButton.logger = logger

published_files = "/var/bigbluebutton/published/presentation/#{meeting_id}"
meeting_metadata = BigBlueButton::Events.get_meeting_metadata("/var/bigbluebutton/recording/raw/#{meeting_id}/events.xml")

#
# This runs the download script
#
download_status = system("/usr/bin/python /usr/local/bigbluebutton/core/scripts/post_publish/download.py #{meeting_id}")

# Here begins the Opencast Upload
if(download_status)
  oc_server = 'https://opencast-admin.example.com'
  oc_user = 'username:password'
  oc_workflow = 'schedule-and-upload'

  BigBlueButton.logger.info("Check Upload to Opencast for [#{meeting_id}]...")

  ingest = false
  upload = false
  presenter = ''
  presentation = ''
  title = Shellwords.escape(meeting_metadata['meetingName'])
  title = title.gsub('\ ', ' ')
  title = title.gsub('\(', '(')
  title = title.gsub('\)', ')')
  title = title.gsub('\[', '[')
  title = title.gsub('\]', ']')
  title = title.gsub('\ä', 'ä')
  title = title.gsub('\ö', 'ö')
  title = title.gsub('\ü', 'ü')
  title = title.gsub('\Ä', 'Ä')
  title = title.gsub('\Ö', 'Ö')
  title = title.gsub('\Ü', 'Ü')
  title = title.gsub('\=', '=')
  ocpresenter = ''
  octitle = ''
  ocseries = 'dd30a72c-0555-4b4a-a63e-54bfe66e41c8' #Exchange this with your default Series ID
  if meeting_metadata['ocpresenter']
    upload = true
    ocpresenter = Shellwords.escape(meeting_metadata['ocpresenter'])
  end
  if meeting_metadata['octitle']
    octitle = Shellwords.escape(meeting_metadata['octitle'])
    octitle = octitle.gsub('\ ', ' ')
    octitle = octitle.gsub('\(', '(')
    octitle = octitle.gsub('\)', ')')
    octitle = octitle.gsub('\[', '[')
    octitle = octitle.gsub('\]', ']')
    octitle = octitle.gsub('\ä', 'ä')
    octitle = octitle.gsub('\ö', 'ö')
    octitle = octitle.gsub('\ü', 'ü')
    octitle = octitle.gsub('\Ä', 'Ä')
    octitle = octitle.gsub('\Ö', 'Ö')
    octitle = octitle.gsub('\Ü', 'Ü')
    octitle = octitle.gsub('\=', '=')
  end
  if meeting_metadata['ocseries']
    ocseries = Shellwords.escape(meeting_metadata['ocseries'])
  end
  oc_user = Shellwords.escape(oc_user)

  if (File.exists?(published_files + '/video/webcams.mp4')  && File.exists?(published_files + '/video/webcams.found'))
    BigBlueButton.logger.info("Found presenter video")
    ingest = true
    presenter = "-F 'flavor=presenter/source' -F 'BODY1=@#{published_files + '/video/webcams.mp4'}'"
  end
  if (File.exists?(published_files + '/_presentation.mp4'))
    BigBlueButton.logger.info("Found _presentation video")
    ingest = true
    presentation = "-F 'flavor=presentation/source' -F 'BODY2=@#{published_files + '/_presentation.mp4'}'"
  elsif (File.exists?(published_files + '/deskshare/deskshare.mp4'))
    BigBlueButton.logger.info("Found presentation video")
    ingest = true
    presentation = "-F 'flavor=presentation/source' -F 'BODY2=@#{published_files + '/deskshare/deskshare.mp4'}'"
  end
  if (ingest && upload)
    BigBlueButton.logger.info("Uploading...")
    puts `curl -u '#{oc_user}' "#{oc_server}/ingest/addMediaPackage/#{oc_workflow}" #{presenter} #{presentation} -F creator="#{ocpresenter}" -F title="#{title}" -F subject="#{octitle}" -F seriesDCCatalogUri="#{oc_server}/series/#{ocseries}.xml"`
  end
  BigBlueButton.logger.info("Upload for [#{meeting_id}] ends")
else
  BigBlueButton.logger.info("Opencast Upload not possibly [#{meeting_id}]")
end

exit 0
