#!/bin/bash

if [[ 0 == 1 ]]; then
NAME="Demo3.mp4"
URL="https://synthesia-ttv-data.s3.amazonaws.com/video_data/5a218015-6827-4a5f-af3f-527abbe22bb2/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide1.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=N8jifSBEPOoycIZ8D3Zpso521N0%3D&Expires=1756592762"
curl -L -o "$NAME" "$URL"
fi;

# Put your list in a heredoc (or replace with a file)
cat <<EOF | while read -r NAME URL
slide7 https://synthesia-ttv-data.s3.amazonaws.com/video_data/12be4aee-5e4a-4fc0-a7a6-5f2a043cc6c6/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide7.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=O369Jrl4uouPv7FTSYKSCgnxv%2F4%3D&Expires=1756593684
slide5 https://synthesia-ttv-data.s3.amazonaws.com/video_data/11e7ee20-767b-44bc-86b8-e60bae784a43/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide5.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=%2BBbYLXGUO8QEkhjtYSuhtRFJdsM%3D&Expires=1756593684
slide4 https://synthesia-ttv-data.s3.amazonaws.com/video_data/25fb8e9d-805d-4265-a1be-b909d31449b6/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide4.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=ijvHRgJiB5f0L%2FNJ7uRfXT84zrI%3D&Expires=1756593684
slide3 https://synthesia-ttv-data.s3.amazonaws.com/video_data/f987944f-6e4b-4bc0-b616-b4685944f417/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide3.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=eLU0reM27ksJGCRFTj%2FAyNFgoU0%3D&Expires=1756593684
slide2 https://synthesia-ttv-data.s3.amazonaws.com/video_data/b3d69197-e283-4d67-976f-6aefef17514f/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide2.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=BHq%2Bm%2B5gQePU4TgxLvYh0q4hLaI%3D&Expires=1756593684
slide1 https://synthesia-ttv-data.s3.amazonaws.com/video_data/5a218015-6827-4a5f-af3f-527abbe22bb2/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide1.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=DLmrWFJJfNNwr1%2BvjsrYg1eRyvU%3D&Expires=1756593684
EOF
do
    # Save current name and URL for next iteration
    if [ -n "$prev_name" ]; then
        echo "Downloading next URL into $prev_name.mp4"
        curl -L -o "$prev_name.mp4" "$URL"
    fi
    prev_name="$NAME"
done
