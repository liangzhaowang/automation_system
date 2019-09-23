#!/usr/bin/env python


class Config(dict):
    def __getattr__(self, name):
        return self[name]


host = Config({
    'PASSWD': '123456',
    'COMPORT_IOCARD': '/dev/ttyUSB4',
    'COMPORT_DCARD_0': '/dev/ttyUSB0',
    'COMPORT_DCARD_1': '/dev/ttyUSB1',
    'COMPORT_DCARD_2': '/dev/ttyUSB2',
    'COMPORT_DCARD_3': '/dev/ttyUSB3',
    'IOCARD_POWERKEY': 1,
    'IOCARD_POWER': 3,
    'IOCARD_USB': 2,
})

flash = Config({
    'bxtp_ivi_o': {
        'build_info': 'gordon_peak',
        'configurations': 'blank_gr_mrb_b1',
        'ioc_port': '/dev/ttyUSB2',
        'ioc': 'ioc_firmware_gp_mrb_fab_d_slcan.ias_ioc',
    },
    'bxtp_ivi_p': {
        'build_info': 'gordon_peak',
        'configurations': 'blank_gr_mrb_b1',
        'ioc_port': '/dev/ttyUSB2',
        'ioc': 'ioc_firmware_gp_mrb_fab_d.ias_ioc'
    },
    'bxtp_ivi_q': {
        'build_info': 'gordon_peak',
        'configurations': 'blank_gr_mrb_b1',
        'ioc_port': '/dev/ttyUSB2',
        'ioc': 'ioc_firmware_gp_mrb_fab_d.ias_ioc'
    },
    'bxtp_ivi_m':{
        'build_info': 'r0_bxtp_abl',
        'configurations': 'blank_gr_mrb_b1',
        'ioc_port': '/dev/ttyUSB2',
        'ioc': 'ioc_firmware_gp_mrb_fab_d.ias_ioc'
    },
    'mmr1_bxtp_ivi_maint': {
        'build_info': 'r0_bxtp_abl',
        'configurations': 'blank_gr_mrb_b1',
        'ioc_port': '/dev/ttyUSB2',
        'ioc': 'ioc_firmware_gp_mrb_fab_d_slcan.ias_ioc'
    },
    'f_p_early_external': {
        'build_info': 'gordon_peak',
        'configurations': 'blank_gr_mrb_b1',
        'ioc_port': '/dev/ttyUSB2',
        'ioc': 'ioc_firmware_gp_mrb_fab_d.ias_ioc'
    }
})

case = Config({
    'cooldown_time': 1
})

