# serialize images

import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    key = event['s3_key']
    bucket = event['s3_bucket']

    boto3.resource('s3').Bucket(bucket).download_file(key, '/tmp/image.png')

    # Download the data from s3 to /tmp/image.png
    #s3.Bucket(bucket).download_file(key, '/tmp/image.png')
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    ENDPOINT = event['endpoint']
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": [],
            "endpoint": ENDPOINT
        }
    }

# classify images

import json
#import sagemaker
import base64
#from sagemaker.serializers import IdentitySerializer
import boto3

#ENDPOINT = "image-classification-2024-06-03-15-43-34-149"

def lambda_handler(event, context):
    runtime= boto3.client('runtime.sagemaker')
    print("Event:", event.keys())
    
    ENDPOINT = event['body']['endpoint']

    # Decode the image data
    image = base64.b64decode(event['body']['image_data'])

    # Instantiate a Predictor
    predictor = runtime.invoke_endpoint(EndpointName=ENDPOINT, ContentType='application/x-image', Body=image)

    # For this model the IdentitySerializer needs to be "image/png"
    #predictor.serializer = IdentitySerializer("image/png")
    
    # Make a prediction:
    inferences = predictor['Body'].read().decode('utf-8')
    # We return the data back to the Step Function    
    #event['body']['inferences'] = inferences.decode('utf-8')
    infer = [float(x) for x in inferences[1:-1].split(',')]
    return {
        'statusCode': 200,
        'body': json.dumps(event),
        'inferences': infer
    }

# filter images

import json


THRESHOLD = .93


def lambda_handler(event, context):
    
    # Grab the inferences from the event
    inferences = event['inferences']
    
    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = any (x >= THRESHOLD for x in inferences)
    
    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        #raise("THRESHOLD_CONFIDENCE_NOT_MET")
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET: " + str(inferences[0]) + " " + str(inferences[1]))

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }


