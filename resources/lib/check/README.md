## Check Provider Tool

Usage:

```shell
python check_tool.py -n <provider_name> -k <keyword> -q <query> -pr <results_page> -pc <chapters_page>
```

- Values for keyword: `search`, `popular`, `marvel`, `dc`, `darkhorse` and `by_letter`
- query is optional (only used for `search` and `by_letter` keywords)
- both page values are optional (default is `1`)
