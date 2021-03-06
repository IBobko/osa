PG_TYPE_BOOL = 16
PG_TYPE_BYTEA = 17
PG_TYPE_CHAR = 18
PG_TYPE_NAME = 19
PG_TYPE_INT8 = 20
PG_TYPE_INT2 = 21
PG_TYPE_INT28 = 22
PG_TYPE_INT4 = 23
PG_TYPE_REGPROC = 24
PG_TYPE_TEXT = 25
PG_TYPE_OID = 26
PG_TYPE_TID = 27
PG_TYPE_XID = 28
PG_TYPE_CID = 29
PG_TYPE_OID8 = 30
PG_TYPE_SET = 32
PG_TYPE_CHAR2 = 409
PG_TYPE_CHAR4 = 410
PG_TYPE_CHAR8 = 411
PG_TYPE_POINT = 600
PG_TYPE_LSEG = 601
PG_TYPE_PATH = 602
PG_TYPE_BOX = 603
PG_TYPE_POLYGON = 604
PG_TYPE_FILENAME = 605
PG_TYPE_FLOAT4 = 700
PG_TYPE_FLOAT8 = 701
PG_TYPE_ABSTIME = 702
PG_TYPE_RELTIME = 703
PG_TYPE_TINTERVAL = 704
PG_TYPE_UNKNOWN = 705
PG_TYPE_MONEY = 790
PG_TYPE_OIDINT2 = 810
PG_TYPE_OIDINT4 = 910
PG_TYPE_OIDNAME = 911
PG_TYPE_BPCHAR = 1042
PG_TYPE_VARCHAR = 1043
PG_TYPE_DATE = 1082
PG_TYPE_TIME = 1083
PG_TYPE_DATETIME = 1184
PG_TYPE_TIMESTAMPTZ = 1296
PG_TYPE_TIMESTAMP = 1114
PG_TYPE_NUMERIC = 1700

char_types = [PG_TYPE_CHAR, PG_TYPE_CHAR2, PG_TYPE_CHAR4, PG_TYPE_CHAR8, PG_TYPE_NAME, PG_TYPE_BPCHAR]

blob_types = [PG_TYPE_BYTEA]

varchar_types = [PG_TYPE_VARCHAR, PG_TYPE_TEXT]

timestamp_types = [PG_TYPE_TIMESTAMPTZ, PG_TYPE_TIMESTAMP, PG_TYPE_DATETIME, PG_TYPE_ABSTIME]

int_types = [PG_TYPE_BOOL, PG_TYPE_OID, PG_TYPE_XID, PG_TYPE_INT2, PG_TYPE_INT4]
