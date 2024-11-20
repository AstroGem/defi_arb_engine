// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@aave/v3-core/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";

contract FlashArb is FlashLoanSimpleReceiverBase {
    address public owner;
    address public executor;

    IUniswapV2Router02 public immutable uniRouter;
    IUniswapV2Router02 public immutable sushiRouter;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyExecutor() {
        require(msg.sender == executor || msg.sender == owner, "Not authorized");
        _;
    }

    constructor(
        address _poolProvider,
        address _uniRouter,
        address _sushiRouter
    ) FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_poolProvider)) {
        owner = msg.sender;
        executor = msg.sender;
        uniRouter = IUniswapV2Router02(_uniRouter);
        sushiRouter = IUniswapV2Router02(_sushiRouter);
    }

    function executeArbitrage(
        address token,
        uint256 amount,
        address[] calldata buyPath,
        address[] calldata sellPath,
        bool buyOnUni
    ) external onlyExecutor {
        // Request flash loan from Aave
        POOL.flashLoanSimple(address(this), token, amount, abi.encode(buyPath, sellPath, buyOnUni), 0);
    }

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(POOL), "Caller must be pool");
        require(initiator == address(this), "Initiator must be this contract");

        (address[] memory buyPath, address[] memory sellPath, bool buyOnUni) =
            abi.decode(params, (address[], address[], bool));

        IUniswapV2Router02 buyRouter = buyOnUni ? uniRouter : sushiRouter;
        IUniswapV2Router02 sellRouter = buyOnUni ? sushiRouter : uniRouter;

        // Approve and buy
        IERC20(asset).approve(address(buyRouter), amount);
        uint256[] memory buyAmounts = buyRouter.swapExactTokensForTokens(
            amount, 0, buyPath, address(this), block.timestamp + 300
        );

        // Approve and sell
        uint256 received = buyAmounts[buyAmounts.length - 1];
        address boughtToken = buyPath[buyPath.length - 1];
        IERC20(boughtToken).approve(address(sellRouter), received);
        sellRouter.swapExactTokensForTokens(
            received, 0, sellPath, address(this), block.timestamp + 300
        );

        // Repay flash loan + premium
        uint256 amountOwed = amount + premium;
        IERC20(asset).approve(address(POOL), amountOwed);

        return true;
    }

    function setExecutor(address _executor) external onlyOwner {
        executor = _executor;
    }

    function withdrawETH() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    function withdrawToken(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner, balance);
    }

    receive() external payable {}
}
