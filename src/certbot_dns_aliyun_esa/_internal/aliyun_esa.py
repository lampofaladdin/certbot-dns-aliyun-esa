"""Aliyun ESA DNS API client."""

import logging
from dataclasses import dataclass
from time import sleep
from typing import Any
from typing import Optional

from certbot import errors

try:
    from alibabacloud_esa20240910.client import Client as EsaSdkClient
    from alibabacloud_esa20240910 import models as esa_models
    from alibabacloud_tea_openapi import models as open_api_models
except ImportError:  # pragma: no cover
    EsaSdkClient = None  # type: ignore[assignment]
    esa_models = None  # type: ignore[assignment]
    open_api_models = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_RETRYABLE_CREATE_RECORD_CODES = {"Site.ServiceBusy", "TooManyRequests"}
_CREATE_RECORD_RETRY_SECONDS = 5
_CREATE_RECORD_RETRY_ATTEMPTS = 10


@dataclass(frozen=True)
class _Site:
    site_id: int
    site_name: str


class AliyunEsaClient:
    """Client that creates and deletes DNS TXT records in Aliyun ESA."""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        region_id: str = "cn-hangzhou",
        endpoint: str = "esa.cn-hangzhou.aliyuncs.com",
        ttl: int = 1,
        sdk_client: Optional[Any] = None,
    ) -> None:
        self.ttl = ttl
        self._sites: Optional[list[_Site]] = None
        self._client = sdk_client or self._build_client(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region_id,
            endpoint=endpoint,
        )

    def add_txt_record(self, domain: str, record_name: str, record_content: str) -> None:
        site = self._find_site(domain)
        request = esa_models.CreateRecordRequest(
            type="TXT",
            record_name=record_name.rstrip("."),
            ttl=self.ttl,
            comment="Created by certbot-dns-aliyun-esa",
            data=esa_models.CreateRecordRequestData(value=record_content),
            site_id=site.site_id,
        )

        try:
            self._create_record_with_retry(request)
        except Exception as error:  # pylint: disable=broad-except
            logger.debug("Encountered error adding TXT record", exc_info=True)
            raise errors.PluginError(
                "Error adding TXT record {0} for {1}: {2}".format(record_name, domain, error)
            ) from error

    def del_txt_record(self, domain: str, record_name: str, record_content: str) -> None:
        try:
            site = self._find_site(domain)
            record = self._find_txt_record(site.site_id, record_name, record_content)
        except errors.PluginError as error:
            logger.debug("Encountered error finding TXT record during deletion: %s", error)
            return

        if record is None:
            logger.debug("TXT record %s with expected value was not found", record_name)
            return

        try:
            self._client.delete_record(
                esa_models.DeleteRecordRequest(record_id=self._get_attr(record, "record_id"))
            )
        except Exception as error:  # pylint: disable=broad-except
            logger.debug("Encountered error deleting TXT record", exc_info=True)

    def _build_client(
        self, access_key_id: str, access_key_secret: str, region_id: str, endpoint: str
    ) -> Any:
        if EsaSdkClient is None or open_api_models is None:
            raise errors.PluginError(
                "Aliyun ESA SDK is not installed. Please install alibabacloud-esa20240910."
            )

        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region_id,
            endpoint=endpoint,
        )
        return EsaSdkClient(config)

    def _create_record_with_retry(self, request: Any) -> Any:
        for attempt in range(1, _CREATE_RECORD_RETRY_ATTEMPTS + 1):
            try:
                return self._client.create_record(request)
            except Exception as error:  # pylint: disable=broad-except
                if attempt == _CREATE_RECORD_RETRY_ATTEMPTS or not self._is_retryable_error(error):
                    raise
                logger.debug(
                    "Retrying CreateRecord after %s: attempt %d/%d",
                    self._get_error_code(error),
                    attempt,
                    _CREATE_RECORD_RETRY_ATTEMPTS,
                )
                sleep(_CREATE_RECORD_RETRY_SECONDS)

        return None

    def _find_site(self, domain: str) -> _Site:
        normalized_domain = domain.lstrip("*.").rstrip(".")
        candidates = self._base_domain_name_guesses(normalized_domain)
        sites = self._list_sites()

        for candidate in candidates:
            for site in sites:
                if site.site_name == candidate:
                    return site

        raise errors.PluginError(
            "Unable to determine Aliyun ESA site for {0}; tried: {1}".format(
                domain, ", ".join(candidates)
            )
        )

    def _list_sites(self) -> list[_Site]:
        if self._sites is not None:
            return self._sites

        sites: list[_Site] = []
        page_number = 1

        try:
            while True:
                response = self._client.list_sites(
                    esa_models.ListSitesRequest(page_number=page_number, page_size=500)
                )
                body = self._get_attr(response, "body")
                for site in self._get_attr(body, "sites") or []:
                    site_id = self._get_attr(site, "site_id")
                    site_name = self._get_attr(site, "site_name")
                    if site_id is not None and site_name:
                        sites.append(_Site(site_id=int(site_id), site_name=str(site_name).rstrip(".")))

                page_size = self._get_attr(body, "page_size") or 500
                total_count = self._get_attr(body, "total_count") or len(sites)
                if page_number * page_size >= total_count:
                    break
                page_number += 1
        except Exception as error:  # pylint: disable=broad-except
            logger.debug("Encountered error listing Aliyun ESA sites", exc_info=True)
            raise errors.PluginError("Error listing Aliyun ESA sites: {0}".format(error)) from error

        self._sites = sites
        return sites

    def _find_txt_record(self, site_id: int, record_name: str, record_content: str) -> Optional[Any]:
        page_number = 1
        normalized_record_name = record_name.rstrip(".")

        while True:
            response = self._client.list_records(
                esa_models.ListRecordsRequest(
                    page_number=page_number,
                    page_size=500,
                    record_match_type="exact",
                    record_name=normalized_record_name,
                    site_id=site_id,
                    type="TXT",
                )
            )
            body = self._get_attr(response, "body")
            for record in self._get_attr(body, "records") or []:
                if self._record_matches(record, normalized_record_name, record_content):
                    return record

            page_size = self._get_attr(body, "page_size") or 500
            total_count = self._get_attr(body, "total_count") or 0
            if page_number * page_size >= total_count:
                return None
            page_number += 1

    def _record_matches(self, record: Any, record_name: str, record_content: str) -> bool:
        data = self._get_attr(record, "data")
        return (
            self._get_attr(record, "record_name") == record_name
            and self._get_attr(record, "record_type") == "TXT"
            and self._get_attr(data, "value") == record_content
        )

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        return AliyunEsaClient._get_error_code(error) in _RETRYABLE_CREATE_RECORD_CODES

    @staticmethod
    def _get_error_code(error: Exception) -> Optional[str]:
        code = getattr(error, "code", None)
        if code:
            return str(code)

        data = getattr(error, "data", None)
        if isinstance(data, dict) and data.get("Code"):
            return str(data["Code"])

        return None

    @staticmethod
    def _base_domain_name_guesses(domain: str) -> list[str]:
        labels = domain.split(".")
        return [".".join(labels[i:]) for i in range(0, len(labels) - 1)]

    @staticmethod
    def _get_attr(obj: Any, name: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(name)
        return getattr(obj, name, None)
