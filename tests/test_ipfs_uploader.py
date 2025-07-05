import pytest
import requests
import json
from unittest.mock import MagicMock
from ipfsUploader import upload_to_ipfs

def test_upload_success(mocker):
    """
    Why: Verifies the happy path for IPFS uploads.
    How: Mocks requests.post to simulate a successful API response from Pinata.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"IpfsHash": "QmTestCID"}
    mocker.patch('requests.post', return_value=mock_response)

    # Act
    result_uri = upload_to_ipfs("./sample_rfd.json")

    # Assert
    assert result_uri == "ipfs://QmTestCID"

def test_upload_failure(mocker):
    """
    Why: Ensures errors from Pinata are handled gracefully.
    How: Mocks requests.post to simulate an API error.
    """
    mock_response = MagicMock()
    mock_response.status_code = 401  # Unauthorized
    mock_response.text = "Invalid API Key"

    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
    
    mocker.patch('requests.post', return_value=mock_response)


    expected_error_msg = f"Failed to upload to IPFS: 401 - Invalid API Key"
    with pytest.raises(Exception, match=expected_error_msg):
        upload_to_ipfs("./sample_rfd.json")