#!/bin/bash

if [[ 0 == 1 ]]; then
NAME="Demo3.mp4"
URL="https://synthesia-ttv-data.s3.amazonaws.com/video_data/5a218015-6827-4a5f-af3f-527abbe22bb2/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide1.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=N8jifSBEPOoycIZ8D3Zpso521N0%3D&Expires=1756592762"
curl -L -o "$NAME" "$URL"
fi;

# Put your list in a heredoc (or replace with a file)
cat <<EOF | while read -r NAME URL
slide9 https://synthesia-ttv-data.s3.amazonaws.com/video_data/a121063f-ee1e-4161-a47f-2e921a2689d3/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide9.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=iK0TDoAtm5xdD9txw97H0eu%2FneM%3D&Expires=1756673318
slide5 https://synthesia-ttv-data.s3.amazonaws.com/video_data/ae9c4680-45eb-4ada-b6fb-94a3f6186f4b/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide5.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=Hpciadu9v%2FisPOFKyHuf9O6jogM%3D&Expires=1756673319
slide4 https://synthesia-ttv-data.s3.amazonaws.com/video_data/65dea6a6-06fd-4ead-b136-8b20ca0bda2d/transfers/rendered_video.mp4?response-content-disposition=attachment%3Bfilename%3D%22slide4.mp4%22&AWSAccessKeyId=AKIA32NGJ5TS3KPZZ23Z&Signature=iTtEFTEOP1b%2BuXQYIfVipfd7IMM%3D&Expires=1756673319
EOF
do
    # Save current name and URL for next iteration
    if [ -n "$prev_name" ]; then
        echo "Downloading next URL into $prev_name.mp4"
        curl -L -o "$prev_name.mp4" "$URL"
    fi
    prev_name="$NAME"
done
