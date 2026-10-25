// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// @notice SPV-equity share token with an issuer-governed transfer restriction.
/// It is NOT title to property. A CRE workflow reports ACRIS document sets;
/// adverse filings restrict transfers until the issuer multisig clears.
contract LiensightToken is ERC20 {
    error TransferRestricted();
    error NotReceiver();
    error NotIssuer();

    event Restricted(bytes32 docSetHash, bytes32[] docIds);
    event Cleared(string reason);
    event ClearSuggested(bytes32[] dischargeDocIds);

    address public immutable issuerMultisig;
    address public immutable reportReceiver;
    bytes32 public immutable codeMapHash;

    bool public restricted;
    bytes32 public lastDocSetHash;
    bytes32[] public citedDocIds;

    constructor(string memory name_, string memory symbol_, address issuerMultisig_, address reportReceiver_, bytes32 codeMapHash_)
        ERC20(name_, symbol_)
    {
        issuerMultisig = issuerMultisig_;
        reportReceiver = reportReceiver_;
        codeMapHash = codeMapHash_;
        _mint(issuerMultisig_, 1_000_000 ether);
    }

    function onReport(bytes32, bytes32 docSetHash, bytes32[] calldata newAdverseDocIds, bytes32[] calldata dischargeDocIds)
        external
    {
        if (msg.sender != reportReceiver) revert NotReceiver();
        if (docSetHash == lastDocSetHash) return;
        lastDocSetHash = docSetHash;
        if (newAdverseDocIds.length > 0) {
            restricted = true;
            citedDocIds = newAdverseDocIds;
            emit Restricted(docSetHash, newAdverseDocIds);
        }
        if (dischargeDocIds.length > 0) emit ClearSuggested(dischargeDocIds);
    }

    function clearRestriction(string calldata reason) external {
        if (msg.sender != issuerMultisig) revert NotIssuer();
        restricted = false;
        delete citedDocIds;
        emit Cleared(reason);
    }

    function _update(address from, address to, uint256 value) internal override {
        if (restricted && from != address(0)) revert TransferRestricted();
        super._update(from, to, value);
    }
}
