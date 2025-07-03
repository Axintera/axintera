// hardhat.config.js

require("@nomicfoundation/hardhat-toolbox-viem");
require("@nomicfoundation/hardhat-ignition");
require("dotenv").config();

module.exports = {
  solidity: "0.8.28",
  networks: {
    flow: {
      url: "https://mainnet.evm.nodes.onflow.org",
      accounts: [process.env.DEPLOY_WALLET_1],
    },
    flowTestnet: {
      url: "https://testnet.evm.nodes.onflow.org",
      accounts: [process.env.DEPLOY_WALLET_1],
    },
  },
  etherscan: {
    apiKey: {
      // Blockscout (FlowScan) doesn’t require a real key
      flow: "abc",
      flowTestnet: "abc",
    },
    customChains: [
      {
        network: "flow",
        chainId: 747,
        urls: {
          apiURL: "https://evm.flowscan.io/api",
          browserURL: "https://evm.flowscan.io/",
        },
      },
      {
        network: "flowTestnet",
        chainId: 545,
        urls: {
          apiURL: "https://evm-testnet.flowscan.io/api",
          browserURL: "https://evm-testnet.flowscan.io/",
        },
      },
    ],
  },
  // (optional) you can configure ignition here, but by default it
  // will pick up any modules in ./ignition/
  ignition: { },
};
