import json
import csv
import boto3

s3 = boto3.client('s3')

def lambda_handler(event, context):
    source_bucket = 'bld-tseed-workshop-input-semillero-2026-q4-b'
    source_key = 'sample_users.csv'
    dest_bucket = 'bld-tseed-workshop-output-semillero-2026-q4-b'
    dest_prefix = 'julian_ruiz/'

    obj = s3.get_object(Bucket=source_bucket, Key=source_key)
    text = obj['Body'].read().decode('utf-8-sig')

    reader = csv.DictReader(text.splitlines())

    written = 0
    for row in reader:
        user_id = row['user_id'].strip()
        s3.put_object(
            Bucket=dest_bucket,
            Key=f"{dest_prefix}{user_id}.json",
            Body=(json.dumps(row, ensure_ascii=False) + '\n').encode('utf-8'),
            ContentType='application/json'
        )
        written += 1

    return {
        'statusCode': 200,
        'body': json.dumps(f'{written} archivos creados')
    }