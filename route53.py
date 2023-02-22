import boto3

def lambda_handler(event, context):

    HostedZoneId = 'Z1002499PUV5UNUG4OEA'

    # defining clients
    route53 = boto3.client('route53')
    ec2 = boto3.resource('ec2')

    # get publicIP of container
    for detail in event['detail']['attachments'][0]['details']:
        if detail['name'] == 'networkInterfaceId':
            eni_id = detail['value']
            eni = ec2.NetworkInterface(eni_id)
            publicIP = eni.association_attribute['PublicIp']

    # change A record in route 53
    if len(publicIP) > 0:
        route53.change_resource_record_sets(
            HostedZoneId = HostedZoneId,
            ChangeBatch = {
                'Changes': [
                  {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'kilimanjaro.lauba.cz',
                        'Type': 'A',
                        'TTL': 300,
                        'ResourceRecords': [
                            {
                            'Value': publicIP
                            }
                        ]
                    }
                  }
                ]
              }
            )
        return "Success"

    else: return "publicIP not found"
