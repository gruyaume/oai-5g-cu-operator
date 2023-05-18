#!/usr/bin/env python3
# Copyright 2023 Guillaume Belanger
# See LICENSE file for licensing details.


import pytest


@pytest.mark.abort_on_fail
async def test_build_charm(ops_test):
    await ops_test.build_charm(".")
