import pytest
from eth_tester.exceptions import TransactionFailed

from nucypher.blockchain.eth.agents import WorkLockAgent, ContractAgency, StakingEscrowAgent


def test_create_worklock_agent(testerchain, test_registry, agency, token_economics):
    agent = WorkLockAgent(registry=test_registry)
    assert agent.contract_address
    same_agent = ContractAgency.get_agent(WorkLockAgent, registry=test_registry)
    assert agent == same_agent


def test_bidding(testerchain, agency, token_economics, test_registry):
    big_bid = token_economics.maximum_allowed_locked // 100
    small_bid = token_economics.minimum_allowed_locked // 100

    agent = ContractAgency.get_agent(WorkLockAgent, registry=test_registry)

    # Round 1
    for multiplier, bidder in enumerate(testerchain.unassigned_accounts[:3], start=1):
        bid = big_bid * multiplier
        receipt = agent.bid(checksum_address=bidder, value=bid)
        assert receipt['status'] == 1

    # Round 2
    for multiplier, bidder in enumerate(testerchain.unassigned_accounts[:3], start=1):
        bid = (small_bid * 2) * multiplier
        receipt = agent.bid(checksum_address=bidder, value=bid)
        assert receipt['status'] == 1


def test_get_deposited_eth(testerchain, agency, token_economics, test_registry):
    big_bid = token_economics.maximum_allowed_locked // 10
    big_bidder = testerchain.unassigned_accounts[-1]
    agent = ContractAgency.get_agent(WorkLockAgent, registry=test_registry)
    receipt = agent.bid(checksum_address=big_bidder, value=big_bid)
    assert receipt['status'] == 1
    bid = agent.get_deposited_eth(big_bidder)
    assert bid == big_bid


def test_cancel_bid(testerchain, agency, token_economics, test_registry):
    bidder = testerchain.unassigned_accounts[1]
    agent = ContractAgency.get_agent(WorkLockAgent, registry=test_registry)

    assert agent.get_deposited_eth(bidder)        # Bid
    receipt = agent.cancel_bid(bidder)  # Cancel
    assert receipt['status'] == 1
    assert not agent.get_deposited_eth(bidder)    # No more bid

    # Can't cancel a bid twice in a row
    with pytest.raises((TransactionFailed, ValueError)):
        _receipt = agent.cancel_bid(bidder)


def test_get_remaining_work(testerchain, agency, token_economics, test_registry):
    agent = ContractAgency.get_agent(WorkLockAgent, registry=test_registry)
    bidder = testerchain.unassigned_accounts[0]
    remaining = agent.get_remaining_work(checksum_address=bidder)
    assert remaining == 35905203136136849607983


def test_early_claim(testerchain, agency, token_economics, test_registry):
    agent = ContractAgency.get_agent(WorkLockAgent, registry=test_registry)
    bidder = testerchain.unassigned_accounts[0]
    with pytest.raises(TransactionFailed):
        _receipt = agent.claim(checksum_address=bidder)


def test_successful_claim(testerchain, agency, token_economics, test_registry):

    # Wait until the bidding window closes...
    testerchain.time_travel(seconds=token_economics.bidding_duration+1)

    agent = ContractAgency.get_agent(WorkLockAgent, registry=test_registry)
    staking_agent = ContractAgency.get_agent(StakingEscrowAgent, registry=test_registry)

    bidder = testerchain.unassigned_accounts[0]

    # Ensure that the bidder is not staking.
    locked_tokens = staking_agent.get_locked_tokens(staker_address=bidder, periods=10)
    assert locked_tokens == 0

    receipt = agent.claim(checksum_address=bidder)
    assert receipt['status'] == 1

    # Cant claim more than once
    with pytest.raises(TransactionFailed):
        _receipt = agent.claim(checksum_address=bidder)

    # Ensure that the claimant is now the holder of a stake.
    locked_tokens = staking_agent.get_locked_tokens(staker_address=bidder, periods=10)
    assert locked_tokens == 71810406272273699215965
