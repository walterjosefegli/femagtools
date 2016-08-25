#!/usr/bin/env python
#
import unittest
import os
import femagtools
import copy

modelpars = dict(
    name="PM 130 L4",
    outer_diam=0.13,
    bore_diam=0.07,
    lfe=0.1,
    poles=4,
    stator=dict(
        num_slots=12,
        mcvkey_yoke="3",
        num_slots_gen=3,
        nodedist=1.5,
        rlength=1.0),
    windings=dict(
        num_phases=3,
        num_layers=1,
        num_wires=4,
        coil_span=3))

feapars = dict(
    lfe=0.1,
    speed=50.0,
    current=10.0,
    nu_move_steps=49,
    num_cur_steps=5,
    angl_i_up=0,
    optim_i_up=0,
    wind_temp=60.0,
    magn_temp=60.0,
    eval_force=0,
    calc_fe_loss=1,
    cog_move_steps=90,
     
    windings=dict(
        num_layers=1,
        slot_indul=0,
        skew_angle=0.0,
        culength=1.4,
        num_par_wdgs=1,
        cufilfact=0.45,
        num_skew_steps=0))


class FslBuilderTest(unittest.TestCase):
    
    def setUp(self):
        self.m = copy.deepcopy(modelpars)
        self.builder = femagtools.FslBuilder()
        
    def tearDown(self):
        self.m = None
        self.builder = None
        
    def test_stator1(self):
        self.m['stator']['stator1'] = dict(
             tooth_width=0.009,
             slot_rf1=0.002,
             tip_rh1=0.002,
             tip_rh2=0.002,
             slot_width=0.003)
        model = femagtools.Model(self.m)
        fsl = self.builder.create_stator_model(model)
        self.assertEqual(len(fsl), 17)
        
    def test_stator2(self):
        self.m['stator']['stator2'] = dict(
             slot_width=0.009,
             slot_t1=0.002,
             slot_t2=0.002,
             slot_t3=0.002,
             corner_width=0.002,
             slot_depth=0.003)
        model = femagtools.Model(self.m)
        fsl = self.builder.create_stator_model(model)
        self.assertEqual(len(fsl), 17)
        
    def test_stator3(self):
        self.m['stator']['statorRotor3'] = dict(
            slot_h1=0.002,
             slot_h2=0.004,
             middle_line=0,
             tooth_width=0.009,
             wedge_width2=0.0,
             wedge_width1=0.0,
             slot_top_sh=0,
             slot_r2=0.002,
             slot_height=0.02,
             slot_r1=0.003,
             slot_width=0.003)
        model = femagtools.Model(self.m)
        fsl = self.builder.create_stator_model(model)
        self.assertEqual(len(fsl), 23)

    def test_stator4(self):
        self.m['stator']['stator4'] = dict(
            slot_height=0.1,
            slot_h1=1e-3,
            slot_h2=0,
            slot_h3=2e-3,
            slot_h4=3e-4,
            slot_r1=11e-3,
            slot_width=22e-3,
            wedge_width1=111e-5,
            wedge_width2=222e-5,
            wedge_width3=333e-5 )
        model = femagtools.Model(self.m)
        fsl = self.builder.create_stator_model(model)
        self.assertEqual( len( fsl ), 22 )

    def test_magnetSector(self):
        self.m['magnet']=dict(
            magnetSector=dict(
                magn_height=0.005
                ,magn_width_pct=0.8
                ,condshaft_r=0.0591
                ,magn_rfe=0.0
                ,magn_len=1.0
                ,magn_shape=0.0
                ,bridge_height=0.0
                ,bridge_width=0.0
                ,magn_ori=2
                ,magn_type=1
                ,magn_num=1 ) )
        model = femagtools.Model(self.m)
        fsl = self.builder.create_magnet_model(model)
        self.assertEqual( len( fsl ), 27 )
        
    def test_run_models(self):
        feapars['calculationMode'] = "cogg_calc"
        fsl = self.builder.create_analysis(feapars)
        self.assertEqual( len( fsl ), 26 )
        
        feapars['calculationMode'] = "pm_sym_fast"
        fsl = self.builder.create_analysis(feapars)
        self.assertEqual( len( fsl ), 48 )
        
        feapars['calculationMode'] = "mult_cal_fast"
        fsl = self.builder.create_analysis(feapars)
        self.assertEqual(len(fsl), 49)

    def test_readfsl(self):
        content = [
            'dshaft = 360 --shaft diameter',
            'hm  = 38 -- magnet height',
            'bm = 122 -- magnet width',
            'ws = 10  -- slot width',
            'lfe = 224',
            '-- calculate slot height, angle and pole pairs',
            'hs = (da2-dy2)/2 - bm   ',
            'alpha = math.pi/p/2     -- slot angle',
            'p   = m.num_poles/2',
            'x = {}',
            'y = {}',
            '-- Berechnung der Koordinaten',
            'x[1],y[1] = pr2c(dy2/2, 0)',
            'x[2],y[2] = pr2c(da2/2, 0)',
            'x[3],y[3] = pr2c(da2/2, alpha - math.atan2(ws,(da2/2)))',
            'x[4],y[4] = pr2c(da2/2-hs, alpha - math.atan2(ws,(da2/2 - hs)))',
            'nc_line(x[1], y[1], x[2], y[2], 0)']
        result = self.builder.read(content)
        self.assertEqual(len(result['parameter']), 4)
        for p in result['parameter']:
            self.assertTrue(p['key'] in ['dshaft', 'hm', 'bm', 'ws'])

        
if __name__ == '__main__':
    unittest.main()

