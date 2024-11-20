// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Multicall helper for batching read calls
 * @notice Used by the bot to fetch reserves from multiple pairs in one RPC call
 */
contract MultiPairQuery {
    struct PairReserves {
        address pair;
        uint112 reserve0;
        uint112 reserve1;
        address token0;
    }

    function getReserves(address[] calldata pairs)
        external
        view
        returns (PairReserves[] memory results)
    {
        results = new PairReserves[](pairs.length);

        for (uint256 i = 0; i < pairs.length; i++) {
            address pair = pairs[i];

            (bool success, bytes memory data) = pair.staticcall(
                abi.encodeWithSignature("getReserves()")
            );

            if (success && data.length >= 64) {
                (uint112 r0, uint112 r1, ) = abi.decode(data, (uint112, uint112, uint32));

                (, bytes memory t0Data) = pair.staticcall(
                    abi.encodeWithSignature("token0()")
                );
                address token0 = abi.decode(t0Data, (address));

                results[i] = PairReserves(pair, r0, r1, token0);
            }
        }
    }
}
