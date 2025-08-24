curl --request GET      --url 'https://api.synthesia.io/v2/videos?limit=20&offset=0'      --header 'Authorization: be460062502ee67f43509256c12c9a15'      --header 'accept: application/json' >status.txt

jq -r '.videos[] 
  | [ 
      .id,
      (.createdAt     | strflocaltime("%Y-%m-%d %H:%M:%S")), 
      (.lastUpdatedAt | strflocaltime("%Y-%m-%d %H:%M:%S")),
      .title, 
      .status,
      .download
    ] 
  | @tsv' status.txt | column -t -s $'\t'
