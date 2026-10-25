// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {LiensightToken} from "../src/LiensightToken.sol";

contract LiensightTokenTest is Test {
    LiensightToken token;
    address issuer = address(0x15);
    address receiver = address(0xCE); // stands in for the CRE KeystoneForwarder
    address alice = address(0xA11CE);
    address owner = address(0xB0B);
    bytes32 constant KEY = keccak256("BBL:2-05789-1022");
    bytes32 constant CODEMAP = keccak256("codemap-v1");

    function setUp() public {
        token = new LiensightToken("Liensight SPV", "LSPV", issuer, receiver, CODEMAP, owner, KEY);
    }

    function _one(bytes32 a) internal pure returns (bytes32[] memory arr) {
        arr = new bytes32[](1);
        arr[0] = a;
    }

    function _none() internal pure returns (bytes32[] memory) {
        return new bytes32[](0);
    }

    function _meta(address wfOwner) internal pure returns (bytes memory) {
        return abi.encodePacked(bytes32(uint256(1)), bytes10("liensight"), wfOwner);
    }

    function _send(bytes32 setHash, bytes32[] memory adverse, bytes32[] memory discharge) internal {
        vm.prank(receiver);
        token.onReport(_meta(owner), abi.encode(KEY, setHash, adverse, discharge));
    }

    function _clear(string memory why) internal {
        bytes32 h = token.citedHash();
        vm.prank(issuer);
        token.clearRestriction(h, why);
    }

    function _restrict() internal {
        _send(keccak256("set1"), _one(keccak256("doc-LOCC-1")), _none());
    }

    function test_transferWorksWhenUnrestricted() public {
        vm.prank(issuer);
        token.transfer(alice, 10);
        assertEq(token.balanceOf(alice), 10);
    }

    function test_onReportWithAdverseDocRestrictsTransfers() public {
        _restrict();
        assertTrue(token.restricted());
        assertEq(token.citedHash(), keccak256(abi.encode(_one(keccak256("doc-LOCC-1")))));
        vm.prank(issuer);
        vm.expectRevert(LiensightToken.TransferRestricted.selector);
        token.transfer(alice, 10);
    }

    function test_onReportFromNonReceiverReverts() public {
        vm.prank(alice);
        vm.expectRevert(LiensightToken.NotReceiver.selector);
        token.onReport(_meta(owner), abi.encode(KEY, keccak256("set1"), _one(keccak256("d")), _none()));
    }

    function test_onlyIssuerCanClear() public {
        _restrict();
        bytes32 h = token.citedHash();
        vm.prank(alice);
        vm.expectRevert(LiensightToken.NotIssuer.selector);
        token.clearRestriction(h, "nope");
    }

    function test_clearReenablesTransfers() public {
        _restrict();
        _clear("reviewed");
        assertFalse(token.restricted());
        vm.prank(issuer);
        token.transfer(alice, 10);
        assertEq(token.balanceOf(alice), 10);
    }

    function test_dischargeEmitsClearSuggestedButStaysRestricted() public {
        _restrict();
        vm.expectEmit(false, false, false, true);
        emit LiensightToken.ClearSuggested(_one(keccak256("doc-RFL-1")));
        _send(keccak256("set2"), _none(), _one(keccak256("doc-RFL-1")));
        assertTrue(token.restricted());
    }

    function test_unchangedDocSetHashIsNoOp() public {
        _restrict();
        _clear("reviewed");
        _send(keccak256("set1"), _one(keccak256("doc-LOCC-1")), _none());
        assertFalse(token.restricted());
    }

    function test_emptyAdverseListNeverRestricts() public {
        _send(keccak256("set0"), _none(), _none());
        assertFalse(token.restricted());
        assertEq(token.lastDocSetHash(), keccak256("set0"));
    }

    function test_clearedLienDoesNotRestrictAgainOnUnrelatedFiling() public {
        _restrict();
        _clear("reviewed");
        // a new, unrelated filing changes the set; the same old lien is still listed as adverse
        _send(keccak256("set2"), _one(keccak256("doc-LOCC-1")), _none());
        assertFalse(token.restricted());
    }

    function test_newLienAfterClearRestrictsAgain() public {
        _restrict();
        _clear("reviewed");
        bytes32[] memory both = new bytes32[](2);
        both[0] = keccak256("doc-LOCC-1");
        both[1] = keccak256("doc-FL-2");
        _send(keccak256("set3"), both, _none());
        assertTrue(token.restricted());
        assertEq(token.citedHash(), keccak256(abi.encode(_one(keccak256("doc-FL-2")))));
    }

    function test_supportsReceiverInterface() public {
        assertTrue(token.supportsInterface(0x805f2132)); // IReceiver.onReport(bytes,bytes)
        assertTrue(token.supportsInterface(0x01ffc9a7)); // ERC165
    }

    function test_reportFromWrongWorkflowOwnerReverts() public {
        vm.prank(receiver);
        vm.expectRevert(LiensightToken.WrongWorkflowOwner.selector);
        token.onReport(_meta(alice), abi.encode(KEY, keccak256("s"), _one(keccak256("d")), _none()));
    }

    function test_shortMetadataReverts() public {
        vm.prank(receiver);
        vm.expectRevert(LiensightToken.BadMetadata.selector);
        token.onReport("", abi.encode(KEY, keccak256("s"), _one(keccak256("d")), _none()));
    }

    function test_reportForWrongPropertyReverts() public {
        vm.prank(receiver);
        vm.expectRevert(LiensightToken.WrongProperty.selector);
        token.onReport(_meta(owner), abi.encode(keccak256("other"), keccak256("s"), _one(keccak256("d")), _none()));
    }

    function test_clearWithStaleReviewedHashReverts() public {
        _restrict();
        bytes32 reviewed = token.citedHash();
        // lien B lands before the multisig's clear executes
        _send(keccak256("set2"), _one(keccak256("doc-FL-9")), _none());
        vm.prank(issuer);
        vm.expectRevert(LiensightToken.ReviewMismatch.selector);
        token.clearRestriction(reviewed, "reviewed only lien A");
        assertTrue(token.restricted());
    }

    function test_manyNewAdverseDocsFitInGasBudget() public {
        bytes32[] memory many = new bytes32[](20);
        for (uint256 i; i < 20; i++) many[i] = keccak256(abi.encode("doc", i));
        uint256 g = gasleft();
        _send(keccak256("big"), many, _none());
        assertLt(g - gasleft(), 1_500_000);
        assertTrue(token.restricted());
    }

    function test_issuerCanRotateExpectedWorkflowOwner() public {
        vm.prank(issuer);
        token.setExpectedWorkflowOwner(alice);
        vm.prank(receiver);
        token.onReport(_meta(alice), abi.encode(KEY, keccak256("s"), _one(keccak256("d")), _none()));
        assertTrue(token.restricted());
        // old owner is now rejected
        vm.prank(receiver);
        vm.expectRevert(LiensightToken.WrongWorkflowOwner.selector);
        token.onReport(_meta(owner), abi.encode(KEY, keccak256("s2"), _one(keccak256("d2")), _none()));
    }

    function test_nonIssuerCannotRotateWorkflowOwner() public {
        vm.prank(alice);
        vm.expectRevert(LiensightToken.NotIssuer.selector);
        token.setExpectedWorkflowOwner(alice);
    }
}
