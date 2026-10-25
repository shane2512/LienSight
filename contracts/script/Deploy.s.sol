// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {LiensightToken} from "../src/LiensightToken.sol";

/// Env (no keys here): FORWARDER, WORKFLOW_OWNER, CODEMAP_HASH, ISSUER (receives supply, can clear).
/// Note: msg.sender in a script is Foundry's default sender, NOT the broadcaster, so ISSUER is explicit.
/// Sign with a keystore: forge script ... --account <name> --broadcast
contract Deploy is Script {
    function run() external {
        address forwarder = vm.envAddress("FORWARDER");
        address wfOwner = vm.envAddress("WORKFLOW_OWNER");
        bytes32 codeMapHash = vm.envBytes32("CODEMAP_HASH");
        address issuer = vm.envAddress("ISSUER");
        bytes32 key = keccak256(bytes("BBL:2-5789-1022")); // must match workflow/config bbl
        vm.startBroadcast();
        LiensightToken t = new LiensightToken("Liensight SPV", "LSPV", issuer, forwarder, codeMapHash, wfOwner, key);
        vm.stopBroadcast();
        console.log("LiensightToken:", address(t));
    }
}
