# tests/test_nft_authorizer.py
import pytest
from unittest.mock import MagicMock
from nftAuthorizer import NFTAuthorizer

@pytest.fixture
def mock_web3(mocker):
    # This fixture creates a complex mock for the web3 library
    mock_w3_instance = MagicMock()
    mock_w3_instance.is_connected.return_value = True
    
    mock_contract_instance = MagicMock()
    # Mock the chain of calls: .functions.balanceOf(address).call()
    mock_w3_instance.eth.contract.return_value = mock_contract_instance
    
    mocker.patch('nftAuthorizer.Web3', return_value=mock_w3_instance)
    return mock_w3_instance

def test_has_nft_true(mock_web3, mocker):
    """
    Why: Verifies that a wallet with an NFT is correctly identified.
    How: Mocks the contract call to return a balance > 0.
    """
    # Arrange
    # Configure the final call in the chain to return 1
    mock_web3.eth.contract.return_value.functions.balanceOf().call.return_value = 1
    authorizer = NFTAuthorizer() # This will now use our mock_web3
    
    # Act
    has_nft = authorizer.has_nft("0xWalletWithNFT")
    
    # Assert
    assert has_nft is True

def test_has_nft_false(mock_web3, mocker):
    """
    Why: Verifies that a wallet without an NFT is correctly identified.
    How: Mocks the contract call to return a balance of 0.
    """
    # Arrange
    mock_web3.eth.contract.return_value.functions.balanceOf().call.return_value = 0
    authorizer = NFTAuthorizer()
    
    # Act
    has_nft = authorizer.has_nft("0xWalletWithoutNFT")
    
    # Assert
    assert has_nft is False