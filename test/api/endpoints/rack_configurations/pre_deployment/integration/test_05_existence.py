from typing import Any, Dict

from test_fixtures.integration import (
    assert_api_gateway_exists,
    create_www_common_s3_existence_tests,
)


class TestAPIBackendPrerequisites:
    def test_api_common_routing_outputs_provides_gateway_id(
        self,
        api_common_routing_outputs: Dict[str, str]
    ) -> None:
        assert api_common_routing_outputs.get("api_gateway_id"), (
            "api_gateway_id output not found in api_common_routing. "
            "Run terraform apply in src/api/common/routing/"
        )

    def test_api_gateway_rest_api_exists(self, api_gateway_info: Dict[str, Any]) -> None:
        assert_api_gateway_exists(api_gateway_info)
        assert True


TestWWWSharedPrerequisites = create_www_common_s3_existence_tests()
