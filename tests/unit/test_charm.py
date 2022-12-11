# Copyright 2022 Guillaume Belanger
# See LICENSE file for licensing details.

import unittest
from unittest.mock import patch

import ops.testing
from lightkube.models.core_v1 import (
    LoadBalancerIngress,
    LoadBalancerStatus,
    Service,
    ServiceSpec,
)
from lightkube.models.core_v1 import ServiceStatus as K8sServiceStatus
from ops.model import ActiveStatus
from ops.pebble import ServiceInfo, ServiceStartup, ServiceStatus
from ops.testing import Harness

from charm import Oai5GCUOperatorCharm


class TestCharm(unittest.TestCase):
    @patch("lightkube.core.client.GenericSyncClient")
    @patch(
        "charm.KubernetesServicePatch",
        lambda charm, ports, service_type: None,
    )
    def setUp(self, patch_lightkube_client):
        ops.testing.SIMULATE_CAN_CONNECT = True
        self.model_name = "whatever"
        self.addCleanup(setattr, ops.testing, "SIMULATE_CAN_CONNECT", False)
        self.harness = Harness(Oai5GCUOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.set_model_name(name=self.model_name)
        self.harness.begin()

    def _create_amf_relation_with_valid_data(self):
        relation_id = self.harness.add_relation("fiveg-n2", "amf")
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name="amf/0")

        amf_address = "5.6.7.8"
        key_values = {
            "amf_address": amf_address,
        }
        self.harness.update_relation_data(
            relation_id=relation_id, app_or_unit="amf", key_values=key_values
        )
        return amf_address

    @patch("lightkube.Client.get")
    @patch("ops.model.Container.push")
    def test_given_amf_relation_contains_amf_info_when_amf_relation_joined_then_config_file_is_pushed(  # noqa: E501
        self, mock_push, patch_lightkube_client_get
    ):
        load_balancer_ip = "1.2.3.4"
        patch_lightkube_client_get.return_value = Service(
            spec=ServiceSpec(type="LoadBalancer"),
            status=K8sServiceStatus(
                loadBalancer=LoadBalancerStatus(ingress=[LoadBalancerIngress(ip=load_balancer_ip)])
            ),
        )
        self.harness.set_can_connect(container="cu", val=True)
        amf_address = self._create_amf_relation_with_valid_data()

        mock_push.assert_called_with(
            path="/opt/oai-gnb/etc/gnb.conf",
            source='Active_gNBs = ( "oai-cu-rfsim");\n'
            "# Asn1_verbosity, choice in: none, info, annoying\n"
            'Asn1_verbosity = "none";\n'
            "Num_Threads_PUSCH = 8;\n\n"
            "gNBs =\n"
            "(\n"
            " {\n"
            "    ////////// Identification parameters:\n"
            "    gNB_ID = 0xe00;\n\n"
            '#     cell_type =  "CELL_MACRO_GNB";\n\n'
            '    gNB_name  =  "oai-cu-rfsim";\n\n'
            "    // Tracking area code, 0x0000 and 0xfffe are reserved values\n"
            "    tracking_area_code  =  1;\n"
            "    plmn_list = ({ mcc = 208; mnc = 99; mnc_length = 2; snssaiList = ({ sst = 1, sd = 0x0027db }) });\n\n\n"  # noqa: E501, W505
            "    nr_cellid = 12345678L;\n"
            "    force_256qam_off = 1;\n\n"
            '    tr_s_preference = "f1";\n\n'
            '    local_s_if_name = "eth0";\n'
            '    local_s_address = "1.2.3.4";\n'
            '    remote_s_address = "127.0.0.1";\n'
            "    local_s_portc   = 501;\n"
            "    local_s_portd   = 2153;\n"
            "    remote_s_portc  = 500;\n"
            "    remote_s_portd  = 2153;\n"
            "    min_rxtxtime                                              = 6;\n\n"
            "     pdcch_ConfigSIB1 = (\n"
            "      {\n"
            "        controlResourceSetZero = 12;\n"
            "        searchSpaceZero = 0;\n"
            "      }\n"
            "      );\n\n"
            "    servingCellConfigCommon = (\n"
            "    {\n"
            " #spCellConfigCommon\n\n"
            "      physCellId                                                    = 0;\n\n"
            "#  downlinkConfigCommon\n"
            "    #frequencyInfoDL\n"
            "      # this is 3600 MHz + 43 PRBs@30kHz SCS (same as initial BWP)\n"
            "      absoluteFrequencySSB                                             = 641280;\n"  # noqa: E501, W505
            "      dl_frequencyBand                                                 = 78;\n"
            "      # this is 3600 MHz\n"
            "      dl_absoluteFrequencyPointA                                       = 640008;\n"  # noqa: E501, W505
            "      #scs-SpecificCarrierList\n"
            "        dl_offstToCarrier                                              = 0;\n"
            "# subcarrierSpacing\n"
            "# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120\n"
            "        dl_subcarrierSpacing                                           = 1;\n"
            "        dl_carrierBandwidth                                            = 106;\n"  # noqa: E501, W505
            "     #initialDownlinkBWP\n"
            "      #genericParameters\n"
            "        # this is RBstart=27,L=48 (275*(L-1))+RBstart\n"
            "        initialDLBWPlocationAndBandwidth                               = 28875; # 6366 12925 12956 28875 12952\n"  # noqa: E501, W505
            "# subcarrierSpacing\n# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120\n"
            "        initialDLBWPsubcarrierSpacing                                   = 1;\n"
            "      #pdcch-ConfigCommon\n"
            "        initialDLBWPcontrolResourceSetZero                              = 11;\n"  # noqa: E501, W505
            "        initialDLBWPsearchSpaceZero                                     = 0;\n\n"  # noqa: E501, W505
            "  #uplinkConfigCommon\n"
            "     #frequencyInfoUL\n"
            "      ul_frequencyBand                                              = 78;\n"
            "      #scs-SpecificCarrierList\n"
            "      ul_offstToCarrier                                             = 0;\n"
            "# subcarrierSpacing\n"
            "# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120\n"
            "      ul_subcarrierSpacing                                          = 1;\n"
            "      ul_carrierBandwidth                                           = 106;\n"
            "      pMax                                                          = 20;\n"
            "     #initialUplinkBWP\n"
            "      #genericParameters\n"
            "        initialULBWPlocationAndBandwidth                            = 28875;\n"
            "# subcarrierSpacing\n"
            "# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120\n"
            "        initialULBWPsubcarrierSpacing                               = 1;\n"
            "      #rach-ConfigCommon\n"
            "        #rach-ConfigGeneric\n"
            "          prach_ConfigurationIndex                                  = 98;\n"
            "#prach_msg1_FDM\n"
            "#0 = one, 1=two, 2=four, 3=eight\n"
            "          prach_msg1_FDM                                            = 0;\n"
            "          prach_msg1_FrequencyStart                                 = 0;\n"
            "          zeroCorrelationZoneConfig                                 = 13;\n"
            "          preambleReceivedTargetPower                               = -96;\n"
            "#preamblTransMax (0...10) = (3,4,5,6,7,8,10,20,50,100,200)\n"
            "          preambleTransMax                                          = 6;\n"
            "#powerRampingStep\n"
            "# 0=dB0,1=dB2,2=dB4,3=dB6\n"
            "        powerRampingStep                                            = 1;\n"
            "#ra_ReponseWindow\n"
            "#1,2,4,8,10,20,40,80\n"
            "        ra_ResponseWindow                                           = 4;\n"
            "#ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR\n"
            "#1=oneeighth,2=onefourth,3=half,4=one,5=two,6=four,7=eight,8=sixteen\n"
            "        ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR                = 4;\n"
            "#oneHalf (0..15) 4,8,12,16,...60,64\n"
            "        ssb_perRACH_OccasionAndCB_PreamblesPerSSB                   = 14;\n"
            "#ra_ContentionResolutionTimer\n"
            "#(0..7) 8,16,24,32,40,48,56,64\n"
            "        ra_ContentionResolutionTimer                                = 7;\n"
            "        rsrp_ThresholdSSB                                           = 19;\n"
            "#prach-RootSequenceIndex_PR\n"
            "#1 = 839, 2 = 139\n"
            "        prach_RootSequenceIndex_PR                                  = 2;\n"
            "        prach_RootSequenceIndex                                     = 1;\n"
            "        # SCS for msg1, can only be 15 for 30 kHz < 6 GHz, takes precendence over the one derived from prach-ConfigIndex\n"  # noqa: E501, W505
            "        #\n"
            "        msg1_SubcarrierSpacing                                      = 1,\n"
            "# restrictedSetConfig\n"
            "# 0=unrestricted, 1=restricted type A, 2=restricted type B\n"
            "        restrictedSetConfig                                         = 0,\n\n"
            "        msg3_DeltaPreamble                                          = 1;\n"
            "        p0_NominalWithGrant                                         =-90;\n\n"
            "# pucch-ConfigCommon setup :\n"
            "# pucchGroupHopping\n"
            "# 0 = neither, 1= group hopping, 2=sequence hopping\n"
            "        pucchGroupHopping                                           = 0;\n"
            "        hoppingId                                                   = 40;\n"
            "        p0_nominal                                                  = -90;\n"
            "# ssb_PositionsInBurs_BitmapPR\n"
            "# 1=short, 2=medium, 3=long\n"
            "      ssb_PositionsInBurst_PR                                       = 2;\n"
            "      ssb_PositionsInBurst_Bitmap                                   = 1;\n\n"
            "# ssb_periodicityServingCell\n"
            "# 0 = ms5, 1=ms10, 2=ms20, 3=ms40, 4=ms80, 5=ms160, 6=spare2, 7=spare1\n"
            "      ssb_periodicityServingCell                                    = 2;\n\n"
            "# dmrs_TypeA_position\n"
            "# 0 = pos2, 1 = pos3\n"
            "      dmrs_TypeA_Position                                           = 0;\n\n"
            "# subcarrierSpacing\n"
            "# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120\n"
            "      subcarrierSpacing                                             = 1;\n\n\n"
            "  #tdd-UL-DL-ConfigurationCommon\n"
            "# subcarrierSpacing\n"
            "# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120\n"
            "      referenceSubcarrierSpacing                                    = 1;\n"
            "      # pattern1\n"
            "      # dl_UL_TransmissionPeriodicity\n"
            "      # 0=ms0p5, 1=ms0p625, 2=ms1, 3=ms1p25, 4=ms2, 5=ms2p5, 6=ms5, 7=ms10\n"
            "      dl_UL_TransmissionPeriodicity                                 = 6;\n"
            "      nrofDownlinkSlots                                             = 7;\n"
            "      nrofDownlinkSymbols                                           = 6;\n"
            "      nrofUplinkSlots                                               = 2;\n"
            "      nrofUplinkSymbols                                             = 4;\n\n"
            "      ssPBCH_BlockPower                                             = -25;\n"
            "  }\n\n"
            "  );\n"
            "    # ------- SCTP definitions\n"
            "    SCTP :\n"
            "    {\n"
            "        # Number of streams to use in input/output\n"
            "        SCTP_INSTREAMS  = 2;\n"
            "        SCTP_OUTSTREAMS = 2;\n"
            "    };\n\n\n"
            "    ////////// AMF parameters:\n"
            f'        amf_ip_address      = ( {{ ipv4       = "{amf_address}";\n'
            '                              ipv6       = "192:168:30::17";\n'
            '                              active     = "yes";\n'
            '                              preference = "ipv4";\n'
            "                            }\n"
            "                          );\n\n"
            "    NETWORK_INTERFACES :\n"
            "    {\n\n"
            '        GNB_INTERFACE_NAME_FOR_NG_AMF            = "eth0";\n'
            '        GNB_IPV4_ADDRESS_FOR_NG_AMF              = "1.2.3.4";\n'
            '        GNB_INTERFACE_NAME_FOR_NGU               = "eth0";\n'
            '        GNB_IPV4_ADDRESS_FOR_NGU                 = "1.2.3.4";\n'
            "        GNB_PORT_FOR_S1U                         = 2152; # Spec 2152\n"
            "    };\n"
            "  }\n"
            ");\n\n"
            "security = {\n"
            "  # preferred ciphering algorithms\n"
            "  # the first one of the list that an UE supports in chosen\n"
            "  # valid values: nea0, nea1, nea2, nea3\n"
            '  ciphering_algorithms = ( "nea0" );\n\n'
            "  # preferred integrity algorithms\n"
            "  # the first one of the list that an UE supports in chosen\n"
            "  # valid values: nia0, nia1, nia2, nia3\n"
            '  integrity_algorithms = ( "nia2", "nia0" );\n\n'
            "  # setting 'drb_ciphering' to \"no\" disables ciphering for DRBs, no matter\n"
            "  # what 'ciphering_algorithms' configures; same thing for 'drb_integrity'\n"  # noqa: E501, W505
            '  drb_ciphering = "yes";\n'
            '  drb_integrity = "no";\n'
            "};\n"
            "     log_config :\n"
            "     {\n"
            '       global_log_level                      ="info";\n'
            '       hw_log_level                          ="info";\n'
            '       phy_log_level                         ="info";\n'
            '       mac_log_level                         ="info";\n'
            '       rlc_log_level                         ="debug";\n'
            '       pdcp_log_level                        ="info";\n'
            '       rrc_log_level                         ="info";\n'
            '       f1ap_log_level                         ="debug";\n'
            '       ngap_log_level                         ="debug";\n'
            "    };",
        )

    @patch("lightkube.Client.get")
    @patch("ops.model.Container.push")
    def test_given_amf_and_db_relation_are_set_when_config_changed_then_pebble_plan_is_created(  # noqa: E501
        self, _, patch_lightkube_client_get
    ):
        load_balancer_ip = "1.2.3.4"
        patch_lightkube_client_get.return_value = Service(
            spec=ServiceSpec(type="LoadBalancer"),
            status=K8sServiceStatus(
                loadBalancer=LoadBalancerStatus(ingress=[LoadBalancerIngress(ip=load_balancer_ip)])
            ),
        )
        self.harness.set_can_connect(container="cu", val=True)
        self._create_amf_relation_with_valid_data()

        expected_plan = {
            "services": {
                "cu": {
                    "override": "replace",
                    "summary": "cu",
                    "command": "/opt/oai-gnb/bin/nr-softmodem -O /opt/oai-gnb/etc/gnb.conf --sa -E --rfsim --log_config.global_log_options level nocolor time",  # noqa: E501
                    "startup": "enabled",
                }
            },
        }
        self.harness.container_pebble_ready("cu")
        updated_plan = self.harness.get_container_pebble_plan("cu").to_dict()
        self.assertEqual(expected_plan, updated_plan)
        service = self.harness.model.unit.get_container("cu").get_service("cu")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    @patch("lightkube.Client.get")
    @patch("ops.model.Container.get_service")
    def test_given_unit_is_leader_when_f1_relation_joined_then_cu_relation_data_is_set(
        self, patch_get_service, patch_k8s_get
    ):
        load_balancer_ip = "5.6.7.8"
        patch_k8s_get.return_value = Service(
            spec=ServiceSpec(type="LoadBalancer"),
            status=K8sServiceStatus(
                loadBalancer=LoadBalancerStatus(ingress=[LoadBalancerIngress(ip=load_balancer_ip)])
            ),
        )
        self.harness.set_leader(True)
        self.harness.set_can_connect(container="cu", val=True)
        patch_get_service.return_value = ServiceInfo(
            name="cu",
            current=ServiceStatus.ACTIVE,
            startup=ServiceStartup.ENABLED,
        )

        relation_id = self.harness.add_relation(relation_name="fiveg-f1", remote_app="cu")
        self.harness.add_relation_unit(relation_id=relation_id, remote_unit_name="cu/0")

        relation_data = self.harness.get_relation_data(
            relation_id=relation_id, app_or_unit=self.harness.model.app.name
        )

        assert relation_data["cu_address"] == load_balancer_ip
