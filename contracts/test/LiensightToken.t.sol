// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {LiensightToken} from "../src/LiensightToken.sol";

contract LiensightTokenTest is Test {
    LiensightToken token;
    address issuer = address(0x15);
    address receiver = address(0xCE);
    address alice = address(0xA11CE);
    bytes32 constant KEY = keccak256("BBL:1-00001-0001");
    bytes32 constant CODEMAP = keccak256("codemap-v1");

    function setUp() public {
        token = new LiensightToken("Liensight SPV", "LSPV", issuer, receiver, CODEMAP);
    }

    function _one(bytes32 a) internal pure returns (bytes32[] memory arr) {
        arr = new bytes32[](1);
        arr[0] = a;
    }

    function _restrict() internal {
        vm.prank(receiver);
        token.onReport(KEY, keccak256("set1"), _one(keccak256("doc-LP-1")), new bytes32[](0));
    }

    function test_transferWorksWhenUnrestricted() public {
        vm.prank(issuer);
        token.transfer(alice, 10);
        assertEq(token.balanceOf(alice), 10);
    }

    function test_onReportWithAdverseDocRestrictsTransfers() public {
        _restrict();
        assertTrue(token.restricted());
        assertEq(token.citedDocIds(0), keccak256("doc-LP-1"));
        vm.prank(issuer);
        vm.expectRevert(LiensightToken.TransferRestricted.selector);
        token.transfer(alice, 10);
    }

    function test_onReportFromNonReceiverReverts() public {
        vm.prank(alice);
        vm.expectRevert(LiensightToken.NotReceiver.selector);
        token.onReport(KEY, keccak256("set1"), _one(keccak256("d")), new bytes32[](0));
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
        emit LiensightToken.ClearSuggested(_one(keccak256("doc-SAT-1")));
        vm.prank(receiver);
        token.onReport(KEY, keccak256("set2"), new bytes32[](0), _one(keccak256("doc-SAT-1")));
        assertTrue(token.restricted());
    }

    function test_unchangedDocSetHashIsNoOp() public {
        _restrict();
        vm.prank(issuer);
        token.clearRestriction("ok");
        // same hash replayed must not re-restrict
        vm.prank(receiver);
        token.onReport(KEY, keccak256("set1"), _one(keccak256("doc-LP-1")), new bytes32[](0));
        assertFalse(token.restricted());
    }

    function test_emptyAdverseListNeverRestricts() public {
        vm.prank(receiver);
        token.onReport(KEY, keccak256("set0"), new bytes32[](0), new bytes32[](0));
        assertFalse(token.restricted());
        assertEq(token.lastDocSetHash(), keccak256("set0"));
    }
}
