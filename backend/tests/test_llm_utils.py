import unittest
from unittest.mock import patch, MagicMock
from app.core.llm_utils import call_llm, LLMError

class TestLLMUtils(unittest.TestCase):

    @patch('app.core.llm_utils.httpx.Client')
    def test_call_llm_proxy_success(self, mock_client_cls):
        # Scenario 1: Proxy (trust_env=True) succeeds immediately
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Success via proxy"}}]
        }
        mock_client.post.return_value = mock_response

        # Call
        result = call_llm("test prompt", summary_mode="online")
        
        # Verify
        self.assertEqual(result, "Success via proxy")
        # Ensure it was called with trust_env=True
        mock_client_cls.assert_called_once()
        self.assertTrue(mock_client_cls.call_args[1].get('trust_env'))

    @patch('app.core.llm_utils.doh_dns_bypass')
    @patch('app.core.llm_utils.httpx.Client')
    def test_call_llm_proxy_fail_doh_success(self, mock_client_cls, mock_doh):
        # Scenario 2: Proxy fails, fallback to DoH succeeds
        
        # We need httpx.Client to behave differently on 1st vs 2nd call
        # 1st call (proxy): raise Exception
        # 2nd call (DoH): succeed
        
        mock_client_1 = MagicMock()
        mock_client_1.post.side_effect = Exception("Proxy Blocked")
        
        mock_client_2 = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Success via DoH"}}]
        }
        mock_client_2.post.return_value = mock_response

        # Context manager returns
        mock_client_cls.return_value.__enter__.side_effect = [mock_client_1, mock_client_2]

        result = call_llm("test prompt", summary_mode="online")
        
        self.assertEqual(result, "Success via DoH")
        self.assertEqual(mock_client_cls.call_count, 2)
        
        # Check that the first call was trust_env=True, second was trust_env=False
        self.assertTrue(mock_client_cls.call_args_list[0][1].get('trust_env'))
        self.assertFalse(mock_client_cls.call_args_list[1][1].get('trust_env'))
        
        # Verify DoH bypass was invoked
        mock_doh.assert_called_once()

    @patch('app.core.llm_utils.httpx.Client')
    def test_call_llm_total_failure(self, mock_client_cls):
        # Scenario 3: Total network failure (both proxy and DoH fail)
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("Connection Timeout")
        mock_client_cls.return_value.__enter__.return_value = mock_client
        
        with self.assertRaises(LLMError) as ctx:
            call_llm("test prompt", summary_mode="online")
            
        self.assertIn("Connection Timeout", str(ctx.exception))
        # Internal client calls: 1 for proxy + 1 for direct (DoH bypass uses separate network.httpx)
        self.assertGreaterEqual(mock_client_cls.call_count, 2)

if __name__ == '__main__':
    unittest.main()
