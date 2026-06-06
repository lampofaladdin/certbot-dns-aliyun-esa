# Contributing

Thanks for your interest in contributing to `certbot-dns-aliyun-esa`.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

## Tests

```bash
pytest
```

Before opening a pull request, please make sure tests pass and Certbot can discover the plugin:

```bash
certbot plugins | grep -A 5 dns-aliyun-esa
```

## Security

Do not include real Aliyun AccessKeys, Certbot account keys, private keys, or certificate material in issues, pull requests, screenshots, or test fixtures.
