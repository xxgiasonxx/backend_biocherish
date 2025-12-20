from boto3.resources.base import ServiceResource
import logging

logger = logging.getLogger(__name__)


tables = [
    {
        "TableName": "access_token",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "refresh_token", "AttributeType": "S"}
        ],
        "ProvisionedThroughput": {
            "ReadCapacityUnits": 5, 
            "WriteCapacityUnits": 5
        },
        "GlobalSecondaryIndexes": [
            {
                'IndexName': 'UserIdIndex', # 索引名称
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}, # 以 user_id 为索引键
                ],
                'Projection': {
                    'ProjectionType': 'ALL' # 查询时返回所有字段
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
            {
                'IndexName': 'refreshTokenIndex', # 索引名称
                'KeySchema': [
                    {'AttributeName': 'refresh_token', 'KeyType': 'HASH'}, # 以 refresh_token 为索引键
                ],
                'Projection': {
                    'ProjectionType': 'ALL' # 查询时返回所有字段
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
        ],
    },
    {
        "TableName": "user",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "Email", "AttributeType": "S"},
            {"AttributeName": "Google_ID", "AttributeType": "S"},
        ],
        "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        "GlobalSecondaryIndexes": [
            {
                'IndexName': 'EmailIndex', # 索引名称
                'KeySchema': [
                    {'AttributeName': 'Email', 'KeyType': 'HASH'}, # 以 Email 为索引键
                ],
                'Projection': {
                    'ProjectionType': 'ALL' # 查询时返回所有字段
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
            {
                'IndexName': 'GoogleIDIndex', # 索引名称
                'KeySchema': [
                    {'AttributeName': 'Google_ID', 'KeyType': 'HASH'}, # 以 Google_ID 为索引键
                ],
                'Projection': {
                    'ProjectionType': 'ALL' # 查询时返回所有字段
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
        ],
    },
    {
        "TableName": "bottle",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "device_id", "AttributeType": "S"}
        ],
        "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        "GlobalSecondaryIndexes": [
            {
                'IndexName': 'UserIdIndex',                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
            {
                'IndexName': 'DeviceIdIndex',
                'KeySchema': [
                    {'AttributeName': 'device_id', 'KeyType': 'HASH'},
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
        ],
    },
    {
        "TableName": "deviceset",
        "KeySchema": [{"AttributeName": "device_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "device_id", "AttributeType": "S"}],
        "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
    },
    {
        "TableName": "detect_record",
        "KeySchema": [
            {"AttributeName": "detect_record_id", "KeyType": "HASH"}, # 分區鍵
        ],
        "AttributeDefinitions": [
            {"AttributeName": "bottle_id", "AttributeType": "S"},
            {"AttributeName": "device_id", "AttributeType": "S"},
            {"AttributeName": "detect_record_id", "AttributeType": "S"}
        ],
        "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        "GlobalSecondaryIndexes": [
            {
                'IndexName': 'BottleIdIndex',                
                'KeySchema': [
                    {'AttributeName': 'bottle_id', 'KeyType': 'HASH'},                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
            {
                'IndexName': 'DeviceIdIndex',                
                'KeySchema': [
                    {'AttributeName': 'device_id', 'KeyType': 'HASH'},                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            },
        ],
    },
    {
        "TableName": "detect_record_state",
        "KeySchema": [{"AttributeName": "detect_record_state_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "detect_record_state_id", "AttributeType": "S"}],
        "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
    }
]


def init_tables(dynamodb: ServiceResource):
    try:
        for table_def in tables:
            if table_def["TableName"] in dynamodb.meta.client.list_tables()["TableNames"]:
                logger.info(f"資料表 {table_def['TableName']} 已存在，跳過建立。")
                continue

            # table = dynamodb.create_table(
            #     TableName=table_def["TableName"],
            #     KeySchema=table_def["KeySchema"],
            #     AttributeDefinitions=table_def["AttributeDefinitions"],
            #     ProvisionedThroughput=table_def["ProvisionedThroughput"]
            # )
            table = dynamodb.create_table(**table_def)

            logger.info(f"正在建立資料表 {table_def['TableName']}...")
            table.wait_until_exists()
            logger.info(f"資料表 {table_def['TableName']} 建立完成。")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        logger.info()