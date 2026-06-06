"""Aliyun ESA DNS Authenticator plugin."""

from certbot.plugins import dns_common

from certbot_dns_aliyun_esa._internal.aliyun_esa import AliyunEsaClient


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for Aliyun ESA."""

    description = "Obtain certificates using a DNS TXT record in Aliyun ESA."

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super().add_parser_arguments(add, default_propagation_seconds=60)
        add("credentials", help="Aliyun ESA credentials INI file.")
        add("region-id", default="cn-hangzhou", help="Aliyun ESA region ID.")
        add("endpoint", default="esa.cn-hangzhou.aliyuncs.com", help="Aliyun ESA API endpoint.")
        add("ttl", default=1, type=int, help="TTL for created TXT records. Use 1 for ESA default TTL.")

    def more_info(self):
        return "This plugin configures DNS TXT records using the Aliyun ESA API."

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "Aliyun ESA credentials INI file",
            {
                "access-key-id": "AccessKey ID for Aliyun ESA API",
                "access-key-secret": "AccessKey secret for Aliyun ESA API",
            },
        )

    def _perform(self, domain, validation_name, validation):
        self._get_client().add_txt_record(domain, validation_name, validation)

    def _cleanup(self, domain, validation_name, validation):
        self._get_client().del_txt_record(domain, validation_name, validation)

    def _get_client(self):
        if not hasattr(self, "_client"):
            self._client = AliyunEsaClient(
                access_key_id=self.credentials.conf("access-key-id"),
                access_key_secret=self.credentials.conf("access-key-secret"),
                region_id=self.conf("region-id"),
                endpoint=self.conf("endpoint"),
                ttl=self.conf("ttl"),
            )
        return self._client
