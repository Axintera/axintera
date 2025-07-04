// ignition/RewardGaugeModule.js

const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

// you can parameterize things via CLI:
//   npx hardhat ignition --network flowTestnet --param rewardToken=0xABC...
module.exports = buildModule("RewardGaugeModule", (m) => {
  // fetch a constructor param or fall back to this default
  const rewardToken = m.getParameter(
    "rewardToken",
    "0x5FbDB2315678afecb367f032d93F642f64180aa3" // your test‐token address
  );

  // deploy the proxy (or regular) contract
  const gauge = m.contract("RewardGauge", [rewardToken], {
    // if you want to send ETH/wei on creation:
    // value: m.getParameter("fundingAmount", 1_000_000_000_000_000_000n)
  });

  return { gauge };
});
