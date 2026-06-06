from types import SimpleNamespace

from certbot import errors

from certbot_dns_aliyun_esa._internal import aliyun_esa
from certbot_dns_aliyun_esa._internal.aliyun_esa import AliyunEsaClient


class FakeAliyunError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class FakeModels:
    class CreateRecordRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class CreateRecordRequestData:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class DeleteRecordRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class ListSitesRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class ListRecordsRequest:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)


class FakeSdkClient:
    def __init__(self):
        self.created = []
        self.deleted = []
        self.list_records_requests = []
        self.records = []
        self.create_record_errors = []

    def list_sites(self, request):
        return SimpleNamespace(
            body=SimpleNamespace(
                sites=[
                    SimpleNamespace(site_id=1, site_name="example.com"),
                    SimpleNamespace(site_id=2, site_name="bar.example.com"),
                ],
                page_size=500,
                total_count=2,
            )
        )

    def create_record(self, request):
        self.created.append(request)
        if self.create_record_errors:
            raise self.create_record_errors.pop(0)
        return SimpleNamespace(body=SimpleNamespace(record_id=123))

    def list_records(self, request):
        self.list_records_requests.append(request)
        return SimpleNamespace(
            body=SimpleNamespace(records=self.records, page_size=500, total_count=len(self.records))
        )

    def delete_record(self, request):
        self.deleted.append(request)
        return SimpleNamespace(body=SimpleNamespace())


def make_client(monkeypatch):
    monkeypatch.setattr(aliyun_esa, "esa_models", FakeModels)
    sdk_client = FakeSdkClient()
    client = AliyunEsaClient("id", "secret", sdk_client=sdk_client)
    return client, sdk_client


def test_add_txt_record_creates_txt_record_for_best_matching_site(monkeypatch):
    client, sdk_client = make_client(monkeypatch)

    client.add_txt_record("foo.bar.example.com", "_acme-challenge.foo.bar.example.com", "value")

    request = sdk_client.created[0]
    assert request.type == "TXT"
    assert request.record_name == "_acme-challenge.foo.bar.example.com"
    assert request.ttl == 1
    assert request.data.value == "value"
    assert request.site_id == 2


def test_add_txt_record_retries_retryable_create_record_errors(monkeypatch):
    client, sdk_client = make_client(monkeypatch)
    monkeypatch.setattr(aliyun_esa, "sleep", lambda seconds: None)
    sdk_client.create_record_errors = [FakeAliyunError("Site.ServiceBusy")]

    client.add_txt_record("example.com", "_acme-challenge.example.com", "value")

    assert len(sdk_client.created) == 2


def test_add_txt_record_does_not_retry_non_retryable_create_record_errors(monkeypatch):
    client, sdk_client = make_client(monkeypatch)
    sdk_client.create_record_errors = [FakeAliyunError("InvalidParameter")]

    try:
        client.add_txt_record("example.com", "_acme-challenge.example.com", "value")
        assert False
    except errors.PluginError:
        pass

    assert len(sdk_client.created) == 1


def test_delete_txt_record_matches_record_name_type_and_value(monkeypatch):
    client, sdk_client = make_client(monkeypatch)
    sdk_client.records = [
        SimpleNamespace(
            record_id=10,
            record_name="_acme-challenge.example.com",
            record_type="TXT",
            data=SimpleNamespace(value="other-value"),
        ),
        SimpleNamespace(
            record_id=11,
            record_name="_acme-challenge.example.com",
            record_type="TXT",
            data=SimpleNamespace(value="expected-value"),
        ),
    ]

    client.del_txt_record("example.com", "_acme-challenge.example.com", "expected-value")

    assert sdk_client.list_records_requests[0].record_match_type == "exact"
    assert sdk_client.list_records_requests[0].record_name == "_acme-challenge.example.com"
    assert sdk_client.list_records_requests[0].site_id == 1
    assert sdk_client.list_records_requests[0].type == "TXT"
    assert sdk_client.deleted[0].record_id == 11


def test_delete_txt_record_ignores_missing_record(monkeypatch):
    client, sdk_client = make_client(monkeypatch)

    client.del_txt_record("example.com", "_acme-challenge.example.com", "missing")

    assert sdk_client.deleted == []
