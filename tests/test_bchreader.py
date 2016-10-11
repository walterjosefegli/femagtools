#!/usr/bin/env python
#
import unittest
import os
import femagtools
from io import open

class BchReaderTest(unittest.TestCase):

    def read_bch( self, filename ):
        testPath = os.path.join(os.path.split(__file__)[0], 'data')
        if len(testPath) == 0:
            testPath = os.path.join(os.path.abspath('.'), 'data')
        r = femagtools.BchReader()
        with open('{0}/{1}'.format(testPath, filename),encoding='latin1') as f:
            r.read( f )
        return r
        
    def test_read_cogging( self ):
        bch = self.read_bch('cogging.BATCH')
        self.assertEqual( bch.version, '7.9.147')
        self.assertEqual( bch.nodes, 2315)
        self.assertEqual( bch.elements, 3305)
        self.assertEqual( bch.quality, 100.0)

        self.assertEqual( len(bch.torque_fft), 1 ) 
        self.assertEqual( len(bch.torque_fft[0]), 5 ) 
        self.assertTrue( 'order' in bch.torque_fft[0] ) 
        self.assertTrue( 'torque' in bch.torque_fft[0] ) 
        self.assertEqual( len(bch.torque_fft[0]['torque']), 5 ) 
        self.assertEqual( bch.torque_fft[0]['order'], [4, 12, 24, 36, 48] )

        self.assertEqual( sorted(bch.flux.keys()), ['1','2','3'] )
        self.assertEqual( sorted(bch.flux['1'][0].keys()), 
                          sorted(['displ', 'voltage_four', 'current_k', 'flux_k',
                           'voltage_ir', 'displunit', 'voltage_dpsi']))
        self.assertEqual( len(bch.flux['1'][0]['flux_k']), 61 )
        self.assertEqual( bch.flux_fft['1'][0]['order'], [1,3,5,7,9,11] )

        self.assertEqual( len(bch.torque), 1 )
        self.assertEqual( sorted(bch.torque[0].keys()), 
                         sorted(['angle', 'force_y', 'force_x', 'torque',
                          'current_1', 'ripple', 't_idpsi']) )
        self.assertEqual( len(bch.torque[0]['torque']), 61 )

        self.assertAlmostEqual( bch.losses[0]['winding'], 0.0, 1 )
        self.assertAlmostEqual( bch.losses[0]['stajo'], 0.458, 2 )
        self.assertAlmostEqual( bch.losses[0]['staza'], 0.344, 3 )
        self.assertAlmostEqual( bch.losses[0]['magnetJ'], 0.006, 3 )
        #self.assertAlmostEqual( bch.losses[0]['rotfe'], 0.000, 3 )

        self.assertAlmostEqual( bch.lossPar['fo'][0], 50.0, 1 )
        self.assertAlmostEqual( bch.lossPar['fo'][1], 50.0, 1 )
        self.assertEqual( bch.get( ('machine', 'p') ), 2 )
                                
    def test_read_sctest( self ):
        bch = self.read_bch( 'sctest.BATCH' ) 

        self.assertEqual( len(bch.torque_fft), 1 )
        self.assertEqual( len(bch.scData['ia']), 134 )
        self.assertAlmostEqual( bch.scData['ikd'], 0.0, 1 )
        self.assertAlmostEqual( bch.scData['iks'], 1263.581, 2)
        self.assertAlmostEqual( bch.scData['tks'], 1469.736, 2)

    def test_read_pmsim( self ):
        bch = self.read_bch( 'pmsim.BATCH' ) 

        self.assertEqual( len(bch.torque_fft), 2 ) 
        self.assertTrue( 'order' in bch.torque_fft[0] ) 
        self.assertTrue( 'torque' in bch.torque_fft[0] ) 
        self.assertEqual( len(bch.torque_fft[0]['torque']), 5 ) 
        self.assertEqual( bch.torque_fft[1]['order'], [0,12,24,36] )

        self.assertEqual( sorted(bch.flux['1'][0].keys()),
                          sorted(['displ', 'voltage_four', 'current_k', 'flux_k',
                           'voltage_ir', 'displunit', 'voltage_dpsi']))
        self.assertEqual( len(bch.flux['1'][0]['flux_k']), 61 )

        self.assertEqual( len(bch.torque), 2 )
        self.assertTrue( 'torque' in bch.torque[1] )
        self.assertEqual( len(bch.torque[1]['torque']), 61 )

        self.assertTrue( 'ld' in bch.dqPar )
        self.assertAlmostEqual( bch.dqPar['i1'][1], 14.142, 3 )
        self.assertAlmostEqual( bch.dqPar['ld'][0], 0.241e-3, 6 )
        self.assertAlmostEqual( bch.dqPar['ld'][0], 0.241e-3, 6 )
        self.assertAlmostEqual( bch.dqPar['u1'][1], 3.423, 3 )
        self.assertAlmostEqual( bch.dqPar['torque'][0], 0.36, 2 )

        self.assertAlmostEqual( bch.lossPar['fo'][0], 50.0, 1 )

    def test_read_psidq( self ):
        bch = self.read_bch('psidpsiq.BATCH')

        self.assertEqual( len(bch.torque_fft), 10 ) 
        self.assertTrue( 'order' in bch.torque_fft[0] ) 
        self.assertTrue( 'torque' in bch.torque_fft[0] ) 
        self.assertEqual( len(bch.torque_fft[0]['torque']), 5 ) 
        self.assertEqual( bch.torque_fft[0]['order'], [4, 12, 24, 36, 48] )

        self.assertEqual( sorted(bch.flux.keys()), ['1','2','3'] )
        self.assertEqual( len(bch.flux['1']), 10 )
        self.assertTrue( 'flux_k' in bch.flux['1'][0] )
        self.assertEqual( len(bch.flux['1'][0]['flux_k']), 61 )

        self.assertEqual( len(bch.torque), 10 )
        self.assertEqual( len(bch.torque[-1]['torque']), 91 )

        self.assertEqual( len(bch.psidq), 5 )
        self.assertEqual( len(bch.psidq_ldq), 6 )
        self.assertEqual( len(bch.psidq['psid']), 9 )
        self.assertEqual( len(bch.psidq_ldq['ld']), 9 )

    def test_read_ldq( self ):
        bch = self.read_bch('ldq.BATCH')
        self.assertEqual( len(bch.torque_fft), 6 ) 
        self.assertTrue( 'order' in bch.torque_fft[0] ) 
        self.assertTrue( 'torque' in bch.torque_fft[0] ) 
        self.assertEqual( len(bch.torque_fft[0]['torque']), 5 ) 
        self.assertEqual( bch.torque_fft[0]['order'], [4, 12, 24, 36, 48] )

        self.assertEqual( sorted(bch.flux.keys()), ['1','2','3'] )
        self.assertEqual( len(bch.flux['1']), 6 )
        self.assertEqual( len(bch.flux['1'][0]), 7 )
        self.assertTrue( 'flux_k' in bch.flux['1'][0] )
        self.assertEqual( len(bch.flux['1'][0]['flux_k']), 61 )

        self.assertEqual( len(bch.torque), 6 )
        self.assertEqual( len(bch.torque[-1]['torque']), 61 )

        #self.assertTrue( 'i1' in bch.airgapInduction )
        #self.assertEqual( len(bch.airgapInduction['i1']), 5 )
        #self.assertEqual( len(bch.airgapInduction['an']), 4 )
        #self.assertEqual( len(bch.airgapInduction['an'][0]), 9 )

    def test_read_pmsim2( self ):
        bch = self.read_bch('PM_270_L8_001.BATCH')
        self.assertAlmostEqual( bch.dqPar['i1'][1], 70.0, 1 )
        self.assertAlmostEqual( bch.dqPar['beta'][0], -38.0, 1 )
        

if __name__ == '__main__':
  unittest.main()