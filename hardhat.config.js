require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.20",
  networks: {
    // We add a 'ganache' network block here
    ganache: {
      url: process.env.WEB3_PROVIDER_URI, // http://127.0.0.1:7545
      accounts: [process.env.PRIVATE_KEY],
      chainId: 5777, // IMPORTANT: Ganache default chain ID
    },
  },
};
