// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {LiensightToken} from "../src/LiensightToken.sol";

contract LiensightTokenTest is Test {
    LiensightToken token;
    address issuer = address(0x15);
    address receiver = address(0xCE); // stands in for the CRE KeystoneForwarder
    address alice = address(0xA11CE);
    bytes32 constant KEY = keccak256("BBL:2-05789-1022");
    bytes32 constant CODEMAP = keccak256("codemap-v1");

    function setUp() public {
        token = new LiensightToken("Liensight SPV", "LSPV", issuer, receiver, CODEMAP);
    }

    function _one(bytes32 a) internal pure returns (bytes32[] memory arr) {
        arr = new bytes32[](1);
        arr[0] = a;
    }

    function _none() internal pure returns (bytes32[] memory) {
        return new bytes32[](0);
    }

    function _send(bytes32 setHash, bytes32[] memory adverse, bytes32[] memory discharge) internal {
        vm.prank(receiver);
        token.onReport("", abi.encode(KEY, setHash, adverse, discharge));
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
        assertEq(token.citedDocIds(0), keccak256("doc-LOCC-1"));
        vm.prank(issuer);
        vm.expectRevert(LiensightToken.TransferRestricted.selector);
        token.transfer(alice, 10);
    }

    function test_onReportFromNonReceiverReverts() public {
        vm.prank(alice);
        vm.expectRevert(LiensightToken.NotReceiver.selector);
        token.onReport("", abi.encode(KEY, keccak256("set1"), _one(keccak256("d")), _none()));
    }

    function test_onlyIssuerCanClear() public {
        _restrict();
        vm.prank(alice);
        vm.expectRevert(LiensightToken.NotIssuer.selector);
        token.clearRestriction("nope");
    }

    function test_clearReenablesTransfers() public {
        _restrict();
        vm.prank(issuer);
        token.clearRestriction("lien discharged, counsel confirmed");
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
        vm.prank(issuer);
        token.clearRestriction("ok");
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
        vm.prank(issuer);
        token.clearRestriction("known lien, accepted");
        // a new, unrelated filing changes the set; the same old lien is still listed as adverse
        _send(keccak256("set2"), _one(keccak256("doc-LOCC-1")), _none());
        assertFalse(token.restricted());
    }

    function test_newLienAfterClearRestrictsAgain() public {
        _restrict();
        vm.prank(issuer);
        token.clearRestriction("ok");
        bytes32[] memory both = new bytes32[](2);
        both[0] = keccak256("doc-LOCC-1");
        both[1] = keccak256("doc-FL-2");
        _send(keccak256("set3"), both, _none());
        assertTrue(token.restricted());
        assertEq(token.citedDocIds(0), keccak256("doc-FL-2"));
    }

    function test_supportsReceiverInterface() public {
        assertTrue(token.supportsInterface(0x805f2132)); // IReceiver.onReport(bytes,bytes)
        assertTrue(token.supportsInterface(0x01ffc9a7)); // ERC165
    }
}
