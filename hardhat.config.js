import "@nomicfoundation/hardhat-toolbox";
import "dotenv/config"; // This is the ESM way to load .env

/** @type import('hardhat/config').HardhatUserConfig */
export default {
  solidity: "0.8.20",
  networks: {
    hardhat: {
      forking: {
        url: "https://eth-mainnet.g.alchemy.com/v2/uX9mDI_nyR4uPvXLHOyhU",
      },
    },
    ganache: {
      url: process.env.WEB3_PROVIDER_URI || "http://127.0.0.1:7545",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 5777,
    },
  },
};
