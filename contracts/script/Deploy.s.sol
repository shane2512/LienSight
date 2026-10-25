// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {LiensightToken} from "../src/LiensightToken.sol";

/// Env (no keys here): FORWARDER, WORKFLOW_OWNER, CODEMAP_HASH. The deployer becomes the issuer.
/// Sign with a keystore: forge script ... --account <name> --broadcast
contract Deploy is Script {
    function run() external {
        address forwarder = vm.envAddress("FORWARDER");
        address wfOwner = vm.envAddress("WORKFLOW_OWNER");
        bytes32 codeMapHash = vm.envBytes32("CODEMAP_HASH");
        bytes32 key = keccak256(bytes("BBL:2-5789-1022")); // must match workflow/config bbl
        vm.startBroadcast();
        LiensightToken t = new LiensightToken("Liensight SPV", "LSPV", msg.sender, forwarder, codeMapHash, wfOwner, key);
        vm.stopBroadcast();
        console.log("LiensightToken:", address(t));
    }
}
