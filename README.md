# certbot-dns-aliyun-esa

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Certbot](https://img.shields.io/badge/certbot-2.0%2B-green.svg)](https://certbot.eff.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Aliyun ESA DNS authenticator plugin for Certbot. It creates and removes Aliyun ESA DNS TXT records for ACME `dns-01` challenges, including wildcard certificates.

> This project is community-maintained and is not an official Aliyun or Certbot plugin.

中文文档：见 [README.zh-CN.md](README.zh-CN.md)。

## Features

- Certbot Authenticator-only plugin for `dns-01` validation.
- Supports wildcard certificates, for example `*.example.com`.
- Uses Aliyun ESA `CreateRecord`, `ListRecords`, `DeleteRecord`, and `ListSites` APIs.
- Deletes TXT records by matching record name, record type, and TXT value to avoid removing unrelated records.
- Supports multiple TXT values under the same `_acme-challenge` name.

## Installation

### From PyPI

```bash
pip install certbot-dns-aliyun-esa
```

### From source

```bash
git clone https://github.com/lampofaladdin/certbot-dns-aliyun-esa.git
cd certbot-dns-aliyun-esa
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

Verify that Certbot can discover the plugin:

```bash
certbot plugins
```

You should see `dns-aliyun-esa` in the plugin list.

## Credentials

Create an INI file, for example `/etc/letsencrypt/aliyun-esa.ini`:

```ini
dns_aliyun_esa_access_key_id = your-access-key-id
dns_aliyun_esa_access_key_secret = your-access-key-secret
```

Protect the file:

```bash
chmod 600 /etc/letsencrypt/aliyun-esa.ini
```

The AccessKey needs permissions to:

- list ESA sites;
- create DNS records;
- list DNS records;
- delete DNS records.

## Usage

Issue a certificate:

```bash
certbot certonly \
  --authenticator dns-aliyun-esa \
  --dns-aliyun-esa-credentials /etc/letsencrypt/aliyun-esa.ini \
  --dns-aliyun-esa-propagation-seconds 60 \
  -d example.com \
  -d '*.example.com'
```

Use staging first when testing automation:

```bash
certbot certonly \
  --test-cert \
  --authenticator dns-aliyun-esa \
  --dns-aliyun-esa-credentials /etc/letsencrypt/aliyun-esa.ini \
  --dns-aliyun-esa-propagation-seconds 60 \
  -d example.com \
  -d '*.example.com'
```

## Plugin options

| Option | Default | Description |
| --- | --- | --- |
| `--dns-aliyun-esa-credentials` | required | Path to the credentials INI file. |
| `--dns-aliyun-esa-propagation-seconds` | `60` | Seconds to wait before ACME validation. Increase this if DNS propagation is slow. |
| `--dns-aliyun-esa-region-id` | `cn-hangzhou` | Aliyun ESA region ID. |
| `--dns-aliyun-esa-endpoint` | `esa.cn-hangzhou.aliyuncs.com` | Aliyun ESA API endpoint passed to the official SDK. Override it if your environment needs another regional endpoint. |
| `--dns-aliyun-esa-ttl` | `1` | TTL for created TXT records. `1` follows ESA default TTL behavior from Aliyun's generated sample. |

## How it works

Certbot calls the plugin with a validation name such as `_acme-challenge.example.com` and a TXT value. The plugin then:

1. lists Aliyun ESA sites;
2. matches the requested domain to the best ESA site name;
3. creates a TXT record using ESA `CreateRecord`;
4. waits for DNS propagation through Certbot's DNS plugin flow;
5. finds the exact TXT record by record name, type, and value;
6. deletes only that matching TXT record.

## Development

Install development dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

Run tests:

```bash
pytest
```

Run a basic plugin discovery check:

```bash
certbot plugins | grep -A 5 dns-aliyun-esa
```

## Security notes

- Do not commit credentials files.
- Restrict credential file permissions to `0600`.
- Prefer least-privilege RAM users/roles for the Aliyun AccessKey.
- Test with `--test-cert` before requesting production certificates.

## License

Apache License 2.0. See [LICENSE](LICENSE).
