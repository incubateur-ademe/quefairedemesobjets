# This is the query to get our north star metric:
#   The number of oriented users
#   who were exposed to a product/family page
#   of who search in the map
QUERY_DATA = {
    "query": {
        "dateRange": {
            "date_from": "2025-01-29T00:00:00+00:00",  # first day with data
            "date_to": None,
            "explicitDate": False,
        },
        "filterTestAccounts": True,
        "interval": "day",
        "kind": "TrendsQuery",
        "properties": {
            "type": "AND",
            "values": [
                {
                    "type": "AND",
                    "values": [
                        {
                            "key": "conversionScore",
                            "operator": "gt",
                            "type": "person",
                            "value": "0",
                        }
                    ],
                }
            ],
        },
        "series": [
            {"event": "$set", "kind": "EventsNode", "math": "dau", "name": "$set"}
        ],
        "trendsFilter": {},
        "version": 2,
    },
    "name": "Get insight data",
}
