// onchain/test/gauge.js
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RewardGauge – debug run", function () {
  it("stores the new score and mints 1 xREP", async function () {
    const [provider] = await ethers.getSigners();
    console.log("Provider :", provider.address);

    /* deploy token */
    const Token = await ethers.getContractFactory("RewardToken");
    const token = await Token.deploy();
    await token.deployed();
    console.log("Token    :", token.address);

    /* deploy gauge */
    const Gauge = await ethers.getContractFactory("RewardGauge");
    const gauge = await Gauge.deploy(token.address);
    await gauge.deployed();
    console.log("Gauge    :", gauge.address);

    /* build + sign repHash */
    const scoreBps = 7500;
    const epoch    = 0n;                         // deterministic
    const repHash  = ethers.utils.solidityKeccak256(
      ["address","uint16","uint64"],
      [provider.address, scoreBps, epoch]
    );
    const sig = await provider.signMessage(ethers.utils.arrayify(repHash));

    /* call */
    const tx = await gauge.submitScore(repHash, scoreBps, sig);
    await tx.wait();

    /* read state */
    const stored = await gauge.lastScore(provider.address);
    const bal    = await token.balanceOf(provider.address);

    console.log("storedScore:", stored.toString());
    console.log("balance    :", bal.toString());

    /* assertions */
    expect(Number(stored)).to.equal(scoreBps);  // Convert BigInt/BigNumber to number
    expect(bal.toString()).to.equal(ethers.utils.parseEther("1").toString());  // Compare string values
  });
});