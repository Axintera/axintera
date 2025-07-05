const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

/**
 * This is an Ignition module for deploying the FlowYieldGate contract.
 * @param {ModuleBuilder} m - The module builder object provided by Hardhat Ignition.
 */
module.exports = buildModule("FlowYieldGateModule", (m) => {
  // This line defines a deployment task for your contract.
  // The string "FlowYieldGate" MUST exactly match the name of your contract
  // as it is written in the FlowYieldGate.sol file.
  const flowYieldGate = m.contract("FlowYieldGate");

  // The module returns an object with the deployed contract instance.
  // This allows other modules to depend on it in the future.
  return { flowYieldGate };
});