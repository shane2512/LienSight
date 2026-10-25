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
    /// Adverse docs already reported once. A cleared lien never re-restricts.
    mapping(bytes32 => bool) public seenAdverse;

    constructor(string memory name_, string memory symbol_, address issuerMultisig_, address reportReceiver_, bytes32 codeMapHash_)
        ERC20(name_, symbol_)
    {
        issuerMultisig = issuerMultisig_;
        reportReceiver = reportReceiver_;
        codeMapHash = codeMapHash_;
        _mint(issuerMultisig_, 1_000_000 ether);
    }

    /// IReceiver: called by the CRE forwarder with (metadata, abi-encoded report).
    function onReport(bytes calldata, bytes calldata report) external {
        if (msg.sender != reportReceiver) revert NotReceiver();
        (, bytes32 docSetHash, bytes32[] memory adverse, bytes32[] memory discharge) =
            abi.decode(report, (bytes32, bytes32, bytes32[], bytes32[]));
        if (docSetHash == lastDocSetHash) return;
        lastDocSetHash = docSetHash;

        uint256 n;
        bytes32[] memory fresh = new bytes32[](adverse.length);
        for (uint256 i; i < adverse.length; i++) {
            if (!seenAdverse[adverse[i]]) {
                seenAdverse[adverse[i]] = true;
                fresh[n++] = adverse[i];
            }
        }
        if (n > 0) {
            bytes32[] memory cited = new bytes32[](n);
            for (uint256 i; i < n; i++) cited[i] = fresh[i];
            restricted = true;
            citedDocIds = cited;
            emit Restricted(docSetHash, cited);
        }
        if (discharge.length > 0) emit ClearSuggested(discharge);
    }

    function supportsInterface(bytes4 id) external pure returns (bool) {
        return id == 0x805f2132 || id == 0x01ffc9a7;
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
