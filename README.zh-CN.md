# certbot-dns-aliyun-esa

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Certbot](https://img.shields.io/badge/certbot-2.0%2B-green.svg)](https://certbot.eff.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

这是一个用于 Certbot 的阿里云 ESA DNS 验证插件。它通过阿里云 ESA DNS API 自动创建和删除 ACME `dns-01` 验证所需的 TXT 记录，支持泛域名证书。

> 本项目是社区维护项目，不是阿里云或 Certbot 官方插件。

English documentation: see [README.md](README.md).

## 功能特性

- Certbot Authenticator-only 插件，只负责 `dns-01` 验证。
- 支持泛域名证书，例如 `*.example.com`。
- 使用阿里云 ESA 的 `CreateRecord`、`ListRecords`、`DeleteRecord` 和 `ListSites` API。
- 清理 TXT 记录时同时匹配记录名、记录类型和 TXT 值，避免误删其他记录。
- 支持同一个 `_acme-challenge` 记录名下存在多个 TXT 值。

## 安装

### 从 PyPI 安装

```bash
pip install certbot-dns-aliyun-esa
```

### 从源码安装

```bash
git clone https://github.com/lampofaladdin/certbot-dns-aliyun-esa.git
cd certbot-dns-aliyun-esa
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

确认 Certbot 可以发现插件：

```bash
certbot plugins
```

插件列表中应出现 `dns-aliyun-esa`。

## 凭证配置

创建一个 INI 文件，例如 `/etc/letsencrypt/aliyun-esa.ini`：

```ini
dns_aliyun_esa_access_key_id = your-access-key-id
dns_aliyun_esa_access_key_secret = your-access-key-secret
```

限制文件权限：

```bash
chmod 600 /etc/letsencrypt/aliyun-esa.ini
```

AccessKey 至少需要以下权限：

- 查询 ESA 站点列表；
- 创建 DNS 记录；
- 查询 DNS 记录；
- 删除 DNS 记录。

建议使用最小权限的 RAM 用户或角色，不要使用主账号 AccessKey。

## 使用方法

签发证书：

```bash
certbot certonly \
  --authenticator dns-aliyun-esa \
  --dns-aliyun-esa-credentials /etc/letsencrypt/aliyun-esa.ini \
  --dns-aliyun-esa-propagation-seconds 60 \
  -d example.com \
  -d '*.example.com'
```

首次测试建议使用 Let's Encrypt 测试环境，避免触发生产环境频率限制：

```bash
certbot certonly \
  --test-cert \
  --authenticator dns-aliyun-esa \
  --dns-aliyun-esa-credentials /etc/letsencrypt/aliyun-esa.ini \
  --dns-aliyun-esa-propagation-seconds 60 \
  -d example.com \
  -d '*.example.com'
```

## 插件参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--dns-aliyun-esa-credentials` | 必填 | 凭证 INI 文件路径。 |
| `--dns-aliyun-esa-propagation-seconds` | `60` | 创建 TXT 记录后等待 DNS 传播的秒数。如果验证失败，可以适当调大。 |
| `--dns-aliyun-esa-region-id` | `cn-hangzhou` | 阿里云 ESA Region ID。 |
| `--dns-aliyun-esa-endpoint` | `esa.cn-hangzhou.aliyuncs.com` | 传给阿里云官方 SDK 的 ESA API endpoint。如果你的环境需要其他区域 endpoint，可以覆盖这个参数。 |
| `--dns-aliyun-esa-ttl` | `1` | 创建 TXT 记录时使用的 TTL。`1` 与阿里云生成示例中的默认行为一致。 |

## 工作原理

Certbot 在执行 `dns-01` 验证时会把验证记录名和 TXT 值传给插件，例如：

```text
_acme-challenge.example.com TXT "validation-value"
```

插件执行流程：

1. 调用 ESA `ListSites` 获取可管理站点；
2. 根据申请的域名匹配最合适的 ESA site；
3. 调用 ESA `CreateRecord` 创建 TXT 记录；
4. 由 Certbot 等待 DNS 传播；
5. 验证完成后调用 ESA `ListRecords` 查找记录；
6. 只删除记录名、类型和 TXT 值都匹配的记录。

## 开发

安装开发依赖：

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

运行测试：

```bash
pytest
```

检查 Certbot 插件发现：

```bash
certbot plugins | grep -A 5 dns-aliyun-esa
```

本地构建并检查包元数据：

```bash
python -m pip install --upgrade build twine
rm -rf dist build *.egg-info src/*.egg-info
python -m build
python -m twine check dist/*
```

## 发布

本仓库包含 GitHub Actions 工作流：

- [.github/workflows/ci.yml](.github/workflows/ci.yml)：运行测试、插件发现检查、包构建和元数据检查。
- [.github/workflows/publish.yml](.github/workflows/publish.yml)：在 GitHub Release 发布时发布到 PyPI。

发布使用 PyPI Trusted Publishing，因此不需要把 PyPI API Token 保存到 GitHub Secrets。

### 配置 PyPI Trusted Publishing

在 PyPI 项目 `certbot-dns-aliyun-esa` 的设置里添加 pending trusted publisher：

| 字段 | 值 |
| --- | --- |
| Owner | `lampofaladdin` |
| Repository name | `certbot-dns-aliyun-esa` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

### 发布一个版本

1. 更新 [pyproject.toml](pyproject.toml) 里的 `version`。
2. 更新 [CHANGELOG.md](CHANGELOG.md)。
3. 提交并推送到 `main`。
4. 创建并推送匹配的 tag，例如 `v0.1.1`。
5. 基于该 tag 创建 GitHub Release。
6. 发布 GitHub Release 后会触发 PyPI 发布 workflow。

## 安全建议

- 不要提交任何真实凭证文件。
- 凭证文件权限建议设置为 `0600`。
- 使用最小权限 RAM 用户/角色。
- 正式签发前先使用 `--test-cert` 测试。

## 许可证

Apache License 2.0。详见 [LICENSE](LICENSE)。
