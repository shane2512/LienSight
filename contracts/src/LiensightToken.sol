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
    error BadMetadata();
    error WrongWorkflowOwner();
    error WrongProperty();
    error ReviewMismatch();

    event Restricted(bytes32 docSetHash, bytes32[] docIds);
    event Cleared(string reason);
    event ClearSuggested(bytes32[] dischargeDocIds);

    address public immutable issuerMultisig;
    address public immutable reportReceiver;
    bytes32 public immutable codeMapHash;
    /// Only reports from workflows owned by this address are accepted (the forwarder is shared by all workflows).
    address public expectedWorkflowOwner;
    bytes32 public immutable propertyKey;

    bool public restricted;
    bytes32 public lastDocSetHash;
    /// keccak256(abi.encode(bytes32[])) of the liens cited by the current restriction. Full list is in the Restricted event.
    bytes32 public citedHash;
    /// Adverse docs already reported once. A cleared lien never re-restricts.
    mapping(bytes32 => bool) public seenAdverse;

    constructor(string memory name_, string memory symbol_, address issuerMultisig_, address reportReceiver_, bytes32 codeMapHash_, address expectedWorkflowOwner_, bytes32 propertyKey_)
        ERC20(name_, symbol_)
    {
        issuerMultisig = issuerMultisig_;
        reportReceiver = reportReceiver_;
        codeMapHash = codeMapHash_;
        expectedWorkflowOwner = expectedWorkflowOwner_;
        propertyKey = propertyKey_;
        _mint(issuerMultisig_, 1_000_000 ether);
    }

    /// IReceiver: called by the CRE forwarder with (metadata, abi-encoded report).
    function onReport(bytes calldata metadata, bytes calldata report) external {
        if (msg.sender != reportReceiver) revert NotReceiver();
        // forwarder metadata (packed): workflowId(32) | workflowName(10) | workflowOwner(20)
        if (metadata.length < 62) revert BadMetadata();
        if (address(bytes20(metadata[42:62])) != expectedWorkflowOwner) revert WrongWorkflowOwner();
        (bytes32 key, bytes32 docSetHash, bytes32[] memory adverse, bytes32[] memory discharge) =
            abi.decode(report, (bytes32, bytes32, bytes32[], bytes32[]));
        if (key != propertyKey) revert WrongProperty();
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
            citedHash = keccak256(abi.encode(cited));
            emit Restricted(docSetHash, cited);
        }
        if (discharge.length > 0) emit ClearSuggested(discharge);
    }

    function supportsInterface(bytes4 id) external pure returns (bool) {
        return id == 0x805f2132 || id == 0x01ffc9a7;
    }

    /// Issuer may rotate the accepted workflow owner (e.g. simulator -> deployed CRE workflow).
    function setExpectedWorkflowOwner(address newOwner) external {
        if (msg.sender != issuerMultisig) revert NotIssuer();
        expectedWorkflowOwner = newOwner;
    }

    /// @param reviewedCitedHash the citedHash the multisig reviewed; reverts if new liens landed since.
    function clearRestriction(bytes32 reviewedCitedHash, string calldata reason) external {
        if (msg.sender != issuerMultisig) revert NotIssuer();
        if (reviewedCitedHash != citedHash) revert ReviewMismatch();
        restricted = false;
        citedHash = bytes32(0);
        emit Cleared(reason);
    }

    function _update(address from, address to, uint256 value) internal override {
        if (restricted && from != address(0)) revert TransferRestricted();
        super._update(from, to, value);
    }
}
